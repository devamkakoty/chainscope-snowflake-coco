# Architecture and Governance

## Entity and Relationship Model

| Entity | Source key | Relationship evidence |
|---|---|---|
| Supplier | `suppliers.id` | `sourcing` approves supplier + part |
| Part | `parts.id` | `inventory` connects part + plant |
| Plant | `plants.id` | `shipments.plant_id` is the inbound destination |
| Shipment | `shipments.id` | `allocations` explicitly associates supply with an order line |
| Order | `orders.id` | `order_lines` identifies part demand; `customer_id` identifies customer |
| Customer | `customers.id` | Customer-specific order commitments |

This is an inbound supply and demand-allocation model, not a transport route:
the displayed Plant -> Shipment edge means "receives at", not "ships from".
Parts are treated as fulfillable items with one-to-one units. No implicit bill
of materials, substitutions or manufacturing yields are assumed.

The generated network has 69 main entity nodes and 111 relationship edges.
The 163 source rows include inventory, sourcing, order lines, allocations and a
snapshot record. Source keys are stable and source payloads remain inspectable.

## Query Path

1. Exact normalization of a question or explicit alias selects one approved metric.
2. The server derives the simulated role from its session, not the query payload.
3. Permissions are checked **before** executing fixed SQL against read-only SQLite.
4. Results carry explicit row grain and evidence from real fixture records.
5. Source endpoints allow only approved tables and parameterize the source key.
6. Commercial fields are removed from operations source records.
7. Browser query outcomes append SHA-256-linked decision records, including
   denials and unsupported prompts. Raw rejected questions are not retained.

Counts and financial aggregates are computed before allocation joins; the
order-risk predicate joins distinct late-allocation flags. Independent tests add duplicate allocations
to ensure exposure does not multiply. Other tests cover due-today boundaries,
fulfilled orders, inactive sourcing, zero denominators and empty datasets.

## Shared Snowflake Contract

`02_views.sql` is used by both SQLite and Snowflake. Local adaptation only changes
the DDL prefix; business expressions are shared. `03_semantic_views.sql` defines
native operations and commercial semantic models separately. Reference grants
expose nonfinancial source tables and safe projections to operations, never raw
`order_lines`, financial `v_orders`, or the commercial semantic view.

Snowflake standard-table key constraints are informational. Account validation
must inspect uniqueness and referential integrity, not assume DDL enforces them.
Secondary roles must be disabled during negative permission tests. Existing
privileged or custom role inheritance must be reviewed by an administrator.

The supplied Cortex Analyst request demonstrates the supported semantic-view
API request format. No generated SQL is auto-executed locally. A future production
adapter must validate the requested object/metric, inspect generated SQL, apply
the user's actual Snowflake role, enforce result limits, and retain query IDs.

## Trust Boundaries

**Local:** anyone at the keyboard may choose either demo identity. This is
explicitly a policy demonstration, not enterprise authentication. The server
binds to loopback, rejects foreign Host/Origin headers, allows only static
whitelisted paths, caps JSON bodies, applies CSP, and makes the source DB read-only.

**Static replay:** all fixture values are public. Selection of a role changes the
illustration, not data access. No server, Snowflake connection, durable audit or
secret storage exists. Exported answers identify themselves as static replay.

**Snowflake:** object grants are the proposed authorization boundary. Prompt
instructions are guidance, never a security control. All account-side claims
remain unverified until commands run against an approved account.

**Audit:** last 100 decisions per browser session, memory only. SHA-256 links help
inspect continuity but are not signed, immutable, tamper-proof or durable.

## Reproduction and Storage

Run `scripts/generate_data.py` to generate the database, CSVs, load SQL and
manifest directly on disk. Scenario generation is seeded and deterministic;
retrieval timestamps in manifests naturally vary. `scripts/build_static.py`
derives the public replay from that database. No bulk artifact is embedded in
source patches. Screenshots are produced by the optional browser capture tool.
