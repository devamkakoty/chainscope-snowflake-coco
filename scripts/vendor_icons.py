"""Fetch a small, local Lucide SVG sprite; not required to run the app."""

import hashlib
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chainscope.model import ROOT, within_project

ICONS = ["layout-dashboard", "messages-square", "network", "book-open", "shield-check",
         "arrow-up-right", "arrow-right", "send", "x", "download", "check",
         "clock", "package", "truck", "lock-keyhole", "factory", "users", "circle-help"]


def main():
    base = "https://raw.githubusercontent.com/lucide-icons/lucide/0.468.0/"
    ns = "http://www.w3.org/2000/svg"
    ET.register_namespace("", ns)
    sprite = ET.Element(f"{{{ns}}}svg")
    sources = []
    for name in ICONS:
        url = f"{base}icons/{name}.svg"
        with urllib.request.urlopen(url, timeout=25) as response:
            raw = response.read()
        tree = ET.fromstring(raw)
        symbol = ET.SubElement(sprite, f"{{{ns}}}symbol", id=name, viewBox="0 0 24 24")
        for child in tree:
            symbol.append(child)
        sources.append({"name": name, "source": url, "sha256": hashlib.sha256(raw).hexdigest()})
    target = within_project(ROOT / "static" / "icons.svg")
    target.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(sprite).write(target, encoding="utf-8", xml_declaration=True)
    with urllib.request.urlopen(base + "LICENSE", timeout=25) as response:
        license_text = response.read().decode()
    (target.parent / "LUCIDE-LICENSE").write_text(license_text, encoding="utf-8")
    (target.parent / "icons-manifest.json").write_text(json.dumps({
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "license": "ISC for Lucide portions; MIT for Feather-derived portions; see LUCIDE-LICENSE",
        "command": "python scripts/vendor_icons.py", "sources": sources,
        "sprite_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Vendored {len(ICONS)} icons, {target.stat().st_size} bytes: {target}")


if __name__ == "__main__":
    main()
