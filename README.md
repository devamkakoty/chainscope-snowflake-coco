# ChainScope

**Supply chain answers you can trace to the source.**

Hackathon MVP for **Problem Statement 05: Supply Chain Ontology and Governed
Conversational Analytics**, Snowflake CoCo CLI Hackathon GCC Edition.
Owner-provided deadline: **October 4, 2026, 23:59 IST**.

ChainScope connects Supplier -> Part -> Plant -> Shipment -> Order -> Customer.
Seven deterministic business questions return inspectable source records,
explicit metric definitions and approved SQL. It includes a polished local web
app, CLI, public static replay, and genuine Snowflake deployment assets.

**Truthful status:** the local product runs without credentials, packages or
network services. Snowflake/Cortex Analyst deployment and CoCo CLI execution
have **not** been performed. The local copilot is an approved-query engine,
not an LLM. All companies, relationships and amounts are synthetic.

## Run Locally

Python **3.10+**, standard library only; validated here with Python 3.13.3.

```powershell
cd D:\MoneyMaker\services\snowflake-supply-chain-copilot
python -B app.py serve --port 8766
```

Open `http://127.0.0.1:8766`. If the port is occupied, choose another.
The app generates its database automatically if absent. Stop with Ctrl+C.
It binds only to loopback. No package installation or account is needed.

```powershell
python -B scripts/generate_data.py
python -B -m unittest discover -s tests -v
python -B app.py catalog
python -B app.py ask "Which customer orders are at risk?"
python -B app.py ask "What revenue is at risk?" --role commercial
```

The generator writes directly under `data/`, with source CSVs, a read-only app
database, Snowflake load SQL and a checksum manifest. Do not regenerate while
another process holds the database open. Snapshot: **2026-10-04**, 163 records,
11 tables. Money is integer USD cents.

## Demo Script

1. **Overview:** 5 late inbound shipments, 4 at-risk orders, 41.6% unit fill.
2. **Ask copilot:** choose customer orders at risk. Expand source records and
   inspect `ORD-013`, `LIN-025`, `ALC-025`, and `SHP-025`.
3. **Supply network:** trace `ORD-013` from Atlas Components through the control
   module and Jebel Ali to the customer. The order is not yet due; the risk comes
   from an explicitly allocated overdue inbound shipment.
4. Ask revenue exposure as **Operations analyst**: denied. Switch the simulated
   identity to **Commercial analyst**: **$67,050.00** gross open-order exposure.
5. Ask an unsupported prediction: refused. Inspect the **Audit trail**.

The demo role picker is deliberately not authentication. Server-side field
redaction and pre-query permissions demonstrate the policy boundary; production
identity must come from trusted authentication. The static replay is entirely
public and has **no** authorization boundary.

## Seven Metric Contracts

| Question | Expected snapshot result | Grain |
|---|---:|---|
| Which shipments are late? | 5 | Unreceived, promised before snapshot |
| Which suppliers have the lowest on-time delivery? | 55.2% network-wide; 16/29 | Due shipments, including open overdue |
| Which plants are below safety stock? | 5 positions; 120 units | Part + plant |
| Which customer orders are at risk? | 4 | Distinct order with at-risk outstanding line |
| Which parts have single-source exposure? | 3 | Distinct active supplier per part |
| What is our order fill rate? | 41.6%; 640/1,540 units | Unit-weighted across order lines |
| What revenue is at risk? | $67,050.00; commercial only | Outstanding value on at-risk lines |

Due today is not overdue. Fulfilled lines never create order risk. Distinct
late-allocation flags prevent many-to-many fanout. Exposure is neither
recognized revenue nor a prediction of financial loss.

## Architecture

```text
Synthetic generator -> CSV + manifest + SQLite + Snowflake load SQL
                                      |
Web UI / CLI -> question allowlist -> role check -> shared SQL views
                                      |                |
                                audit decision     results + source IDs

Same source data + views -> Snowflake native Semantic Views
                         -> object grants -> Cortex Analyst [account required]
Generated docs/ replay -> static hosting, no backend [all data public]
```

`chainscope/metrics.py` owns questions, grain, field policy and citations.
`snowflake/02_views.sql` is the shared SQL contract, executed locally with only
the `CREATE OR REPLACE VIEW` prefix adapted for SQLite.
`snowflake/03_semantic_views.sql` is the **current native Semantic View equivalent
of a Cortex Analyst semantic YAML model**, with relationships, dimensions,
private facts, metrics and AI instructions. See [architecture](docs/ARCHITECTURE.md).

## Snowflake and CoCo

The complete, approval-gated sequence is in [docs/SNOWFLAKE.md](docs/SNOWFLAKE.md).
It includes setup, idempotent synthetic load, native semantic models, least-
privilege roles, positive/negative checks and an Analyst request body.
CoCo prompt files are in `coco/`; the executable is `cortex`, not `coco`.

```powershell
cortex -c chainscope -w D:\MoneyMaker\services\snowflake-supply-chain-copilot --plan
```

Then ask CoCo to review `@coco/01_local_review.md` before any account actions.
Do not claim CoCo usage until it actually runs and produces retained evidence.
No warehouse creation, installation, publishing or account creation is automated.

## GitHub Pages and Screenshots

**Ready-to-host static demo:** `docs/index.html`, with all assets beneath
`docs/static/`. Use the repository's `/docs` folder as the Pages source after
owner-authorized publication. Nothing has been uploaded or published.

```powershell
python -B scripts/build_static.py
python -B -m http.server 8767 --bind 127.0.0.1 --directory docs
```

Open `http://127.0.0.1:8767`. This is a public replay of precomputed results, not
live SQL, Snowflake, authentication or private data.

Screenshots are in `artifacts/screenshots/`. To reproduce manually, use a
1440 x 1000 desktop and 390 x 844 mobile viewport; capture Overview, an answered
question with sources, Network and Audit. Optional automated capture uses
**already installed** Playwright and Chrome, never installs them:

```powershell
python -B scripts/capture_demo.py --url http://127.0.0.1:8766
```

## Limits and Submission

- Fixed snapshot, one currency, no BOM conversion, transit forecasting or live ERP.
- Exact approved questions/aliases, not unrestricted natural-language reasoning.
- In-memory last-100 audit decisions per session; hashes are not durable external
  attestation. Restarting the server clears sessions. CLI queries have no audit.
- Local host/Origin checks and CSP reduce exposure; the standard-library server
  is a local demonstration, not production hosting.
- Snowflake SQL uses official syntax but still requires account-side compilation,
  metric reconciliation and negative role checks. Tests do not substitute for that.
- Static fixtures reveal **all** synthetic commercial values regardless of UI role.

**Pitch:** "A late shipment is not yet an explanation. ChainScope connects it to
the exact customer commitment, shows the approved calculation, and lets the right
person inspect every source. The same metric contract has a Snowflake deployment
path without making a hackathon demo depend on account access."

Submission copy: [SUBMISSION.md](SUBMISSION.md).
Verification: [artifacts/VERIFICATION.md](artifacts/VERIFICATION.md).
Hackathon deck: [artifacts/ChainScope-CoCo-Hackathon-Deck.pdf](artifacts/ChainScope-CoCo-Hackathon-Deck.pdf).
Narrated demo: see the `v1.0-hackathon` GitHub release.
Project code: MIT. Generated data: CC0-1.0. Lucide asset notices are retained.
