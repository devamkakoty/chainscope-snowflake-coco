"""Allowlisted questions, explicit grains, field policy, and record provenance."""

import re
from datetime import date

from chainscope.model import AS_OF, RELATIONS, TABLES, rows

ROLES = {"operations": "Operations analyst", "commercial": "Commercial analyst"}
MONETARY_FIELDS = {"unit_price_cents", "outstanding_value_cents", "at_risk_value_cents"}

CATALOG = [
    {
        "id": "late_shipments", "title": "Late inbound shipments",
        "question": "Which shipments are late?",
        "aliases": ["late shipments", "show late shipments", "late inbound", "what shipments are overdue"],
        "grain": "One inbound shipment", "unit": "shipments", "roles": list(ROLES),
        "definition": "Unreceived shipments with promised_date strictly before the frozen snapshot. "
                      "Due today is not late. Previously received late shipments are excluded.",
        "sql": """SELECT s.id, u.name AS supplier, p.name AS part, t.name AS plant,
                   s.promised_date, s.quantity, s.supplier_id, s.part_id, s.plant_id
                   FROM v_shipments s JOIN suppliers u ON u.id=s.supplier_id
                   JOIN parts p ON p.id=s.part_id JOIN plants t ON t.id=s.plant_id
                   WHERE s.is_open_late=1 ORDER BY s.promised_date, s.id""",
        "columns": [("id", "Shipment"), ("supplier", "Supplier"), ("part", "Part"),
                    ("plant", "Plant"), ("days_late", "Days late"), ("quantity", "Units")],
    },
    {
        "id": "supplier_reliability", "title": "Supplier on-time delivery",
        "question": "Which suppliers have the lowest on-time delivery?",
        "aliases": ["supplier reliability", "supplier on time delivery", "supplier performance", "on time delivery"],
        "grain": "One supplier; shipment-weighted, not unit-weighted",
        "unit": "%", "roles": list(ROLES),
        "definition": "Received on or before promise / all shipments promised before the snapshot. "
                      "Open overdue shipments stay in the denominator. Future and due-today promises "
                      "are excluded. A supplier with no due shipments has a null rate, not 100%.",
        "sql": """SELECT u.id, u.name AS supplier, u.region,
                   COALESCE(SUM(s.is_due),0) AS due_shipments,
                   COALESCE(SUM(s.is_on_time),0) AS on_time_shipments,
                   ROUND(100.0*SUM(s.is_on_time)/NULLIF(SUM(s.is_due),0),1) AS on_time_pct
                   FROM suppliers u LEFT JOIN v_shipments s ON s.supplier_id=u.id
                   GROUP BY u.id, u.name, u.region
                   ORDER BY CASE WHEN SUM(s.is_due)>0 THEN 0 ELSE 1 END, on_time_pct, u.id""",
        "columns": [("supplier", "Supplier"), ("region", "Region"),
                    ("due_shipments", "Due"), ("on_time_shipments", "On time"),
                    ("on_time_pct", "OTD %")],
    },
    {
        "id": "plant_shortages", "title": "Inventory below safety stock",
        "question": "Which plants are below safety stock?",
        "aliases": ["plant shortages", "inventory shortages", "safety stock", "low stock"],
        "grain": "One part at one plant", "unit": "positions", "roles": list(ROLES),
        "definition": "Positions where on_hand < safety_stock. Gap = safety_stock - on_hand. "
                      "This is a stocking-policy breach, not proof of a production stoppage.",
        "sql": """SELECT i.id, t.name AS plant, p.name AS part, i.on_hand, i.safety_stock,
                   i.shortage_units, i.plant_id, i.part_id FROM v_inventory i
                   JOIN plants t ON t.id=i.plant_id JOIN parts p ON p.id=i.part_id
                   WHERE i.shortage_units>0 ORDER BY i.shortage_units DESC, i.id""",
        "columns": [("plant", "Plant"), ("part", "Part"), ("on_hand", "On hand"),
                    ("safety_stock", "Safety stock"), ("shortage_units", "Gap")],
    },
    {
        "id": "at_risk_orders", "title": "Customer orders at risk",
        "question": "Which customer orders are at risk?",
        "aliases": ["at risk orders", "orders at risk", "customer impact", "affected orders"],
        "grain": "One order, deduplicated across lines and shipment allocations",
        "unit": "orders", "roles": list(ROLES),
        "definition": "An order is at risk when at least one unfulfilled line is past its order due "
                      "date or has an explicit allocation to an open overdue inbound shipment. "
                      "No inferred joins by plant alone; completed lines never trigger risk.",
        "sql": """SELECT o.id, c.name AS customer, p.name AS plant, o.due_date,
                   o.outstanding_units, o.customer_id, o.plant_id
                   FROM v_orders_ops o JOIN customers c ON c.id=o.customer_id
                   JOIN plants p ON p.id=o.plant_id WHERE o.is_at_risk=1
                   ORDER BY o.due_date, o.id""",
        "columns": [("id", "Order"), ("customer", "Customer"), ("plant", "Plant"),
                    ("due_date", "Due date"), ("outstanding_units", "Open units"), ("reason", "Risk driver")],
    },
    {
        "id": "single_source_parts", "title": "Single-source exposure",
        "question": "Which parts have single-source exposure?",
        "aliases": ["single source parts", "single source exposure", "single sourcing"],
        "grain": "One part; distinct active suppliers",
        "unit": "parts", "roles": list(ROLES),
        "definition": "Parts with exactly one active approved supplier. Inactive agreements do not "
                      "count. Zero-source parts are a separate condition, not single-source.",
        "sql": """SELECT part_id AS id, part_name AS part, category, active_supplier_count
                   FROM v_part_sources WHERE active_supplier_count=1 ORDER BY part_id""",
        "columns": [("id", "Part ID"), ("part", "Part"), ("category", "Category"),
                    ("active_supplier_count", "Active suppliers")],
    },
    {
        "id": "order_fill_rate", "title": "Unit fill rate",
        "question": "What is our order fill rate?",
        "aliases": ["order fill rate", "fill rate", "fulfillment", "fulfilment"],
        "grain": "One order line, rolled up to order; unit-weighted across all orders",
        "unit": "%", "roles": list(ROLES),
        "definition": "100 * SUM(fulfilled_quantity) / SUM(quantity) across all snapshot order lines. "
                      "Not an average of order percentages; no currency or shipment joins.",
        "sql": """SELECT o.id, c.name AS customer, o.ordered_units, o.fulfilled_units,
                   ROUND(100.0*o.fulfilled_units/NULLIF(o.ordered_units,0),1) AS fill_pct,
                   o.customer_id FROM v_orders_ops o JOIN customers c ON c.id=o.customer_id
                   ORDER BY fill_pct, o.id""",
        "columns": [("id", "Order"), ("customer", "Customer"), ("ordered_units", "Ordered"),
                    ("fulfilled_units", "Fulfilled"), ("fill_pct", "Fill %")],
    },
    {
        "id": "revenue_at_risk", "title": "Revenue exposure",
        "question": "What revenue is at risk?",
        "aliases": ["revenue at risk", "financial exposure", "revenue exposure"],
        "grain": "Unfulfilled units on at-risk lines, rolled up to order",
        "unit": "USD", "roles": ["commercial"],
        "definition": "SUM(outstanding units * unit price) for at-risk lines only, in integer USD "
                      "cents. This is gross open-order exposure, not lost revenue, recognized "
                      "revenue, profit, or a prediction. Shipment joins cannot multiply it.",
        "sql": """SELECT o.id, c.name AS customer, o.at_risk_value_cents, o.customer_id
                   FROM v_orders o JOIN customers c ON c.id=o.customer_id
                   WHERE o.is_at_risk=1 ORDER BY o.at_risk_value_cents DESC, o.id""",
        "columns": [("id", "Order"), ("customer", "Customer"), ("exposure", "Exposure (USD)")],
    },
]
BY_ID = {item["id"]: item for item in CATALOG}


class QueryError(Exception):
    def __init__(self, message, status=422, code="unsupported_question"):
        super().__init__(message)
        self.status, self.code = status, code


def normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def resolve(question):
    if not isinstance(question, str) or not question.strip() or len(question) > 500:
        raise QueryError("Enter a supported question of 1 to 500 characters.", 400, "invalid_question")
    key = normalize(question)
    for item in CATALOG:
        if key in {normalize(v) for v in [item["id"], item["question"], *item["aliases"]]}:
            return item
    raise QueryError("That question is outside the approved metric catalog. Choose a listed "
                     "question; no SQL or speculative answer was generated.")


def source(table, key):
    return {"table": table, "id": key, "label": key, "href": f"/api/records/{table}/{key}"}


def unique_sources(references):
    return list({(r["table"], r["id"]): r for r in references}.values())


def order_sources(db, order_id):
    order = rows(db, "SELECT * FROM orders WHERE id=?", (order_id,))[0]
    result = [source("orders", order_id), source("customers", order["customer_id"]),
              source("plants", order["plant_id"])]
    for line in rows(db, "SELECT id,part_id FROM order_lines WHERE order_id=? ORDER BY id", (order_id,)):
        result.extend([source("order_lines", line["id"]), source("parts", line["part_id"])])
        for allocation in rows(db, "SELECT * FROM allocations WHERE order_line_id=? ORDER BY id", (line["id"],)):
            shipment = rows(db, "SELECT * FROM shipments WHERE id=?", (allocation["shipment_id"],))[0]
            result.extend([source("allocations", allocation["id"]), source("shipments", shipment["id"]),
                           source("suppliers", shipment["supplier_id"])])
    return unique_sources(result)


def catalog(role):
    return [{k: v for k, v in item.items() if k not in {"aliases", "sql"}} |
            {"available": role in item["roles"]} for item in CATALOG]


def answer(db, question, role="operations"):
    if role not in ROLES:
        raise QueryError("Unknown demo role.", 400, "invalid_role")
    item = resolve(question)
    if role not in item["roles"]:
        raise QueryError("Revenue exposure is restricted to the Commercial analyst demo role. "
                         "No financial query was executed.", 403, "forbidden_metric")
    result = rows(db, item["sql"])
    metric_id = item["id"]
    for row in result:
        refs = []
        if metric_id == "late_shipments":
            refs = [source("shipments", row["id"]), source("suppliers", row["supplier_id"]),
                    source("parts", row["part_id"]), source("plants", row["plant_id"])]
            row["days_late"] = (date.fromisoformat(AS_OF)-date.fromisoformat(row["promised_date"])).days
        elif metric_id == "supplier_reliability":
            refs = [source("suppliers", row["id"])]
            refs += [source("shipments", s["id"]) for s in rows(
                db, "SELECT id FROM v_shipments WHERE supplier_id=? AND is_due=1 ORDER BY id", (row["id"],))]
        elif metric_id == "plant_shortages":
            refs = [source("inventory", row["id"]), source("parts", row["part_id"]),
                    source("plants", row["plant_id"])]
        elif metric_id == "single_source_parts":
            refs = [source("parts", row["id"])]
            for s in rows(db, "SELECT id,supplier_id FROM sourcing WHERE part_id=? AND active=1 ORDER BY id", (row["id"],)):
                refs.extend([source("sourcing", s["id"]), source("suppliers", s["supplier_id"])])
        else:
            refs = order_sources(db, row["id"])
            if metric_id == "at_risk_orders":
                row["reason"] = "Past due" if row["due_date"] < AS_OF else "Late allocated supply"
            if metric_id == "revenue_at_risk":
                row["exposure"] = f"${row['at_risk_value_cents']/100:,.2f}"
        row["sources"] = unique_sources(refs)
    if metric_id == "supplier_reliability":
        denominator = sum(r["due_shipments"] for r in result)
        numerator = sum(r["on_time_shipments"] for r in result)
        value = round(100 * numerator / denominator, 1) if denominator else None
        summary = f"{numerator} of {denominator} due shipments arrived on time."
    elif metric_id == "order_fill_rate":
        denominator = sum(r["ordered_units"] for r in result)
        numerator = sum(r["fulfilled_units"] for r in result)
        value = round(100 * numerator / denominator, 1) if denominator else None
        summary = f"{numerator:,} of {denominator:,} ordered units have been fulfilled."
    elif metric_id == "revenue_at_risk":
        value = sum(r["at_risk_value_cents"] for r in result)
        summary = f"${value/100:,.2f} in gross open-order exposure across {len(result)} at-risk orders."
    else:
        value = len(result)
        summary = {
            "late_shipments": f"{value} inbound shipments are overdue and still unreceived.",
            "plant_shortages": f"{value} part-plant positions are below safety stock "
                               f"by {sum(r.get('shortage_units', 0) for r in result)} units in total.",
            "at_risk_orders": f"{value} customer orders have unfulfilled lines with a documented risk trigger.",
            "single_source_parts": f"{value} parts depend on exactly one active approved supplier.",
        }[metric_id]
    display = ("Not available" if value is None else
               f"${value/100:,.2f}" if item["unit"] == "USD" else
               f"{value:.1f}%" if item["unit"] == "%" else str(value))
    citations = unique_sources([source("snapshot", "SC-20261004")] +
                              [s for row in result for s in row["sources"]])
    return {
        "status": "answered", "metric_id": metric_id, "question": item["question"],
        "title": item["title"], "as_of": AS_OF, "summary": summary,
        "metric": {"value": value, "display": display, "unit": item["unit"],
                   "storage_unit": "USD cents" if item["unit"] == "USD" else item["unit"]},
        "definition": item["definition"], "grain": item["grain"], "sql": item["sql"],
        "columns": item["columns"], "rows": result, "citations": citations,
        "policy": {"role": role, "role_label": ROLES[role], "decision": "allowed",
                   "method": "Exact approved question/alias -> fixed read-only SQL",
                   "classification": "Synthetic commercial" if role == "commercial" else "Synthetic operations"},
    }


def get_record(db, table, key, role):
    if table not in TABLES or not isinstance(key, str) or len(key) > 80:
        raise QueryError("Source record not found.", 404, "not_found")
    records = rows(db, f"SELECT * FROM {table} WHERE id=?", (key,))
    if not records:
        raise QueryError("Source record not found.", 404, "not_found")
    record = records[0]
    redacted = []
    if role != "commercial":
        for field in MONETARY_FIELDS:
            if field in record:
                record.pop(field)
                redacted.append(field)
    linked = []
    for child, column, parent in RELATIONS:
        if child == table and record.get(column):
            linked.append(source(parent, record[column]))
        if parent == table:
            linked.extend(source(child, r["id"]) for r in
                          rows(db, f"SELECT id FROM {child} WHERE {column}=? ORDER BY id", (key,)))
    return {"source": source(table, key), "record": record, "redacted_fields": redacted,
            "related": unique_sources(linked), "as_of": AS_OF, "synthetic": True}


def overview(db, role):
    metrics = [answer(db, key, role) for key in
               ["late_shipments", "at_risk_orders", "order_fill_rate", "single_source_parts"]]
    supplier = answer(db, "supplier_reliability", role)
    shortages = answer(db, "plant_shortages", role)
    return {
        "as_of": AS_OF, "role": role, "role_label": ROLES[role], "synthetic": True,
        "kpis": [{"id": m["metric_id"], "title": m["title"], "metric": m["metric"],
                  "summary": m["summary"], "sources": len(m["citations"])} for m in metrics],
        "suppliers": supplier["rows"], "on_time": supplier["metric"]["display"],
        "shortages": shortages["rows"],
        "counts": {table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                   for table in ["suppliers", "parts", "plants", "shipments", "orders", "customers"]},
        "catalog": catalog(role),
    }


def ontology(db):
    entities = {table: rows(db, f"SELECT * FROM {table} ORDER BY id")
                for table in ["suppliers", "parts", "plants", "shipments", "orders", "customers"]}
    # The graph contains source identifiers and actual relationship rows, never prices.
    nodes = [{"id": r["id"], "table": table, "name": r.get("name", r["id"])}
             for table, records in entities.items() for r in records]
    edges = []
    for s in rows(db, "SELECT * FROM sourcing WHERE active=1"):
        edges.append({"from": s["supplier_id"], "to": s["part_id"], "via": s["id"], "table": "sourcing"})
    for i in rows(db, "SELECT * FROM inventory"):
        edges.append({"from": i["part_id"], "to": i["plant_id"], "via": i["id"], "table": "inventory"})
    for s in entities["shipments"]:
        edges.append({"from": s["plant_id"], "to": s["id"], "via": s["id"], "table": "shipments"})
    for a in rows(db, """SELECT a.id,a.shipment_id,l.order_id FROM allocations a
                         JOIN order_lines l ON l.id=a.order_line_id"""):
        edges.append({"from": a["shipment_id"], "to": a["order_id"], "via": a["id"], "table": "allocations"})
    for o in entities["orders"]:
        edges.append({"from": o["id"], "to": o["customer_id"], "via": o["id"], "table": "orders"})
    return {"nodes": nodes, "edges": edges, "as_of": AS_OF,
            "path": ["suppliers", "parts", "plants", "shipments", "orders", "customers"]}
