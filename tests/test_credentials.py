import json
import pytest
from datawais.server import load_token_roles


def test_environment_credentials_override_private_bootstrap_file(tmp_path):
    roles = {"admin":"a"*40,"inspector":"i"*40,"cleaner":"c"*40}
    env = {f"DATAWAIS_{role.upper()}_TOKEN":token for role,token in roles.items()}
    result = load_token_roles(tmp_path/"absent.json",env)
    assert result == {token:role for role,token in roles.items()}


def test_partial_environment_does_not_silently_mix_credentials(tmp_path):
    with pytest.raises(ValueError,match="all three"):
        load_token_roles(tmp_path/"absent.json",{"DATAWAIS_ADMIN_TOKEN":"a"*40})


def test_private_bootstrap_remains_supported(tmp_path):
    path = tmp_path/"secrets.json"
    tokens = {"admin":"a"*40,"inspector":"i"*40,"cleaner":"c"*40}
    path.write_text(json.dumps({"tokens":tokens}))
    assert load_token_roles(path,{}) == {token:role for role,token in tokens.items()}


@pytest.mark.parametrize("tokens", [
    {"admin":"a"*40,"inspector":"a"*40,"cleaner":"c"*40},
    {"admin":"short","inspector":"i"*40,"cleaner":"c"*40},
    {"admin":"a"*40,"inspector":"i"*40,"cleaner":"\u00e9"*40},
    {"admin":"a"*40,"inspector":"i"*40},
])
def test_invalid_role_credentials_are_rejected(tmp_path,tokens):
    path = tmp_path/"secrets.json"
    path.write_text(json.dumps({"tokens":tokens}))
    with pytest.raises(ValueError):
        load_token_roles(path,{})
