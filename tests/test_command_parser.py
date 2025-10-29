import pytest
from cerberus import Validator
from agents.command_poller import SCHEMAS

def test_scan_site_ok():
    v = Validator(SCHEMAS["SCAN_SITE"])
    assert v.validate({"domain": "example.com"})

def test_scan_site_fail():
    v = Validator(SCHEMAS["SCAN_SITE"])
    assert not v.validate({})

def test_publish_report_ok():
    v = Validator(SCHEMAS["PUBLISH_REPORT"])
    assert v.validate({"client": "acme", "dataset": "q3", "format": "pdf"})

def test_format_enum():
    v = Validator(SCHEMAS["PUBLISH_REPORT"])
    assert not v.validate({"client": "x", "dataset": "y", "format": "ppt"})