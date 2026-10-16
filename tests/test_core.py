import json
from pathlib import Path
import shutil

import pytest

from datawais.core import CleanRequest, GuardError, Workspace, digest


@pytest.fixture
def ws(tmp_path):
    shutil.copytree(Path(__file__).parents[1]/"fixtures", tmp_path/"workspace")
    return Workspace(tmp_path/"workspace")


@pytest.mark.parametrize("value", ["../outside", "a/../../outside", "C:\\Windows\\win.ini", "/etc/passwd", "\\\\server\\share", "reports/file.txt:stream", "reports/CON.txt", "reports/aux", "reports/file. ", ".runtime/secrets.json", "reports/../rules/questions.json", "reports/\x00bad"])
def test_rejects_path_escapes_and_ambiguous_names(ws, value):
    with pytest.raises(GuardError):
        ws.path(value)


@pytest.mark.parametrize("target", ["datasets/raw/university_questions.csv", "rules/questions.json", "datasets/cleaned/changed.csv", "handoff/PROJECT_STATE.md"])
def test_originals_rules_and_handoff_cannot_be_deleted(ws, target):
    with pytest.raises(GuardError):
        ws.delete(target, "0"*64, True, "admin")


def test_rejects_symlink(ws, tmp_path):
    outside = tmp_path/"outside"
    outside.mkdir()
    try:
        (ws.root/"link").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("OS account cannot create symbolic links")
    with pytest.raises(GuardError):
        ws.path("link/secret.txt")


def test_write_requires_current_hash_and_exact_match(ws):
    result = ws.write("notes/example.txt", "one two one", "admin")
    with pytest.raises(GuardError, match="Version conflict"):
        ws.write("notes/example.txt", "changed", "admin")
    with pytest.raises(GuardError, match="exactly once"):
        ws.replace("notes/example.txt", "one", "ONE", result["sha256"], "admin")
    changed = ws.replace("notes/example.txt", "two", "TWO", result["sha256"], "admin")
    with pytest.raises(GuardError):
        ws.delete("notes/example.txt", changed["sha256"], False, "admin")
    with pytest.raises(GuardError):
        ws.delete("notes/example.txt", changed["sha256"], True, "cleaner")
    assert ws.delete("notes/example.txt", changed["sha256"], True, "admin")["deleted"]


def test_inspector_write_scope(ws):
    ws.write("reports/inspection.json", "{}", "inspector")
    with pytest.raises(GuardError):
        ws.write("notes/forbidden.txt", "x", "inspector")


def test_quoted_commas_and_multiline_records(ws):
    headers, rows, _ = ws.dataset("datasets/raw/university_questions.csv")
    assert len(rows) == 8
    assert rows[6]["question"] == "Where is Building A, room 201?"
    assert rows[7]["question"] == "What is the\nenrollment deadline?"
    assert headers == ["question", "label"]


@pytest.mark.parametrize("text", ["a,a\n1,2\n", "a,\n1,2\n", "a,b\n1\n", 'a,b\n"unclosed,b\n', ""])
def test_malformed_csv_is_rejected(ws, text):
    (ws.root/"datasets/raw/bad.csv").write_text(text, encoding="utf-8")
    with pytest.raises(GuardError):
        ws.dataset("datasets/raw/bad.csv")


def test_limits_and_bounded_reads(ws):
    result = ws.read("handoff/PROJECT_STATE.md", limit=10)
    assert len(result["content"]) == 10
    assert result["next_offset"] == 10
    with pytest.raises(GuardError):
        ws.read("handoff/PROJECT_STATE.md", limit=32001)
    with pytest.raises(GuardError):
        ws.inspect("datasets/raw/university_questions.csv", 6)
    big = ws.root/"datasets/raw/big.csv"
    big.write_bytes(b"x"*(5*1024*1024+1))
    with pytest.raises(GuardError, match="5 MiB"):
        ws.dataset("datasets/raw/big.csv")


def test_validation_reports_real_problems(ws):
    result = ws.validate("datasets/raw/university_questions.csv", "rules/questions.json")
    assert result["valid"] is False
    assert result["records"] == 8
    assert result["invalid_records"] == 2
    assert result["duplicate_records"] == 1
    assert result["issue_counts"] == {"invalid_label": 1, "missing_value": 1}


def request(ws, name="test-clean"):
    paths = ["datasets/raw/university_questions.csv", "rules/questions.json", "rules/cleaning_policy.json"]
    return CleanRequest(dataset=paths[0], rules_path=paths[1], policy_path=paths[2], expected_dataset_sha256=digest(ws.read_bytes(paths[0])), expected_rules_sha256=digest(ws.read_bytes(paths[1])), expected_policy_sha256=digest(ws.read_bytes(paths[2])), output_name=name)


def test_cleaning_preserves_source_and_audits_exclusions(ws):
    before = ws.read_bytes("datasets/raw/university_questions.csv")
    result = ws.clean(request(ws))
    assert result["input_records"] == 8
    assert result["output_records"] == 6
    assert result["excluded_records"] == 2
    assert result["mapped_cells"] == 1
    assert result["trimmed_cells"] == 1
    assert result["validation"]["valid"] is True
    assert ws.read_bytes("datasets/raw/university_questions.csv") == before
    assert ws.validate(result["outputs"]["cleaned"], "rules/questions.json")["valid"]
    excluded = json.loads(ws.text(result["outputs"]["excluded"]))
    assert {r["record"] for r in excluded} == {3, 5}
    assert len(ws.dataset(result["outputs"]["cleaned"])[1]) == 6
    with pytest.raises(GuardError, match="already exists"):
        ws.clean(request(ws))


@pytest.mark.parametrize("field", ["expected_dataset_sha256", "expected_rules_sha256", "expected_policy_sha256"])
def test_stale_inputs_prevent_cleaning(ws, field):
    req = request(ws).model_copy(update={field: "0"*64})
    with pytest.raises(GuardError, match="conflict"):
        ws.clean(req)
    assert not (ws.root/"datasets/cleaned/test-clean").exists()


def test_missing_schema_columns_are_reported(ws):
    (ws.root/"rules/other.json").write_text('{"required_columns":["absent"],"required_values":["absent"]}')
    result = ws.validate("datasets/raw/university_questions.csv", "rules/other.json")
    assert result["valid"] is False
    assert result["schema_errors"]["missing_columns"] == ["absent"]


def test_invalid_rules_and_unknown_cleaning_actions_fail(ws):
    (ws.root/"rules/invalid.json").write_text('{"auto_guess_labels":true}')
    with pytest.raises(GuardError):
        ws.rules("rules/invalid.json")


def test_agent_cannot_substitute_editable_validation_rules(ws):
    ws.write("reports/fake-rules.json", "{}", "inspector")
    with pytest.raises(GuardError, match="operator-controlled"):
        ws.validate("datasets/raw/university_questions.csv", "reports/fake-rules.json")
    ws.write("reports/fake-policy.json", "{}", "cleaner")
    req = request(ws).model_copy(update={"policy_path":"reports/fake-policy.json", "expected_policy_sha256":digest(ws.read_bytes("reports/fake-policy.json"))})
    with pytest.raises(GuardError, match="operator-controlled"):
        ws.clean(req)


def test_invalid_then_valid_duplicate_survivor(ws):
    (ws.root/"datasets/raw/keys.csv").write_text("id,label\n1,wrong\n1,valid\n")
    (ws.root/"rules/keys.json").write_text(json.dumps({"required_values":["id","label"],"allowed_labels":{"label":["valid"]},"duplicate_keys":["id"]}))
    req = request(ws).model_copy(update={"dataset":"datasets/raw/keys.csv", "rules_path":"rules/keys.json", "expected_dataset_sha256":digest(ws.read_bytes("datasets/raw/keys.csv")), "expected_rules_sha256":digest(ws.read_bytes("rules/keys.json"))})
    (ws.root/"rules/key-policy.json").write_text('{"deduplicate":true,"exclude_invalid":true}')
    req = req.model_copy(update={"policy_path":"rules/key-policy.json", "expected_policy_sha256":digest(ws.read_bytes("rules/key-policy.json"))})
    result = ws.clean(req)
    assert result["output_records"] == 1
    assert result["validation"]["valid"]


def test_numeric_rules_do_not_accept_nan_infinity_or_fractional_integers(ws):
    (ws.root/"datasets/raw/numbers.csv").write_text("count,amount\n1,2.5\n1.5,NaN\n2,Infinity\n")
    (ws.root/"rules/numbers.json").write_text('{"types":{"count":"integer","amount":"decimal"}}')
    result = ws.validate("datasets/raw/numbers.csv", "rules/numbers.json")
    assert result["issue_counts"] == {"invalid_integer":1,"invalid_decimal":2}
