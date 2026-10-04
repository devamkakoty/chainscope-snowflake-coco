# Snowflake and CoCo Deployment Runbook

**Not yet executed.** Local test success is not a Snowflake deployment receipt.
All account actions require the owner's account, permission and cost approval.
No installer, account creation, warehouse creation or automatic AI call is run
by this project.

## Prerequisites

- An approved Snowflake account with a supported Cortex/CoCo configuration.
- A role allowed to create the dedicated `CHAINSCOPE_DEMO` database/schema,
  tables, views and native semantic views, plus SELECT on their underlying objects.
- An existing approved warehouse and its usage grant. Queries/AI may incur costs.
- Administrator review of role grants and Cortex database roles.
- Snowflake CLI (`snow`) and CoCo CLI (`cortex`) already installed by the owner.
  The local app itself requires neither.

Current CoCo documentation distinguishes dedicated CoCo trial access from
ordinary Snowflake trials. Do not assume any standard trial account supports it.

## Connection Configuration

Use the owner's existing named Snowflake connection. If configuration is needed,
the owner should configure `~/.snowflake/connections.toml` outside the repository.
Do not commit or copy credentials into this project.

```toml
[chainscope]
account = "<approved account identifier>"
user = "<approved user>"
authenticator = "externalbrowser"
role = "<approved deployment role>"
warehouse = "<existing approved warehouse>"
database = "CHAINSCOPE_DEMO"
schema = "CORE"
```

The database/schema may not exist before setup; use an existing context for the
first connection test if required. Authentication remains interactive.

```powershell
snow --version
cortex --version
snow connection test -c chainscope
```

## Deployment Sequence

Review every script first. All objects are isolated in `CHAINSCOPE_DEMO.CORE`.
`01_setup.sql` does not replace existing tables. Load SQL skips existing IDs;
it is not an update/migration mechanism. Never run a second load concurrently.

```powershell
python -B scripts/generate_data.py
snow sql -c chainscope -f snowflake/01_setup.sql
snow sql -c chainscope -f data/snowflake_seed.sql
snow sql -c chainscope --database CHAINSCOPE_DEMO --schema CORE -f snowflake/02_views.sql
snow sql -c chainscope -f snowflake/03_semantic_views.sql
snow sql -c chainscope -f snowflake/05_validate.sql
```

The native `CREATE SEMANTIC VIEW` statements are the current official equivalent
of the requested Cortex Analyst semantic YAML. Operations and commercial are
separate semantic views. Account compilation and query execution must still be
verified. Do not replace a failed deployment with a claim that it succeeded.

An authorized administrator can then review and run `04_grants.sql`. It creates
two dedicated roles and does **not** assign them to users. The administrator must
separately grant approved warehouse access and necessary Cortex database roles.
Do not grant raw financial tables to the operations role.

Run `06_role_checks.sql` **interactively**, not as one success-only batch: three
authorization failures are expected. Use `USE SECONDARY ROLES NONE`. Capture the
actual SQLSTATE/query IDs and confirm commercial access succeeds. Audit inherited
roles and grants before treating this as a valid isolation test.

## CoCo CLI Workflow

CoCo CLI's executable is **`cortex`**. Start in plan mode; do not use bypass flags.

```powershell
cortex -c chainscope -w D:\MoneyMaker\services\snowflake-supply-chain-copilot --plan
```

Paste these prompts in order:

```text
Read @coco/01_local_review.md and propose the review plan. Do not make account changes.
```

After local review and explicit account approval:

```text
Read @coco/02_account_validation.md. Inspect the deployment plan and ask for approval
before each write or chargeable query. Capture actual evidence, not expected results.
```

After actual validation:

```text
Read @coco/03_demo_review.md. Review the pitch against the actual evidence and
remaining gaps. Do not publish or submit.
```

Save sanitized version, prompts, commands, timestamps, query IDs and results
under `artifacts/coco/`. Never save tokens, connection secrets or authentication
cookies. An empty evidence directory means CoCo execution remains unperformed.

## Cortex Analyst Request

Endpoint: `POST https://<account-host>/api/v2/cortex/analyst/message`

Request body: `snowflake/analyst-request.operations.json`.
Use the currently supported, owner-approved Snowflake authentication method and
an operations-role session. Do not hardcode tokens. The body names the semantic
view and requests source order IDs.

Cortex Analyst may return suggestions, text or SQL; it does not itself provide
the local app's citation contract. Review SQL before executing with the same
authorized role. Resolve returned IDs to authorized source views; reconcile
metric values with `05_validate.sql`. Do not blindly execute generated SQL.

## Acceptance Evidence

- Actual successful DDL and source row counts; no duplicate primary IDs or orphan keys.
- Seven scalar metric results matching the local snapshot.
- Supplier breakdown reconciles to 16 on-time / 29 due shipments.
- Evidence IDs for at-risk orders and their explicit allocations.
- Operations financial access fails; commercial exposure is USD 67,050.00.
- Actual Analyst/CoCo responses, query IDs and known gaps recorded separately.

## Official References

Documentation retrieved on **October 4, 2026**; verify against the target account.

- [CREATE SEMANTIC VIEW](https://docs.snowflake.com/en/sql-reference/sql/create-semantic-view)
- [Semantic View YAML specification](https://docs.snowflake.com/en/user-guide/views-semantic/semantic-view-yaml-spec)
- [Querying semantic views and privileges](https://docs.snowflake.com/en/user-guide/views-semantic/querying)
- [Creating semantic views and prerequisites](https://docs.snowflake.com/en/user-guide/views-semantic/sql)
- [Cortex Analyst REST API](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/rest-api)
- [CoCo CLI setup](https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code-cli)
- [CoCo CLI options and plan mode](https://docs.snowflake.com/en/user-guide/cortex-code/cli-reference)
