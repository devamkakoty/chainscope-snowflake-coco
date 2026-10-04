# Local Review Prompt

You are reviewing ChainScope for problem statement 05, Supply Chain Ontology and
Governed Conversational Analytics. Work only in this project directory.

This project uses entirely synthetic data. The local app is deterministic, not
an LLM or a live Snowflake connection. Do not invent deployment or CoCo evidence.
Do not install anything, connect to an account, create users, incur spending,
publish, submit, or edit files without explicit approval.

Read README.md, chainscope/metrics.py, snowflake/02_views.sql, and
snowflake/03_semantic_views.sql. Review the supplier -> part -> plant -> shipment
-> order -> customer ontology, including the sourcing, inventory, line and
allocation bridges. Check for join fanout, mixed metric grains, due-today boundary
errors, ungrounded causal claims and financial-field leaks. Propose changes only.

With approval, run:
- python -B -m unittest discover -s tests -v
- python -B app.py ask "Which customer orders are at risk?"
- python -B app.py ask "What revenue is at risk?" --role commercial

Record the actual CoCo CLI version, command, test totals and observations in a
new small Markdown file under artifacts/coco/. Do not call expected results
observed results. Stop for approval before any account-side action.
