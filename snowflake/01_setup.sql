-- Run only in an owner-approved Snowflake account, with an existing warehouse.
-- Creates a dedicated demo database; does not create/resume a warehouse or grant
-- roles to users. No production databases are modified.
CREATE DATABASE IF NOT EXISTS CHAINSCOPE_DEMO;
CREATE SCHEMA IF NOT EXISTS CHAINSCOPE_DEMO.CORE;
USE DATABASE CHAINSCOPE_DEMO;
USE SCHEMA CORE;

CREATE TABLE IF NOT EXISTS snapshot (
  id VARCHAR PRIMARY KEY, as_of DATE NOT NULL, label VARCHAR NOT NULL
);
CREATE TABLE IF NOT EXISTS suppliers (
  id VARCHAR PRIMARY KEY, name VARCHAR NOT NULL, region VARCHAR NOT NULL
);
CREATE TABLE IF NOT EXISTS parts (
  id VARCHAR PRIMARY KEY, name VARCHAR NOT NULL, category VARCHAR NOT NULL
);
CREATE TABLE IF NOT EXISTS plants (
  id VARCHAR PRIMARY KEY, name VARCHAR NOT NULL, region VARCHAR NOT NULL
);
CREATE TABLE IF NOT EXISTS customers (
  id VARCHAR PRIMARY KEY, name VARCHAR NOT NULL, sector VARCHAR NOT NULL
);
CREATE TABLE IF NOT EXISTS sourcing (
  id VARCHAR PRIMARY KEY, supplier_id VARCHAR REFERENCES suppliers(id),
  part_id VARCHAR REFERENCES parts(id), active NUMBER(1,0) NOT NULL
);
CREATE TABLE IF NOT EXISTS inventory (
  id VARCHAR PRIMARY KEY, part_id VARCHAR REFERENCES parts(id),
  plant_id VARCHAR REFERENCES plants(id), on_hand NUMBER(18,0) NOT NULL,
  safety_stock NUMBER(18,0) NOT NULL, UNIQUE(part_id,plant_id)
);
CREATE TABLE IF NOT EXISTS shipments (
  id VARCHAR PRIMARY KEY, supplier_id VARCHAR REFERENCES suppliers(id),
  part_id VARCHAR REFERENCES parts(id), plant_id VARCHAR REFERENCES plants(id),
  promised_date DATE NOT NULL, received_date DATE, quantity NUMBER(18,0) NOT NULL
);
CREATE TABLE IF NOT EXISTS orders (
  id VARCHAR PRIMARY KEY, customer_id VARCHAR REFERENCES customers(id),
  plant_id VARCHAR REFERENCES plants(id), due_date DATE NOT NULL
);
CREATE TABLE IF NOT EXISTS order_lines (
  id VARCHAR PRIMARY KEY, order_id VARCHAR REFERENCES orders(id),
  part_id VARCHAR REFERENCES parts(id), quantity NUMBER(18,0) NOT NULL,
  fulfilled_quantity NUMBER(18,0) NOT NULL, unit_price_cents NUMBER(18,0) NOT NULL
);
CREATE TABLE IF NOT EXISTS allocations (
  id VARCHAR PRIMARY KEY, shipment_id VARCHAR REFERENCES shipments(id),
  order_line_id VARCHAR REFERENCES order_lines(id), quantity NUMBER(18,0) NOT NULL,
  UNIQUE(shipment_id,order_line_id)
);
