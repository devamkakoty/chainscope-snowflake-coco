-- Run as demo owner after loading and before granting access.
-- Every check should return PASS. Save actual query IDs separately.
USE DATABASE CHAINSCOPE_DEMO;
USE SCHEMA CORE;
SELECT 'snapshot_rows' AS check_name, IFF(COUNT(*)=1,'PASS','FAIL') AS result FROM snapshot
UNION ALL
SELECT 'late_shipments', IFF(SUM(is_open_late)=5,'PASS','FAIL') FROM v_shipments
UNION ALL
SELECT 'due_shipments', IFF(SUM(is_due)=29,'PASS','FAIL') FROM v_shipments
UNION ALL
SELECT 'on_time_shipments', IFF(SUM(is_on_time)=16,'PASS','FAIL') FROM v_shipments
UNION ALL
SELECT 'on_time_pct', IFF(ROUND(100.0*SUM(is_on_time)/NULLIF(SUM(is_due),0),1)=55.2,'PASS','FAIL') FROM v_shipments
UNION ALL
SELECT 'at_risk_orders', IFF(SUM(is_at_risk)=4,'PASS','FAIL') FROM v_orders
UNION ALL
SELECT 'fill_pct', IFF(ROUND(100.0*SUM(fulfilled_units)/NULLIF(SUM(ordered_units),0),1)=41.6,'PASS','FAIL') FROM v_orders
UNION ALL
SELECT 'single_source', IFF(COUNT(*)=3,'PASS','FAIL') FROM v_part_sources WHERE active_supplier_count=1
UNION ALL
SELECT 'shortage_positions', IFF(COUNT(*)=5,'PASS','FAIL') FROM v_inventory WHERE shortage_units>0
UNION ALL
SELECT 'exposure_cents', IFF(SUM(at_risk_value_cents)=6705000,'PASS','FAIL') FROM v_orders;

-- Must return zero rows. Standard-table PK/FK constraints are not enforcement.
SELECT a.id AS invalid_allocation FROM allocations a
LEFT JOIN shipments s ON s.id=a.shipment_id
LEFT JOIN order_lines l ON l.id=a.order_line_id
LEFT JOIN orders o ON o.id=l.order_id
WHERE s.id IS NULL OR l.id IS NULL OR o.id IS NULL
   OR s.part_id<>l.part_id OR s.plant_id<>o.plant_id;
SELECT id FROM order_lines WHERE quantity<=0 OR fulfilled_quantity<0
  OR fulfilled_quantity>quantity OR unit_price_cents<0;
SELECT shipment_id FROM allocations GROUP BY shipment_id
HAVING SUM(quantity) > (SELECT quantity FROM shipments WHERE id=shipment_id);

-- Semantic execution tests: compare with the scalar expectations above.
SELECT * FROM SEMANTIC_VIEW(CHAINSCOPE_OPERATIONS METRICS shipments.late_shipments);
SELECT * FROM SEMANTIC_VIEW(CHAINSCOPE_OPERATIONS METRICS shipments.on_time_pct);
SELECT * FROM SEMANTIC_VIEW(CHAINSCOPE_OPERATIONS METRICS orders.at_risk_orders);
SELECT * FROM SEMANTIC_VIEW(CHAINSCOPE_OPERATIONS METRICS orders.order_fill_pct);
SELECT * FROM SEMANTIC_VIEW(CHAINSCOPE_OPERATIONS METRICS parts.single_source_parts);
SELECT * FROM SEMANTIC_VIEW(CHAINSCOPE_OPERATIONS METRICS inventory.shortage_positions);
SELECT * FROM SEMANTIC_VIEW(CHAINSCOPE_COMMERCIAL METRICS orders.revenue_at_risk_usd);

-- Evidence queries preserve row IDs. Supplier breakdown should reconcile to 16/29.
SELECT * FROM SEMANTIC_VIEW(CHAINSCOPE_OPERATIONS
  DIMENSIONS suppliers.supplier_id, suppliers.supplier_name
  METRICS shipments.due_shipments, shipments.on_time_shipments, shipments.on_time_pct);
SELECT id, customer_id, at_risk_value_cents FROM v_orders WHERE is_at_risk=1 ORDER BY id;
