"""Reproducibly generate the synthetic scenario, never download business data."""

import argparse
import csv
import hashlib
import json
import random
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chainscope.model import (AS_OF, DB_PATH, ROOT, SCHEMA_VERSION, SEED, TABLES,
                             load_views, within_project)


def scenario():
    rng = random.Random(SEED)
    today = date.fromisoformat(AS_OF)
    data = {table: [] for table in TABLES}
    data["snapshot"] = [{"id": "SC-20261004", "as_of": AS_OF,
                         "label": "Synthetic GCC manufacturing network"}]
    for i, (name, region) in enumerate([
        ("Atlas Components", "UAE"), ("Crescent Precision", "Saudi Arabia"),
        ("Harbor Circuits", "Oman"), ("Meridian Metals", "Bahrain"),
        ("Nova Motion", "Qatar"), ("Vertex Materials", "Kuwait"),
    ]):
        data["suppliers"].append(dict(id=f"SUP-{i+1:03}", name=name, region=region))
    for i, (name, category) in enumerate([
        ("Control module", "Electronics"), ("Pressure sensor", "Electronics"),
        ("Drive assembly", "Mechanical"), ("Valve body", "Mechanical"),
        ("Cooling fan", "Thermal"), ("Power board", "Electronics"),
        ("Seal kit", "Consumables"), ("Steel housing", "Mechanical"),
    ]):
        part = f"PRT-{i+1:03}"
        data["parts"].append(dict(id=part, name=name, category=category))
        for s in ([i % 6] if i < 3 else [i % 6, (i+1) % 6]):
            data["sourcing"].append(dict(id=f"SRC-{len(data['sourcing'])+1:03}",
                                        supplier_id=f"SUP-{s+1:03}",
                                        part_id=part, active=1))
    for i, (name, region) in enumerate([
        ("Jebel Ali", "UAE"), ("Dammam", "Saudi Arabia"), ("Sohar", "Oman"),
    ]):
        plant = f"PLT-{i+1:03}"
        data["plants"].append(dict(id=plant, name=name, region=region))
        for j in range(8):
            safety = 60 + j * 10
            stock = safety - 20 - i * 5 if (i * 8 + j) % 5 == 0 else safety + rng.randint(25, 160)
            data["inventory"].append(dict(id=f"INV-{i*8+j+1:03}", part_id=f"PRT-{j+1:03}",
                                          plant_id=plant, on_hand=stock, safety_stock=safety))
    for i, (name, sector) in enumerate([
        ("Aster Mobility", "Transport"), ("Gulf Grid Systems", "Energy"),
        ("Oasis Industrial", "Manufacturing"), ("Pearl Automation", "Automation"),
        ("Summit Cooling", "Infrastructure"), ("Tidal Engineering", "Engineering"),
    ]):
        data["customers"].append(dict(id=f"CUS-{i+1:03}", name=name, sector=sector))
    for i in range(32):
        part_index = i % 8
        if i < 24:
            promised = today - timedelta(days=24-i)
            received = promised + timedelta(days=1 if i % 3 == 0 else -1)
        else:
            promised = today + timedelta(days=i-29)
            received = None
        data["shipments"].append(dict(
            id=f"SHP-{i+1:03}", supplier_id=f"SUP-{part_index%6+1:03}",
            part_id=f"PRT-{part_index+1:03}", plant_id=f"PLT-{(i//8)%3+1:03}",
            promised_date=promised.isoformat(),
            received_date=received.isoformat() if received else None, quantity=160+i*5,
        ))
    for i in range(14):
        order_id = f"ORD-{i+1:03}"
        data["orders"].append(dict(
            id=order_id, customer_id=f"CUS-{i%6+1:03}", plant_id=f"PLT-{(i//4)%3+1:03}",
            due_date=(today + timedelta(days=i-6)).isoformat(),
        ))
        for j in range(2):
            n = i*2+j
            quantity = 40 + (n % 4)*10
            fulfilled = quantity if i < 4 else (n % 3)*10
            line_id = f"LIN-{n+1:03}"
            data["order_lines"].append(dict(
                id=line_id, order_id=order_id, part_id=f"PRT-{n%8+1:03}",
                quantity=quantity, fulfilled_quantity=fulfilled,
                unit_price_cents=(125 + (n % 8)*35)*100,
            ))
            data["allocations"].append(dict(
                id=f"ALC-{n+1:03}", shipment_id=f"SHP-{n+1:03}",
                order_line_id=line_id, quantity=quantity,
            ))
    return data


def sql_literal(value):
    if value is None:
        return "NULL"
    if isinstance(value, int):
        return str(value)
    return "'" + value.replace("'", "''") + "'"


def generate(destination=ROOT / "data"):
    destination = within_project(destination)
    destination.mkdir(parents=True, exist_ok=True)
    db_path = within_project(destination / "chainscope.sqlite3")
    data = scenario()
    temp = within_project(destination / "chainscope.build.sqlite3")
    if temp.exists():
        temp.unlink()
    db = sqlite3.connect(temp)
    try:
        db.execute("PRAGMA foreign_keys = ON")
        for table, columns in TABLES.items():
            db.execute(f"CREATE TABLE {table} ({columns})")
            for record in data[table]:
                names = ", ".join(record)
                marks = ", ".join("?" for _ in record)
                db.execute(f"INSERT INTO {table} ({names}) VALUES ({marks})", tuple(record.values()))
        db.commit()
        load_views(db)
        violations = db.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise ValueError(f"Foreign key validation failed: {len(violations)} violations")
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("SQLite integrity check failed")
    finally:
        db.close()
    temp.replace(db_path)
    files = {}
    statements = [
        "-- GENERATED synthetic data. Run after 01_setup.sql, in CHAINSCOPE_DEMO.CORE.",
        "-- Replays skip existing source IDs; they do not overwrite source records.",
        "USE DATABASE CHAINSCOPE_DEMO;", "USE SCHEMA CORE;", "BEGIN TRANSACTION;",
    ]
    for table, records in data.items():
        path = within_project(destination / f"{table}.csv")
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
        files[path.name] = {"rows": len(records), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for record in records:
            statements.append(
                f"INSERT INTO {table} ({', '.join(record)}) SELECT "
                f"{', '.join(sql_literal(v) for v in record.values())} "
                f"WHERE NOT EXISTS (SELECT 1 FROM {table} WHERE id = {sql_literal(record['id'])});"
            )
    statements.append("COMMIT;")
    seed_path = within_project(destination / "snowflake_seed.sql")
    seed_path.write_text("\n".join(statements) + "\n", encoding="utf-8")
    files[seed_path.name] = {"sha256": hashlib.sha256(seed_path.read_bytes()).hexdigest()}
    files[db_path.name] = {"sha256": hashlib.sha256(db_path.read_bytes()).hexdigest()}
    manifest = {
        "source": "Algorithmic synthetic scenario; scripts/generate_data.py",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "as_of": AS_OF, "seed": SEED, "schema_version": SCHEMA_VERSION,
        "usage": "Synthetic demonstration only. Fictional entities; no real client or personal data.",
        "license": "CC0-1.0 for generated scenario data",
        "command": "python scripts/generate_data.py", "files": files,
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {"database": str(db_path), "source_records": sum(map(len, data.values())),
            "tables": len(data), "foreign_key_violations": 0, "integrity_check": "ok",
            "rows": {name: len(records) for name, records in data.items()}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    print(json.dumps(generate(args.output), indent=2))
