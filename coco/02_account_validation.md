# Account Validation Prompt

Account access is now owner-approved; this is not permission to spend or deploy.
Use plan mode and request approval before each write or warehouse/AI invocation.
Never use bypass mode. Do not modify production objects or create a warehouse.

1. Read snowflake/01_setup.sql through 06_role_checks.sql, data/manifest.json,
   and docs/SNOWFLAKE.md. Inspect the configured account, active role, secondary
   roles and approved warehouse; do not print credentials.
2. Check syntax and privileges against this account's current Snowflake version.
   Confirm CREATE SEMANTIC VIEW support and applicable Cortex access. Review the
   plan with the owner before executing the deployment commands in docs/SNOWFLAKE.md.
3. After approved deployment, execute 05_validate.sql, inspect actual results,
   and capture query IDs. Check uniqueness and all source foreign keys because
   standard Snowflake PK/FK declarations are informational.
4. With explicit administrator approval, use isolated demo roles and secondary
   roles NONE to run 06_role_checks.sql interactively. Verify denied access,
   not merely absent UI buttons. Stop if any supposedly denied statement works.
5. Validate Cortex Analyst with the supplied request body under the operations
   role. Inspect returned SQL before execution. Compare results and source IDs
   to the deterministic contract; do not execute arbitrary generated SQL.
6. Save sanitized real commands, query IDs, outputs and remaining gaps to
   artifacts/coco/account-validation.md. Never fabricate a receipt. Keep
   submission status as draft; do not publish or submit.
