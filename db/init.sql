-- =============================================================================
-- Databridge — Database Initialization
-- =============================================================================
-- This file runs automatically when Postgres starts on a fresh volume.
-- We use three separate schemas to simulate three distinct source systems.
-- In a real ETL/integration project, each schema would represent data landing
-- from a different upstream system (CRM, ERP, WMS, etc.).
--
-- Postgres schemas are namespaces within a single database — think of them
-- like folders. You access tables as schema.table (e.g. sales.orders).
-- This is different from MySQL where "schema" and "database" mean the same thing.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Source System 1: Customer Management System (CRM)
-- -----------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS customers;

CREATE TABLE customers.customers (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(255)        NOT NULL,
    email       VARCHAR(255) UNIQUE NOT NULL,
    region      VARCHAR(50)         NOT NULL,  -- Northeast, Southeast, Midwest, West
    created_at  TIMESTAMPTZ         NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- Source System 2: Sales / Order Management System
-- -----------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS sales;

CREATE TABLE sales.orders (
    id           SERIAL PRIMARY KEY,
    customer_id  INT             NOT NULL REFERENCES customers.customers(id),
    product_id   INT             NOT NULL,  -- FK to inventory.products (added below)
    quantity     INT             NOT NULL CHECK (quantity > 0),
    unit_price   NUMERIC(10, 2)  NOT NULL CHECK (unit_price >= 0),
    ordered_at   TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- Source System 3: Warehouse / Inventory Management System (WMS)
-- -----------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS inventory;

CREATE TABLE inventory.products (
    id             SERIAL PRIMARY KEY,
    sku            VARCHAR(50)   UNIQUE NOT NULL,
    name           VARCHAR(255)  NOT NULL,
    category       VARCHAR(100)  NOT NULL,  -- Electronics, Office, Supplies
    stock_qty      INT           NOT NULL DEFAULT 0 CHECK (stock_qty >= 0),
    reorder_level  INT           NOT NULL DEFAULT 10,
    updated_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- Now that inventory.products exists, add the FK from sales.orders
ALTER TABLE sales.orders
    ADD CONSTRAINT fk_orders_product
    FOREIGN KEY (product_id) REFERENCES inventory.products(id);

-- -----------------------------------------------------------------------------
-- Source System 4: Auth / Identity
-- -----------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS auth;

CREATE TYPE auth.user_role AS ENUM ('admin', 'viewer');

CREATE TABLE auth.users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255)      NOT NULL,
    role          auth.user_role      NOT NULL DEFAULT 'viewer',
    is_active     BOOLEAN             NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ         NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- Indexes for common query patterns (filtering by region, date range, category)
-- -----------------------------------------------------------------------------
CREATE INDEX idx_customers_region   ON customers.customers(region);
CREATE INDEX idx_orders_customer    ON sales.orders(customer_id);
CREATE INDEX idx_orders_product     ON sales.orders(product_id);
CREATE INDEX idx_orders_ordered_at  ON sales.orders(ordered_at);
CREATE INDEX idx_products_category  ON inventory.products(category);
