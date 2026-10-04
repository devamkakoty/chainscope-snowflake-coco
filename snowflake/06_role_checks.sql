-- Run interactively only AFTER an administrator assigns the demo roles to the
-- test user and grants warehouse USAGE. Expected failures are deliberate.
-- Disable secondary roles so inherited privileged sessions do not invalidate tests.
USE SECONDARY ROLES NONE;
USE ROLE CHAINSCOPE_OPS;
USE DATABASE CHAINSCOPE_DEMO;
USE SCHEMA CORE;
SELECT * FROM SEMANTIC_VIEW(CHAINSCOPE_OPERATIONS METRICS orders.at_risk_orders); -- 4
SELECT id, quantity, fulfilled_quantity FROM v_order_lines_ops LIMIT 2; -- allowed
SELECT unit_price_cents FROM order_lines LIMIT 1; -- EXPECT authorization failure
SELECT at_risk_value_cents FROM v_orders LIMIT 1; -- EXPECT authorization failure
SELECT * FROM SEMANTIC_VIEW(CHAINSCOPE_COMMERCIAL
  METRICS orders.revenue_at_risk_usd); -- EXPECT authorization failure
USE ROLE CHAINSCOPE_COMMERCIAL;
SELECT * FROM SEMANTIC_VIEW(CHAINSCOPE_COMMERCIAL
  METRICS orders.revenue_at_risk_usd); -- 67050.00
