"""Bounded filesystem access and deterministic CSV operations.

The workspace must be owned by the operator; untrusted local users must not be
able to replace directories while the server runs. All server writes are locked.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import stat
import threading
import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MAX_BYTES = 5 * 1024 * 1024
MAX_ROWS = 10_000
MAX_COLUMNS = 100
MAX_TEXT = 32_000


class GuardError(ValueError):
    pass


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Rules(StrictModel):
    required_columns: list[str] = Field(default_factory=list, max_length=100)
    required_values: list[str] = Field(default_factory=list, max_length=100)
    types: dict[str, Literal["integer", "decimal", "string"]] = Field(default_factory=dict)
    allowed_labels: dict[str, list[str]] = Field(default_factory=dict)
    duplicate_keys: list[str] = Field(default_factory=list, max_length=100)


class Cleaning(StrictModel):
    trim_columns: list[str] = Field(default_factory=list, max_length=100)
    label_mappings: dict[str, dict[str, str]] = Field(default_factory=dict)
    deduplicate: bool = True
    exclude_invalid: bool = True


class CleanRequest(StrictModel):
    dataset: str = Field(min_length=1, max_length=500)
    rules_path: str = Field(min_length=1, max_length=500)
    policy_path: str = Field(min_length=1, max_length=500)
    expected_dataset_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_rules_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_policy_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    output_name: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,60}$")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Workspace:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

    def path(self, value: str, *, directory: bool = False) -> Path:
        if not isinstance(value, str) or not value or len(value) > 500:
            raise GuardError("Use a nonempty relative workspace path (max 500 characters).")
        normal = value.replace("\\", "/")
        if PureWindowsPath(value).drive or normal.startswith("/") or ":" in normal or "\x00" in normal:
            raise GuardError("Absolute paths, drive paths, streams, and null bytes are forbidden.")
        parts = normal.split("/")
        if ".." in parts:
            raise GuardError("Parent traversal is forbidden.")
        for part in parts:
            if part in ("", "."):
                continue
            if part.startswith(".") or part.endswith((" ", ".")):
                raise GuardError("Hidden and ambiguous path components are forbidden.")
            if part.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL", *[f"COM{i}" for i in range(1,10)], *[f"LPT{i}" for i in range(1,10)]}:
                raise GuardError("Reserved device names are forbidden.")
        candidate = self.root.joinpath(normal)
        current = self.root
        for part in Path(normal).parts:
            current = current / part
            if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
                raise GuardError("Symbolic links and junctions are forbidden.")
            if current.exists() and getattr(current.lstat(), "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0):
                raise GuardError("Reparse points are forbidden.")
        resolved = candidate.resolve()
        if not resolved.is_relative_to(self.root):
            raise GuardError("Path leaves the permitted workspace.")
        if resolved == self.root and not directory:
            raise GuardError("A file path is required.")
        return resolved

    def relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def writable(self, value: str, role: str, *, delete: bool = False) -> Path:
        p = self.path(value)
        rel = p.relative_to(self.root)
        folders = {"reports", "handoff"} if role == "inspector" else {"reports", "handoff", "notes"}
        if rel.parts[0] not in folders or p.suffix.lower() not in {".md", ".txt", ".json"}:
            raise GuardError("Generic writes are limited to reports/, handoff/, and notes/ text files; originals, rules, and cleaned datasets are protected.")
        if delete and (role != "admin" or rel.parts[0] not in {"reports", "notes"}):
            raise GuardError("Only admin may delete generated reports or notes; handoff files are protected.")
        return p

    def read_bytes(self, value: str) -> bytes:
        p = self.path(value)
        if not p.is_file():
            raise GuardError("File does not exist.")
        if p.stat().st_size > MAX_BYTES:
            raise GuardError("File exceeds the 5 MiB limit.")
        with p.open("rb") as f:
            data = f.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise GuardError("File exceeds the 5 MiB limit.")
        return data

    def text(self, value: str) -> str:
        try:
            return self.read_bytes(value).decode("utf-8-sig")
        except UnicodeDecodeError:
            raise GuardError("Only UTF-8 text is supported.") from None

    def atomic_write(self, p: Path, data: bytes) -> None:
        p.parent.mkdir(parents=True, exist_ok=True)
        temp = p.with_name(f".{p.name}.{uuid.uuid4().hex}.tmp")
        try:
            with temp.open("xb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp, p)
        finally:
            temp.unlink(missing_ok=True)

    def write(self, value: str, content: str, role: str, expected_sha256: str | None = None) -> dict:
        data = content.encode("utf-8")
        if len(data) > MAX_BYTES:
            raise GuardError("Content exceeds the 5 MiB limit.")
        with self.lock:
            p = self.writable(value, role)
            if p.exists():
                if expected_sha256 != digest(self.read_bytes(value)):
                    raise GuardError("Version conflict. Read the current file and supply its SHA-256 to overwrite.")
            elif expected_sha256 is not None:
                raise GuardError("File does not exist; omit expected_sha256 to create it.")
            self.atomic_write(p, data)
        return {"path": value, "sha256": digest(data), "bytes": len(data)}

    def replace(self, value: str, old: str, new: str, expected: str, role: str) -> dict:
        with self.lock:
            self.writable(value, role)
            text = self.text(value)
            if not old or text.count(old) != 1:
                raise GuardError("old_str must be nonempty and match exactly once. Include surrounding text.")
            return self.write(value, text.replace(old, new, 1), role, expected)

    def delete(self, value: str, expected: str, confirm: bool, role: str) -> dict:
        if not confirm:
            raise GuardError("Deletion requires confirm=true.")
        with self.lock:
            p = self.writable(value, role, delete=True)
            if digest(self.read_bytes(value)) != expected:
                raise GuardError("Version conflict. Read the file before deletion.")
            p.unlink()
        return {"deleted": value}

    def list_files(self, value: str = ".", offset: int = 0, limit: int = 50) -> dict:
        if not 0 <= offset <= 100_000 or not 1 <= limit <= 100:
            raise GuardError("Use offset 0..100000 and limit 1..100.")
        p = self.path(value, directory=True)
        if not p.is_dir():
            raise GuardError("Directory does not exist.")
        entries = []
        for entry in sorted(p.iterdir(), key=lambda f: f.name.lower()):
            if entry.name.startswith("."):
                continue
            try:
                safe = self.path(self.relative(entry), directory=True)
                entries.append({"path": self.relative(safe), "kind": "directory" if safe.is_dir() else "file"})
            except GuardError:
                continue
        return {"entries": entries[offset:offset+limit], "total": len(entries), "next_offset": offset+limit if offset+limit < len(entries) else None}

    def read(self, value: str, offset: int = 0, limit: int = 8000) -> dict:
        if offset < 0 or not 1 <= limit <= MAX_TEXT:
            raise GuardError("offset must be nonnegative; limit must be 1..32000 characters.")
        data = self.read_bytes(value)
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise GuardError("Only UTF-8 text is supported.") from None
        return {"path": value, "sha256": digest(data), "content": text[offset:offset+limit], "characters": len(text), "next_offset": offset+limit if offset+limit < len(text) else None}

    def search(self, query: str, value: str = ".", limit: int = 30) -> dict:
        if not query or len(query) > 200 or not 1 <= limit <= 100:
            raise GuardError("Use a 1..200 character query and limit 1..100.")
        root = self.path(value, directory=True)
        if not root.is_dir():
            raise GuardError("Search path must be a directory.")
        matches, scanned, total_bytes = [], 0, 0
        for parent, dirs, files in os.walk(root, followlinks=False):
            safe_dirs = []
            for name in sorted(dirs):
                try:
                    self.path(self.relative(Path(parent)/name), directory=True)
                    safe_dirs.append(name)
                except GuardError:
                    pass
            dirs[:] = safe_dirs
            for name in sorted(files):
                p = Path(parent)/name
                if p.suffix.lower() not in {".csv", ".json", ".md", ".txt"}:
                    continue
                if scanned >= 100 or total_bytes >= 10*1024*1024:
                    return {"matches": matches, "scanned_files": scanned, "truncated": True}
                try:
                    text = self.text(self.relative(p))
                except (GuardError, OSError):
                    continue
                scanned += 1
                total_bytes += len(text.encode("utf-8"))
                for n, line in enumerate(text.splitlines(), 1):
                    if query.casefold() in line.casefold():
                        matches.append({"path": self.relative(p), "line": n, "excerpt": line[:240]})
                        if len(matches) >= limit:
                            return {"matches": matches, "scanned_files": scanned, "truncated": True}
        return {"matches": matches, "scanned_files": scanned, "truncated": False}

    def dataset(self, value: str) -> tuple[list[str], list[dict], str]:
        if self.path(value).suffix.lower() != ".csv":
            raise GuardError("Dataset must have a .csv extension.")
        data = self.read_bytes(value)
        try:
            reader = csv.reader(io.StringIO(data.decode("utf-8-sig"), newline=""), strict=True)
            headers = next(reader, None)
            if not headers or any(not h.strip() for h in headers) or len(set(headers)) != len(headers):
                raise GuardError("CSV requires unique, nonempty column headers.")
            if len(headers) > MAX_COLUMNS:
                raise GuardError("CSV exceeds 100 columns.")
            rows = []
            for record, row in enumerate(reader, 1):
                if len(row) != len(headers):
                    raise GuardError(f"Record {record} has {len(row)} fields; expected {len(headers)}.")
                if record > MAX_ROWS:
                    raise GuardError("CSV exceeds 10000 records.")
                rows.append(dict(zip(headers, row)))
        except (UnicodeDecodeError, csv.Error):
            raise GuardError("CSV is malformed, has an oversized field, or is not UTF-8.") from None
        return headers, rows, digest(data)

    def rules(self, path: str) -> Rules:
        self.operator_rule_file(path)
        try:
            return Rules.model_validate_json(self.text(path))
        except (ValueError, TypeError) as e:
            raise GuardError("Invalid rules JSON. Use required_columns, required_values, types, allowed_labels, and duplicate_keys only.") from None

    def operator_rule_file(self, value: str) -> Path:
        p = self.path(value)
        if p.relative_to(self.root).parts[0] != "rules" or p.suffix.lower() != ".json":
            raise GuardError("Validation rules and cleaning policies must come from operator-controlled rules/*.json files.")
        return p

    @staticmethod
    def check_columns(headers: list[str], names: list[str]) -> None:
        missing = set(names) - set(headers)
        if missing:
            raise GuardError(f"Referenced columns do not exist: {', '.join(sorted(missing))}")

    @staticmethod
    def row_errors(row: dict, rules: Rules) -> list[dict]:
        errors = []
        for col in rules.required_values:
            if not row[col].strip():
                errors.append({"column": col, "code": "missing_value"})
        for col, kind in rules.types.items():
            value = row[col]
            if not value.strip():
                continue
            valid = True
            if kind == "integer":
                valid = re.fullmatch(r"[+-]?[0-9]+", value) is not None
            elif kind == "decimal":
                try:
                    valid = math.isfinite(float(value))
                except ValueError:
                    valid = False
            if not valid:
                errors.append({"column": col, "code": f"invalid_{kind}"})
        for col, allowed in rules.allowed_labels.items():
            if row[col].strip() and row[col] not in allowed:
                errors.append({"column": col, "code": "invalid_label"})
        return errors

    def validate_rows(self, headers: list[str], rows: list[dict], rules: Rules) -> dict:
        missing = sorted(set(rules.required_columns) - set(headers))
        references = [*rules.required_values, *rules.types, *rules.allowed_labels, *rules.duplicate_keys]
        missing_refs = sorted(set(references) - set(headers))
        if missing or missing_refs:
            return {"valid": False, "records": len(rows), "schema_errors": {"missing_columns": sorted(set(missing+missing_refs))}, "invalid_records": None, "issues": [], "duplicate_records": None}
        issues, counts, invalid = [], {}, 0
        for record, row in enumerate(rows, 1):
            errors = self.row_errors(row, rules)
            invalid += bool(errors)
            for e in errors:
                counts[e["code"]] = counts.get(e["code"], 0)+1
                if len(issues) < 100:
                    issues.append({"record": record, **e})
        duplicates = self.duplicates_rows(rows, rules.duplicate_keys or headers)
        return {"valid": invalid == 0 and duplicates["duplicate_records"] == 0, "records": len(rows), "invalid_records": invalid, "issue_counts": counts, "issues": issues, "issues_truncated": sum(counts.values()) > len(issues), **duplicates}

    @staticmethod
    def duplicates_rows(rows: list[dict], keys: list[str]) -> dict:
        seen, samples, count = {}, [], 0
        for record, row in enumerate(rows, 1):
            key = tuple(row[k] for k in keys)
            if key in seen:
                count += 1
                if len(samples) < 50:
                    samples.append({"record": record, "duplicate_of": seen[key]})
            else:
                seen[key] = record
        return {"duplicate_records": count, "duplicate_examples": samples, "duplicate_examples_truncated": count > len(samples)}

    def inspect(self, value: str, sample_rows: int = 3) -> dict:
        if not 0 <= sample_rows <= 5:
            raise GuardError("sample_rows must be 0..5.")
        headers, rows, sha = self.dataset(value)
        return {"path": value, "sha256": sha, "records": len(rows), "columns": headers, "missing_values": {h: sum(not r[h].strip() for r in rows) for h in headers}, "sample": [{k: v[:200] for k,v in r.items()} for r in rows[:sample_rows]]}

    def validate(self, value: str, rules_path: str) -> dict:
        headers, rows, sha = self.dataset(value)
        return {"dataset_sha256": sha, "rules_sha256": digest(self.read_bytes(rules_path)), **self.validate_rows(headers, rows, self.rules(rules_path))}

    @staticmethod
    def csv_bytes(headers: list[str], rows: list[dict]) -> bytes:
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(stream, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        return stream.getvalue().encode("utf-8")

    def clean(self, req: CleanRequest) -> dict:
        with self.lock:
            headers, rows, source_sha = self.dataset(req.dataset)
            if source_sha != req.expected_dataset_sha256:
                raise GuardError("Dataset version conflict. Inspect and validate again.")
            for path, expected in [(req.rules_path, req.expected_rules_sha256), (req.policy_path, req.expected_policy_sha256)]:
                if digest(self.read_bytes(path)) != expected:
                    raise GuardError("Rules or policy version conflict. Read the current files again.")
            rules = self.rules(req.rules_path)
            self.operator_rule_file(req.policy_path)
            try:
                policy = Cleaning.model_validate_json(self.text(req.policy_path))
            except ValueError:
                raise GuardError("Invalid cleaning policy JSON.") from None
            self.check_columns(headers, [*rules.required_columns, *rules.required_values, *rules.types, *rules.allowed_labels, *rules.duplicate_keys, *policy.trim_columns, *policy.label_mappings])
            keys = rules.duplicate_keys or headers
            kept, excluded, seen = [], [], set()
            trimmed_cells, mapped_cells = 0, 0
            for number, original in enumerate(rows, 1):
                row = dict(original)
                for col in policy.trim_columns:
                    value = row[col].strip()
                    trimmed_cells += value != row[col]
                    row[col] = value
                for col, mapping in policy.label_mappings.items():
                    value = mapping.get(row[col], row[col])
                    mapped_cells += value != row[col]
                    row[col] = value
                errors = self.row_errors(row, rules)
                key = tuple(row[k] for k in keys)
                reason = None
                if errors and policy.exclude_invalid:
                    reason = "validation:" + ";".join(f"{e['column']}:{e['code']}" for e in errors)
                elif key in seen and policy.deduplicate:
                    reason = "duplicate"
                if reason:
                    excluded.append({"record": number, "reason": reason, "original": original})
                else:
                    kept.append(row)
                    seen.add(key)
            run = self.path(f"datasets/cleaned/{req.output_name}")
            if run.exists():
                raise GuardError("Output name already exists. Choose a new name; outputs are never overwritten.")
            payload = self.csv_bytes(headers, kept)
            validation = self.validate_rows(headers, kept, rules)
            report = {"source": req.dataset, "source_sha256": source_sha, "rules_sha256": req.expected_rules_sha256, "policy_sha256": req.expected_policy_sha256, "input_records": len(rows), "output_records": len(kept), "excluded_records": len(excluded), "trimmed_cells": trimmed_cells, "mapped_cells": mapped_cells, "cleaned_sha256": digest(payload), "validation": validation}
            run.parent.mkdir(parents=True, exist_ok=True)
            temp = run.parent / f".staging-{uuid.uuid4().hex}"
            temp.mkdir()
            try:
                (temp/"cleaned.csv").write_bytes(payload)
                (temp/"excluded.json").write_text(json.dumps(excluded, indent=2, ensure_ascii=False), encoding="utf-8")
                (temp/"report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
                os.rename(temp, run)
            finally:
                if temp.exists():
                    for f in temp.iterdir():
                        f.unlink()
                    temp.rmdir()
            return {**report, "outputs": {"cleaned": self.relative(run/"cleaned.csv"), "excluded": self.relative(run/"excluded.json"), "report": self.relative(run/"report.json")}}
