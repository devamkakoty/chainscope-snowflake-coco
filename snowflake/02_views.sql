-- Shared deterministic metric contract. Local SQLite executes this same file,
-- changing only CREATE OR REPLACE VIEW to CREATE VIEW.
-- All comparisons are against the source snapshot, never the wall clock.

CREATE OR REPLACE VIEW v_shipments AS
SELECT s.*,
       CASE WHEN s.promised_date < x.as_of AND s.received_date IS NULL
            THEN 1 ELSE 0 END AS is_open_late,
       CASE WHEN s.promised_date < x.as_of THEN 1 ELSE 0 END AS is_due,
       CASE WHEN s.promised_date < x.as_of AND s.received_date IS NOT NULL
                 AND s.received_date <= s.promised_date
            THEN 1 ELSE 0 END AS is_on_time
FROM shipments s CROSS JOIN snapshot x
WHERE x.id = 'SC-20261004';

CREATE OR REPLACE VIEW v_inventory AS
SELECT i.*,
       CASE WHEN i.on_hand < i.safety_stock THEN i.safety_stock-i.on_hand ELSE 0 END
         AS shortage_units
FROM inventory i;

CREATE OR REPLACE VIEW v_part_sources AS
SELECT p.id AS part_id, p.name AS part_name, p.category,
       COUNT(DISTINCT CASE WHEN s.active = 1 THEN s.supplier_id ELSE NULL END)
         AS active_supplier_count
FROM parts p LEFT JOIN sourcing s ON s.part_id = p.id
GROUP BY p.id, p.name, p.category;

-- Deduplicate the allocation bridge before the line join. This is portable to
-- Snowflake, which restricts correlated EXISTS in CASE expressions.
CREATE OR REPLACE VIEW v_late_allocations AS
SELECT DISTINCT a.order_line_id
FROM allocations a JOIN v_shipments s ON s.id=a.shipment_id
WHERE a.quantity>0 AND s.is_open_late=1;

-- A single allocation flag avoids multiplying line amounts through the bridge.
-- Completed lines cannot be at risk, even when an old shipment was late.
CREATE OR REPLACE VIEW v_order_lines AS
SELECT l.*, o.customer_id, o.plant_id, o.due_date,
       l.quantity-l.fulfilled_quantity AS outstanding_units,
       (l.quantity-l.fulfilled_quantity)*l.unit_price_cents AS outstanding_value_cents,
       CASE WHEN l.quantity > l.fulfilled_quantity AND
         (o.due_date < x.as_of OR a.order_line_id IS NOT NULL)
         THEN 1 ELSE 0 END AS is_at_risk
FROM order_lines l
JOIN orders o ON o.id = l.order_id
LEFT JOIN v_late_allocations a ON a.order_line_id=l.id
CROSS JOIN snapshot x WHERE x.id = 'SC-20261004';

CREATE OR REPLACE VIEW v_orders AS
SELECT o.id, o.customer_id, o.plant_id, o.due_date,
       COALESCE(SUM(l.quantity),0) AS ordered_units,
       COALESCE(SUM(l.fulfilled_quantity),0) AS fulfilled_units,
       COALESCE(SUM(l.outstanding_units),0) AS outstanding_units,
       COALESCE(MAX(l.is_at_risk),0) AS is_at_risk,
       COALESCE(SUM(CASE WHEN l.is_at_risk = 1 THEN l.outstanding_value_cents ELSE 0 END),0)
         AS at_risk_value_cents
FROM orders o LEFT JOIN v_order_lines l ON l.order_id = o.id
GROUP BY o.id, o.customer_id, o.plant_id, o.due_date;

-- The operations projection deliberately contains no monetary columns.
CREATE OR REPLACE VIEW v_orders_ops AS
SELECT id, customer_id, plant_id, due_date, ordered_units, fulfilled_units,
       outstanding_units, is_at_risk FROM v_orders;

CREATE OR REPLACE VIEW v_order_lines_ops AS
SELECT id, order_id, part_id, quantity, fulfilled_quantity, customer_id, plant_id,
       due_date, outstanding_units, is_at_risk FROM v_order_lines;
