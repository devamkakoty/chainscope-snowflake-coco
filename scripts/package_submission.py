"""Create a bounded submission ZIP and exact file inventory inside artifacts/."""

import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chainscope.model import ROOT, within_project

SOURCE_DIRS = ["chainscope", "scripts", "static", "tests", "snowflake", "coco", "data", "docs"]
ROOT_FILES = [".gitignore", "LICENSE", "README.md", "SUBMISSION.md", "app.py"]


def main():
    artifacts = within_project(ROOT / "artifacts")
    artifacts.mkdir(exist_ok=True)
    files = [ROOT / name for name in ROOT_FILES]
    for directory in SOURCE_DIRS:
        files += [p for p in (ROOT / directory).rglob("*") if p.is_file()
                  and "__pycache__" not in p.parts and p.suffix != ".pyc"]
    files += [p for p in artifacts.glob("*.md") if p.is_file()]
    files += [p for p in artifacts.glob("*verification.json") if p.is_file()]
    files += [p for p in (artifacts / "screenshots").glob("[0-9]*.png") if p.is_file()]
    files = sorted(set(files), key=lambda p: p.relative_to(ROOT).as_posix())
    for path in files:
        within_project(path)
    listing = ["# Submission File Inventory", "",
               "All paths below are new within this project. No pre-existing project files existed.",
               "Generated datasets, images and archive are produced by direct scripts, not patches.",
               "Browser profiles, temporary files, logs and caches are excluded.", ""]
    listing += [f"- `{p.relative_to(ROOT).as_posix()}` ({p.stat().st_size:,} bytes)" for p in files]
    listing += ["", "Generated packaging records:", "- `artifacts/FILES.md`",
                "- `artifacts/submission-manifest.json`", "- `artifacts/chainscope-submission.zip`", ""]
    inventory = artifacts / "FILES.md"
    inventory.write_text("\n".join(listing), encoding="utf-8")
    files = sorted(set(files + [inventory]), key=lambda p: p.relative_to(ROOT).as_posix())
    archive = within_project(artifacts / "chainscope-submission.zip")
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in files:
            bundle.write(path, path.relative_to(ROOT).as_posix())
    with zipfile.ZipFile(archive) as bundle:
        bad = bundle.testzip()
        if bad:
            raise ValueError(f"Archive integrity failure: {bad}")
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Local ChainScope project only", "command": "python scripts/package_submission.py",
        "usage": "Prepared locally only; not uploaded or submitted",
        "license": "MIT code; CC0-1.0 synthetic data; Lucide notices included", "schema_version": 1,
        "archive": archive.name, "archive_bytes": archive.stat().st_size,
        "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "files": [{"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size,
                   "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in files],
    }
    (artifacts / "submission-manifest.json").write_text(json.dumps(manifest, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"archive": str(archive), "files": len(files), "bytes": archive.stat().st_size,
                      "sha256": manifest["sha256"], "integrity": "ok"}, indent=2))


if __name__ == "__main__":
    main()
