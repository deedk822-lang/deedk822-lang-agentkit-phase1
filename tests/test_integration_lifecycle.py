import pytest, os, sys, requests, json
from unittest.mock import patch
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "server"))
from integrations.mailchimp_agent import check_integration, refresh_token

@pytest.mark.integration
@patch('integrations.mailchimp_agent.requests.get')
def test_check_mailchimp_health(mock_get):
    mock_get.return_value.json.return_value = {"account_name": "test"}
    rsp = check_integration("mailchimp")
    assert rsp["status"] == "connected"
    assert "account_name" in rsp

@pytest.mark.integration
def test_refresh_token_mock():
    rsp = refresh_token("meta_lead_ads")
    assert rsp["status"] == "token_refreshed"
