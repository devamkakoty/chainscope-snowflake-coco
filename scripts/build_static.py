"""Build a self-contained public synthetic replay in docs/ for GitHub Pages."""

import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chainscope.metrics import CATALOG, ROLES, answer, get_record, normalize, ontology, overview
from chainscope.model import DB_PATH, ROOT, TABLES, connect, within_project


def build():
    if not DB_PATH.exists():
        from scripts.generate_data import generate
        generate()
    destination = within_project(ROOT / "docs")
    assets = within_project(destination / "static")
    assets.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        data = {
            "roles": ROLES, "ontology": ontology(db),
            "overviews": {role: overview(db, role) for role in ROLES},
            "answers": {m["id"]: answer(db, m["id"], "commercial") for m in CATALOG},
            "aliases": {normalize(q): m["id"] for m in CATALOG
                        for q in [m["id"], m["question"], *m["aliases"]]},
            "records": {role: {} for role in ROLES},
        }
        for role in ROLES:
            for table in TABLES:
                for row in db.execute(f"SELECT id FROM {table} ORDER BY id"):
                    record = get_record(db, table, row["id"], role)
                    data["records"][role][record["source"]["href"]] = record
    fixture = within_project(assets / "demo-data.js")
    # Write exact UTF-8/LF bytes so the manifest hashes the same payload that
    # GitHub Pages serves, regardless of the checkout's core.autocrlf setting.
    fixture.write_bytes(
        ("window.CHAINSCOPE_DATA=" + json.dumps(data, separators=(",", ":")) + ";\n")
        .encode("utf-8")
    )
    for name in ["style.css", "icons.svg", "replay.js", "LUCIDE-LICENSE", "icons-manifest.json"]:
        shutil.copyfile(ROOT / "static" / name, within_project(assets / name))
    js = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
    (assets / "app.js").write_text(js.replace("/static/", "./static/"), encoding="utf-8")
    html = (ROOT / "static" / "index.html").read_text(encoding="utf-8")
    html = html.replace("/static/", "./static/").replace(
        '<script src="./static/app.js" defer></script>',
        '<script src="./static/demo-data.js" defer></script>\n'
        '  <script src="./static/replay.js" defer></script>\n'
        '  <script src="./static/app.js" defer></script>',
    )
    html = html.replace("Local engine", "Static replay").replace("Online</span>", "Public fixture</span>")
    html = html.replace('<main id="main"', '<div class="replay-notice">Static replay &middot; Public synthetic fixture &middot; Role switches illustrate policy, not access control.</div>\n    <main id="main"')
    (destination / "index.html").write_text(html, encoding="utf-8")
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Local SQLite synthetic snapshot; scripts/build_static.py",
        "command": "python scripts/build_static.py",
        "usage": "Public synthetic replay only. No credentials, authentication or live backend.",
        "schema_version": 1, "license": "CC0-1.0 for fixture data; MIT for project code",
        "fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
        "fixture_bytes": fixture.stat().st_size, "metric_count": len(CATALOG),
        "source_records_per_role": len(data["records"]["operations"]),
    }
    (destination / "static-manifest.json").write_bytes(
        (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    )
    print(json.dumps({"destination": str(destination), "fixture_bytes": fixture.stat().st_size,
                      "metrics": len(CATALOG), "source_records_per_role": manifest["source_records_per_role"]}, indent=2))


if __name__ == "__main__":
    build()
