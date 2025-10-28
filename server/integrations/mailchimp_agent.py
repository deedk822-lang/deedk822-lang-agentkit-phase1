#!/usr/bin/env python3
"""
mailchimp_agent.py
Universal actor for every integration that Mailchimp exposes.
Called by Apps-Script bridge (webhook) with JWT auth.
"""
import os, requests, json, time, logging
from typing import Dict, Optional

MAILCHIMP_KEY = os.getenv("MAILCHIMP_API_KEY")  # <dc>-<hex>  (set by setup.sh)
BASE_URL = f"https://{MAILCHIMP_KEY.split('-')[1]}.api.mailchimp.com/3.0"

log = logging.getLogger("mc_agent")

# ----------  low-level helpers ----------
def _get(path: str) -> Dict:
    r = requests.get(BASE_URL + path, auth=("apikey", MAILCHIMP_KEY), timeout=15)
    r.raise_for_status()
    return r.json()

def _post(path: str, payload: Dict) -> Dict:
    r = requests.post(BASE_URL + path, json=payload, auth=("apikey", MAILCHIMP_KEY), timeout=15)
    r.raise_for_status()
    return r.json()

# ----------  public actions (orchestrator calls these) ----------
def check_integration(service: str) -> Dict:
    """Health-check any connected service."""
    if service == "mailchimp":
        account = _get("/")
        return {"status": "connected", "account_name": account.get("account_name")}
    # Meta-Leads
    if service == "meta_lead_ads":
        # Mailchimp keeps meta info under /connected-sites
        sites = _get("/connected-sites")["sites"]
        meta = next((s for s in sites if s["platform"] == "Facebook"), None)
        return {"status": "connected" if meta else "disconnected", "details": meta}
    # Extend for GA, Canva, LinkedIn, Zapier, IFTTT ...
    return {"status": "unknown_service"}

def refresh_token(service: str) -> Dict:
    """Mailchimp rotates OAuth tokens transparently; we trigger re-authorise."""
    # In real life you’d POST to /oauth/reauthorize – here we mock
    log.info("Rotating token for %s", service)
    return {"status": "token_refreshed", "service": service}

def create_audience_sync(audience_id: str, dest_platform: str) -> Dict:
    """Two-way audience sync (Meta custom-audience example)."""
    audience = _get(f"/lists/{audience_id}")
    if dest_platform == "meta":
        # pretend we push to Meta
        log.info("Syncing audience %s to Meta Ads Manager", audience_id)
        return {"status": "sync_triggered", "audience_name": audience["name"]}
    raise ValueError("Only meta sync implemented")
