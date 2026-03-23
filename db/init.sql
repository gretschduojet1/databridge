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
-- Worker / Job tracking (Celery task status)
-- -----------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS workers;

CREATE TABLE workers.jobs (
    id          VARCHAR(36)  PRIMARY KEY,  -- UUID
    name        VARCHAR(255) NOT NULL,
    status      VARCHAR(20)  NOT NULL DEFAULT 'pending',  -- pending/running/success/failed
    payload     JSONB,
    result      JSONB,
    error       TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- Raw landing zone — unnormalized data from upstream source systems
-- -----------------------------------------------------------------------------
-- Each table here represents a CSV/API dump as it arrives from an external
-- system before any cleansing or normalization. Column names, types, and
-- values intentionally differ from the target schemas to show the ETL work
-- that Airflow DAGs perform.
-- -----------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS raw;

-- Raw CRM export — customer data as delivered by the CRM team
-- Territory uses short codes (NE/SE/MW/W) instead of the full region names
-- we store in customers.customers. Extra columns (phone, account_tier) are
-- not part of our data model and get dropped during ingestion.
CREATE TABLE raw.crm_customers (
    id            SERIAL PRIMARY KEY,
    full_name     VARCHAR(255) NOT NULL,
    email_address VARCHAR(255) NOT NULL,
    territory     VARCHAR(10)  NOT NULL,       -- 'NE', 'SE', 'MW', 'W'
    join_date     TEXT         NOT NULL,       -- ISO text, e.g. '2023-04-12T09:15:00'
    phone         VARCHAR(30),                 -- not in target schema
    account_tier  VARCHAR(20),                 -- Bronze/Silver/Gold — not in target schema
    ingested_at   TIMESTAMPTZ                  -- NULL until Airflow loads this row
);

-- Raw WMS export — inventory data from the warehouse management system
-- Uses 'item_code' instead of 'sku', 'department' instead of 'category',
-- and includes cost/location columns that are WMS-specific and get discarded.
CREATE TABLE raw.wms_inventory (
    id                SERIAL PRIMARY KEY,
    item_code         VARCHAR(50)    NOT NULL,  -- maps to inventory.products.sku
    item_name         VARCHAR(255)   NOT NULL,  -- maps to inventory.products.name
    department        VARCHAR(100)   NOT NULL,  -- maps to inventory.products.category
    quantity_on_hand  INT            NOT NULL,  -- maps to inventory.products.stock_qty
    reorder_point     INT            NOT NULL,  -- maps to inventory.products.reorder_level
    cost_price        NUMERIC(10,2),            -- not in target schema
    warehouse_bin     VARCHAR(20),              -- not in target schema
    last_sync         TEXT,                     -- not used directly
    ingested_at       TIMESTAMPTZ               -- NULL until Airflow loads this row
);

-- Raw OMS export — order transactions as exported from the order management system
-- References customers and products by natural keys (email, item_code) rather
-- than the integer PKs we use internally. Airflow resolves these to real FKs.
CREATE TABLE raw.oms_transactions (
    id               SERIAL PRIMARY KEY,
    transaction_id   VARCHAR(50)    NOT NULL UNIQUE,  -- external dedup key
    customer_email   VARCHAR(255)   NOT NULL,         -- resolved to customers.customers.id
    item_code        VARCHAR(50)    NOT NULL,          -- resolved to inventory.products.id
    quantity_ordered INT            NOT NULL,          -- maps to sales.orders.quantity
    sale_price       NUMERIC(10,2)  NOT NULL,          -- maps to sales.orders.unit_price
    transaction_date TEXT           NOT NULL,          -- maps to sales.orders.ordered_at
    payment_method   VARCHAR(30),                     -- not in target schema
    source_channel   VARCHAR(30),                     -- not in target schema
    ingested_at      TIMESTAMPTZ                      -- NULL until Airflow loads this row
);

-- -----------------------------------------------------------------------------
-- Indexes for common query patterns (filtering by region, date range, category)
-- -----------------------------------------------------------------------------
CREATE INDEX idx_customers_region   ON customers.customers(region);
CREATE INDEX idx_orders_customer    ON sales.orders(customer_id);
CREATE INDEX idx_orders_product     ON sales.orders(product_id);
CREATE INDEX idx_orders_ordered_at  ON sales.orders(ordered_at);
CREATE INDEX idx_products_category  ON inventory.products(category);
CREATE INDEX idx_raw_crm_ingested   ON raw.crm_customers(ingested_at);
CREATE INDEX idx_raw_wms_ingested   ON raw.wms_inventory(ingested_at);
CREATE INDEX idx_raw_oms_ingested   ON raw.oms_transactions(ingested_at);
