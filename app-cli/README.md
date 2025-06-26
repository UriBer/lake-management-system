# Lake Management System – CLI Tools

This directory contains command-line tools for managing and auditing Google BigQuery data lake environments. Each tool is organized in its own subdirectory with dedicated documentation and code.

## Directory Structure

```
app-cli/
├── compare-tables/
│   ├── compare_tables.py
│   └── README.md
└── update-column-metadata/
    ├── main.py
    ├── requirements.txt
    ├── readme.md
    ├── sample/
    │   ├── create_tables.sh
    │   ├── create_tables.sql
    │   └── sample_metadata.csv
    └── (log files)
```

---

## Projects

### 1. compare-tables

**Purpose:**  
Compares table structures between BigQuery projects, highlighting differences and writing results to both a text file and a BigQuery audit table.

**Key Files:**
- `compare_tables.py`: Main script for comparing tables.
- `README.md`: Setup, usage, and requirements.

---

### 2. update-column-metadata

**Purpose:**  
Automates the update of BigQuery column descriptions using metadata from a dedicated table. Supports logging, error handling, and rate limiting.

**Key Files:**
- `main.py`: Main script for updating column metadata.
- `requirements.txt`: Python dependencies.
- `readme.md`: Detailed setup, configuration, and usage instructions.
- `sample/`: Example setup scripts and sample metadata.
  - `create_tables.sh`: Shell script to create sample tables and load metadata.
  - `create_tables.sql`: SQL for table creation.
  - `sample_metadata.csv`: Example metadata for testing.
- `column_updates_job_*.log`: Log files generated during update runs.

---

## Getting Started

Each subproject contains its own README with setup and usage instructions.  
**Typical workflow:**
1. Choose the tool you need (`compare-tables` or `update-column-metadata`).
2. Follow the setup instructions in the respective README.
3. Run the tool as described.

---

## Requirements

- Python 3.6+
- Google Cloud SDK (`gcloud`) configured
- BigQuery API enabled
- Appropriate permissions in your GCP project

---

## Contributing

See individual subproject READMEs for development and contribution guidelines. 