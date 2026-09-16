#!/usr/bin/env python3
"""Validate Obtainium configuration against manifest.json and APK assets.

This script performs strict verification on obtainium.json:
  1. Validates Obtainium schema (id, name, url, author, additionalSettings).
  2. Ensures additionalSettings contains valid JSON with apkFilterRegEx,
     versionExtractionRegEx, and matchGroupToUse.
  3. Tests that apkFilterRegEx matches EXACTLY ONE APK from manifest.json.
  4. Tests that versionExtractionRegEx extracts the EXACT built_version recorded
     in manifest.json for that APK.

Exit code:
  0 on complete validation success
  1 if any validation error occurs
"""
import re
import sys
import json
from pathlib import Path
from typing import Dict, Any, List

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def validate_obtainium_bundle(obtainium_path: Path, manifest_path: Path) -> bool:
    if not obtainium_path.exists():
        print(f"❌ Obtainium file not found: {obtainium_path}", file=sys.stderr)
        return False

    if not manifest_path.exists():
        print(f"❌ Manifest file not found: {manifest_path}", file=sys.stderr)
        return False

    try:
        with obtainium_path.open("r", encoding="utf-8") as f:
            bundle = json.load(f)
    except Exception as e:
        print(f"❌ Failed to parse JSON from {obtainium_path}: {e}", file=sys.stderr)
        return False

    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"❌ Failed to parse JSON from {manifest_path}: {e}", file=sys.stderr)
        return False

    apps: List[Dict[str, Any]] = bundle.get("apps", [])
    if not apps:
        print(f"❌ No apps found in {obtainium_path}", file=sys.stderr)
        return False

    entries: Dict[str, Any] = manifest.get("entries", {})
    all_apks: List[str] = [e["apk"] for e in entries.values() if e.get("apk")]

    # Map apk filename to entry for exact version verification
    apk_to_entry: Dict[str, Dict[str, Any]] = {
        e["apk"]: e for e in entries.values() if e.get("apk")
    }

    errors: List[str] = []
    print(f"🔍 Validating {len(apps)} Obtainium app configurations against {len(all_apks)} manifest APKs...\n")

    for idx, app in enumerate(apps, 1):
        app_name = app.get("name", f"App #{idx}")
        app_id = app.get("id", "")
        url = app.get("url", "")
        settings_str = app.get("additionalSettings", "")

        # 1. Validate required fields
        if not app_id:
            errors.append(f"[{app_name}] Missing required 'id' field")
            continue
        if not url or not url.startswith("https://github.com/"):
            errors.append(f"[{app_name}] Invalid or non-GitHub 'url': {url}")
            continue
        if not settings_str:
            errors.append(f"[{app_name}] Missing 'additionalSettings'")
            continue

        # 2. Parse additionalSettings JSON
        try:
            settings = json.loads(settings_str)
        except Exception as e:
            errors.append(f"[{app_name}] additionalSettings is not valid JSON string: {e}")
            continue

        filter_regex_str = settings.get("apkFilterRegEx", "")
        ver_regex_str = settings.get("versionExtractionRegEx", "")
        group_to_use = settings.get("matchGroupToUse", "1")

        if not filter_regex_str:
            errors.append(f"[{app_name}] Missing 'apkFilterRegEx' in additionalSettings")
            continue
        if not ver_regex_str:
            errors.append(f"[{app_name}] Missing 'versionExtractionRegEx' in additionalSettings")
            continue

        # 3. Test apkFilterRegEx
        try:
            filter_pattern = re.compile(filter_regex_str)
        except re.error as e:
            errors.append(f"[{app_name}] Invalid regex in apkFilterRegEx '{filter_regex_str}': {e}")
            continue

        matching_apks = [apk for apk in all_apks if filter_pattern.search(apk)]

        if len(matching_apks) == 0:
            errors.append(f"[{app_name}] apkFilterRegEx '{filter_regex_str}' matched 0 APKs in manifest")
            continue
        elif len(matching_apks) > 1:
            errors.append(
                f"[{app_name}] apkFilterRegEx '{filter_regex_str}' matched MULTIPLE ({len(matching_apks)}) APKs: {matching_apks}"
            )
            continue

        matched_apk = matching_apks[0]
        entry = apk_to_entry.get(matched_apk, {})
        expected_version = entry.get("built_version", "")

        # 4. Test versionExtractionRegEx
        try:
            ver_pattern = re.compile(ver_regex_str)
        except re.error as e:
            errors.append(f"[{app_name}] Invalid regex in versionExtractionRegEx '{ver_regex_str}': {e}")
            continue

        match = ver_pattern.search(matched_apk)
        if not match:
            errors.append(
                f"[{app_name}] versionExtractionRegEx '{ver_regex_str}' failed to match filename '{matched_apk}'"
            )
            continue

        try:
            group_idx = int(group_to_use)
            extracted_version = match.group(group_idx)
        except Exception as e:
            errors.append(
                f"[{app_name}] Could not extract group '{group_to_use}' with versionExtractionRegEx: {e}"
            )
            continue

        if extracted_version != expected_version:
            errors.append(
                f"[{app_name}] Extracted version '{extracted_version}' does not match manifest built_version '{expected_version}' for '{matched_apk}'"
            )
            continue

        print(f"  ✓ {app_name:<28} -> {matched_apk} (v{extracted_version})")

    print("")
    if errors:
        print(f"❌ Obtainium validation failed with {len(errors)} error(s):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return False

    print(f"🎉 All {len(apps)} Obtainium apps passed strict validation successfully!")
    return True


def main() -> int:
    obtainium_path = Path("obtainium.json")
    manifest_path = Path("manifest.json")

    success = validate_obtainium_bundle(obtainium_path, manifest_path)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
