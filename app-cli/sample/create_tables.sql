-- Create the governance metadata dataset
CREATE DATASET IF NOT EXISTS `@PROJECT_ID.governance_metadata`;

-- Create the metadata table
CREATE TABLE IF NOT EXISTS `@PROJECT_ID.governance_metadata.system_metadata` (
    target_dataset_name STRING,
    table_name STRING,
    column_name STRING,
    column_metadata STRING
);

-- Create the job runs table
CREATE TABLE IF NOT EXISTS `@PROJECT_ID.governance_metadata.job_runs` (
    job_run_id STRING,
    timestamp TIMESTAMP,
    status STRING,
    table_name STRING,
    column_name STRING,
    column_metadata STRING,
    target_dataset STRING
);

-- Create sample tables to update
CREATE DATASET IF NOT EXISTS `@PROJECT_ID.raw_data`;
CREATE DATASET IF NOT EXISTS `@PROJECT_ID.staging`;
CREATE DATASET IF NOT EXISTS `@PROJECT_ID.warehouse`;

-- Create raw_data tables
CREATE TABLE IF NOT EXISTS `@PROJECT_ID.raw_data.customers` (
    customer_id STRING,
    first_name STRING,
    last_name STRING,
    email STRING,
    phone STRING
);

CREATE TABLE IF NOT EXISTS `@PROJECT_ID.raw_data.orders` (
    order_id STRING,
    customer_id STRING,
    order_date DATE,
    total_amount NUMERIC
);

-- Create staging tables
CREATE TABLE IF NOT EXISTS `@PROJECT_ID.staging.customers` (
    customer_id STRING,
    full_name STRING,
    email STRING,
    phone STRING
);

CREATE TABLE IF NOT EXISTS `@PROJECT_ID.staging.orders` (
    order_id STRING,
    customer_id STRING,
    order_date DATE,
    total_amount NUMERIC
);

-- Create warehouse tables
CREATE TABLE IF NOT EXISTS `@PROJECT_ID.warehouse.dim_customers` (
    customer_key INT64,
    customer_id STRING,
    full_name STRING,
    email STRING,
    phone STRING
);

CREATE TABLE IF NOT EXISTS `@PROJECT_ID.warehouse.fact_orders` (
    order_key INT64,
    customer_key INT64,
    order_date DATE,
    total_amount NUMERIC
); 