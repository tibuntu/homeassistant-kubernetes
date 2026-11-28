"""Consistency checks between the code, translations/en.json and icons.json."""

import json
from pathlib import Path
import re

import yaml

COMPONENT_DIR = Path(__file__).parents[1] / "custom_components" / "kubernetes"
STRINGS = json.loads((COMPONENT_DIR / "translations" / "en.json").read_text())
ICONS = json.loads((COMPONENT_DIR / "icons.json").read_text())


def test_literal_translation_keys_exist():
    """Every literal translation_key in the code has a string in en.json."""
    known = set(STRINGS["exceptions"])
    for platform in STRINGS["entity"].values():
        known |= set(platform)
    used = {
        key
        for path in COMPONENT_DIR.glob("*.py")
        for key in re.findall(
            r'translation_key(?:: str)? ?= ?"(\w+)"', path.read_text()
        )
    }
    assert used, "regex no longer matches any translation_key"
    assert used <= known, used - known


def test_icons_match_entity_translations():
    """icons.json only references entity translation keys that exist."""
    for platform, keys in ICONS["entity"].items():
        assert set(keys) <= set(STRINGS["entity"][platform]), platform


def test_workload_namespace_fields():
    """The four workload services share an accurate, translated namespace field."""
    services = yaml.safe_load((COMPONENT_DIR / "services.yaml").read_text())
    for service in (
        "scale_workload",
        "start_workload",
        "stop_workload",
        "restart_workload",
    ):
        field = services[service]["fields"]["namespace"]
        assert field["selector"] == {"text": None}, service
        assert "configured namespace" not in field["description"], service
        translated = STRINGS["services"][service]["fields"]["namespace"]
        assert field["description"] == translated["description"], service
