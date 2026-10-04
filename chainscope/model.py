"""The source schema and a read-only SQLite adapter."""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "chainscope.sqlite3"
AS_OF = "2026-10-04"
SEED = 20261004
SCHEMA_VERSION = 1

# All monetary amounts are integer USD cents. IDs are stable source keys.
TABLES = {
    "snapshot": "id TEXT PRIMARY KEY, as_of TEXT NOT NULL, label TEXT NOT NULL",
    "suppliers": "id TEXT PRIMARY KEY, name TEXT NOT NULL, region TEXT NOT NULL",
    "parts": "id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL",
    "plants": "id TEXT PRIMARY KEY, name TEXT NOT NULL, region TEXT NOT NULL",
    "customers": "id TEXT PRIMARY KEY, name TEXT NOT NULL, sector TEXT NOT NULL",
    "sourcing": """id TEXT PRIMARY KEY, supplier_id TEXT REFERENCES suppliers(id),
        part_id TEXT REFERENCES parts(id), active INTEGER NOT NULL CHECK(active IN (0,1))""",
    "inventory": """id TEXT PRIMARY KEY, part_id TEXT REFERENCES parts(id),
        plant_id TEXT REFERENCES plants(id), on_hand INTEGER NOT NULL CHECK(on_hand>=0),
        safety_stock INTEGER NOT NULL CHECK(safety_stock>=0), UNIQUE(part_id,plant_id)""",
    "shipments": """id TEXT PRIMARY KEY, supplier_id TEXT REFERENCES suppliers(id),
        part_id TEXT REFERENCES parts(id), plant_id TEXT REFERENCES plants(id),
        promised_date TEXT NOT NULL, received_date TEXT,
        quantity INTEGER NOT NULL CHECK(quantity>0)""",
    "orders": """id TEXT PRIMARY KEY, customer_id TEXT REFERENCES customers(id),
        plant_id TEXT REFERENCES plants(id), due_date TEXT NOT NULL""",
    "order_lines": """id TEXT PRIMARY KEY, order_id TEXT REFERENCES orders(id),
        part_id TEXT REFERENCES parts(id), quantity INTEGER NOT NULL CHECK(quantity>0),
        fulfilled_quantity INTEGER NOT NULL CHECK(fulfilled_quantity>=0
            AND fulfilled_quantity<=quantity),
        unit_price_cents INTEGER NOT NULL CHECK(unit_price_cents>=0)""",
    "allocations": """id TEXT PRIMARY KEY, shipment_id TEXT REFERENCES shipments(id),
        order_line_id TEXT REFERENCES order_lines(id),
        quantity INTEGER NOT NULL CHECK(quantity>0), UNIQUE(shipment_id,order_line_id)""",
}

RELATIONS = [
    ("sourcing", "supplier_id", "suppliers"),
    ("sourcing", "part_id", "parts"),
    ("inventory", "part_id", "parts"),
    ("inventory", "plant_id", "plants"),
    ("shipments", "supplier_id", "suppliers"),
    ("shipments", "part_id", "parts"),
    ("shipments", "plant_id", "plants"),
    ("orders", "customer_id", "customers"),
    ("orders", "plant_id", "plants"),
    ("order_lines", "order_id", "orders"),
    ("order_lines", "part_id", "parts"),
    ("allocations", "shipment_id", "shipments"),
    ("allocations", "order_line_id", "order_lines"),
]


def within_project(path):
    """Resolve every generated destination before creating or writing anything."""
    target = Path(path).resolve()
    if target != ROOT and ROOT not in target.parents:
        raise ValueError("Destination must remain inside the ChainScope project")
    if target.drive.upper() != "D:" and ROOT.drive.upper() == "D:":
        raise ValueError("Generated data must remain on D:")
    return target


class ReadConnection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


def connect(path=DB_PATH):
    uri = Path(path).resolve().as_uri() + "?mode=ro"
    db = sqlite3.connect(uri, uri=True, factory=ReadConnection)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only = ON")
    return db


def load_views(db):
    text = (ROOT / "snowflake" / "02_views.sql").read_text(encoding="utf-8")
    # These views otherwise deliberately use the common SQLite/Snowflake subset.
    db.executescript(text.replace("CREATE OR REPLACE VIEW", "CREATE VIEW"))


def rows(db, sql, parameters=()):
    return [dict(row) for row in db.execute(sql, parameters).fetchall()]
