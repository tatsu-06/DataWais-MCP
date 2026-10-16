import json
import pytest
from datawais.tunnel import DOMAIN, configure_hostname


def test_hostname_update_keeps_tokens_private_and_updates_all_clients(tmp_path):
    tokens = {"inspector":"i"*40,"cleaner":"c"*40,"admin":"a"*40}
    (tmp_path/"secrets.json").write_text(json.dumps({"tokens":tokens}))
    for hostname in ["first-demo.trycloudflare.com","recovered-demo.trycloudflare.com"]:
        configure_hostname(hostname,tmp_path)
        assert (tmp_path/"public-url.txt").read_text() == f"https://{hostname}/mcp"
        assert (tmp_path/"public-host.txt").read_text() == hostname
        config = json.loads((tmp_path/"public-clients.json").read_text())["mcpServers"]
        for role,token in tokens.items():
            assert config[f"datawais-{role}"]["headers"]["Authorization"] == f"Bearer {token}"
            assert config[f"datawais-{role}"]["url"] == f"https://{hostname}/mcp"
        assert not list(tmp_path.glob("*.tmp"))


@pytest.mark.parametrize("hostname", ["evil.example", "good.trycloudflare.com.evil", "../bad.trycloudflare.com", "https://good.trycloudflare.com", "good.trycloudflare.com:443"])
def test_rejects_unexpected_hostname_before_writing(tmp_path,hostname):
    with pytest.raises(ValueError):
        configure_hostname(hostname,tmp_path)
    assert not list(tmp_path.iterdir())


def test_extracts_exact_quick_tunnel_url():
    assert DOMAIN.search("INF | https://a-valid-host.trycloudflare.com |").group(1) == "a-valid-host.trycloudflare.com"
    assert DOMAIN.search("https://valid.trycloudflare.com.evil/") is None
