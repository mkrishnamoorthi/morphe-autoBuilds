#!/usr/bin/env python3
"""Update README.md with Obtainium documentation and app badges."""
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.generate_obtainium import get_display_name

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main() -> int:
    readme_path = Path("README.md")
    manifest_path = Path("manifest.json")

    if not readme_path.exists() or not manifest_path.exists():
        print("❌ README.md or manifest.json not found")
        return 1

    with manifest_path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    entries = manifest.get("entries", {})

    table_rows = [
        "| Application | Package Name | Patch Source | Arch | Obtainium (1-Click) |",
        "| :--- | :--- | :--- | :---: | :---: |",
    ]

    for key, v in sorted(entries.items(), key=lambda x: x[1].get("app_name", "")):
        app_name = v.get("app_name", "")
        disp = get_display_name(app_name)
        pkg = v.get("package", "")
        source = v.get("source", "")
        arch = v.get("arch", "arm64-v8a")
        url = v.get("obtainium_url", "")
        badge = (
            f"[![Add to Obtainium](https://img.shields.io/badge/Obtainium-Add-7C3AED?style=flat-square&logo=android&logoColor=white)]({url})"
            if url
            else "Pending build"
        )
        table_rows.append(f"| **{disp}** | `{pkg}` | {source} | `{arch}` | {badge} |")

    table_text = "\n".join(table_rows)

    obtainium_section = """### 📲 Obtainium Auto-Updates & 1-Click Install

This repository provides full first-class integration with [**Obtainium**](https://github.com/ImranR98/Obtainium), allowing you to install and automatically receive daily background updates for any or all apps directly from GitHub Releases with zero manual downloads.

#### 🚀 Option 1: 1-Click Single App Install
Click the **Add to Obtainium** badge for any app in the catalog below on your Android device (with Obtainium installed). Obtainium will automatically open with the exact repository, APK filter regex, and version extractor preconfigured!

#### 📦 Option 2: Bulk Import All Apps
To import the entire curated catalog at once:
1. Open **Obtainium** on your Android device.
2. Tap the **+** button (or navigate to **Import / Export**) $\\rightarrow$ select **Import from URL**.
3. Paste the configuration URL:
   ```text
   https://raw.githubusercontent.com/yashrajrocxx/Mophe-AutoBuilds/main/obtainium.json
   ```
4. Tap **Import**. All apps will be added to your Obtainium database and will automatically track daily releases.

> [!NOTE]
> **User Control & Local State:**
> In Obtainium, importing an app or the `obtainium.json` bundle adds the configuration to your device's local database. It is **not** a forced synchronization—you retain full freedom to install, delete, pause, or pin whichever apps you choose."""

    new_section = f"""{obtainium_section}

### 📱 Supported Apps & Patch Repositories

This repository compiles optimized builds using specific community patch repositories for our curated application catalog:

{table_text}

*(All builds are target-optimized for their respective architectures to reduce bundle sizes and increase device efficiency).*"""

    content = readme_path.read_text(encoding="utf-8")

    # Find the target section
    old_start = "### 📱 Supported Apps & Patch Repositories"
    old_end = "*(All builds are target-optimized for `arm64-v8a` to reduce bundle sizes and increase device efficiency).*"

    # If it was already updated before, handle new footer
    alt_old_end = "*(All builds are target-optimized for their respective architectures to reduce bundle sizes and increase device efficiency).*"

    if old_start not in content:
        print("❌ Could not find apps section in README.md")
        return 1

    # Check if obtainium section already exists
    if "### 📲 Obtainium Auto-Updates" in content:
        start_idx = content.find("### 📲 Obtainium Auto-Updates")
    else:
        start_idx = content.find(old_start)

    end_idx = -1
    if old_end in content:
        end_idx = content.find(old_end) + len(old_end)
    elif alt_old_end in content:
        end_idx = content.find(alt_old_end) + len(alt_old_end)

    if end_idx == -1:
        print("❌ Could not find end marker of apps section in README.md")
        return 1

    updated_content = content[:start_idx] + new_section + content[end_idx:]
    readme_path.write_text(updated_content, encoding="utf-8", newline="\n")
    print(f"✅ README.md updated successfully with {len(entries)} apps and Obtainium documentation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
