# Lake Management System

A comprehensive solution for managing and maintaining Google BigQuery data lakes, with a focus on **column metadata management** and **environment similarity tracking**. This system provides both command-line tools for development and cloud-native automation for production environments.

## 🎯 Purpose

The Lake Management System addresses two critical challenges in data lake operations:

1. **Column Metadata Management**: Automatically synchronizes column descriptions across BigQuery tables using centralized metadata governance
2. **Environment Similarity**: Tracks and compares table structures between different environments (dev, staging, prod) to ensure consistency

## 📁 Project Structure

```
lake-management-system/
├── app-cli/                          # Command-line tools for development
│   ├── compare-tables/               # Environment comparison tool
│   │   ├── compare_tables.py         # Compares tables between BigQuery projects
│   │   └── README.md                 # Tool-specific documentation
│   └── update-column-metadata/       # Column metadata management tool
│       ├── main.py                   # Updates column descriptions from metadata
│       ├── requirements.txt          # Python dependencies
│       ├── readme.md                 # Detailed setup and usage
│       └── sample/                   # Example setup and sample data
│           ├── create_tables.sh      # Setup script for sample tables
│           ├── create_tables.sql     # SQL for creating sample tables
│           └── sample_metadata.csv   # Sample metadata for testing
├── cloud-native/                     # Production-ready cloud automation
│   ├── update_column_descriptions.py # Core column update logic
│   ├── api_server.py                 # FastAPI server for Cloud Run
│   ├── Dockerfile                    # Container configuration
│   ├── requirements.txt              # Python dependencies
│   ├── main.tf                       # Terraform for Cloud Run deployment
│   ├── cloud_scheduler.tf            # Terraform for scheduled execution
│   ├── iam_permissions.tf            # Terraform for IAM setup
│   └── README.md                     # Cloud deployment documentation
└── README.md                         # This file
```

## 🛠️ Components

### 1. Column Metadata Management

**Problem**: Column descriptions in BigQuery tables often become outdated or inconsistent, making data discovery and governance difficult.

**Solution**: Centralized metadata management with automated synchronization.

**Features**:
- Updates column descriptions from a centralized metadata table
- Supports batch processing with rate limiting
- Comprehensive logging and audit trails
- Parallel processing for performance
- Change detection (only updates when descriptions differ)

**Implementation**:
- **CLI Tool** (`app-cli/update-column-metadata/`): For development and manual runs
- **Cloud Service** (`cloud-native/`): Automated daily execution via Cloud Run and Cloud Scheduler

### 2. Environment Similarity Tracking

**Problem**: Data lake environments (dev, staging, prod) can drift apart, leading to inconsistencies and deployment issues.

**Solution**: Automated comparison and reporting of table structures across environments.

**Features**:
- Compares table existence between BigQuery projects
- Generates detailed reports (text file + BigQuery audit table)
- Tracks differences over time with timestamps
- Identifies tables missing in specific environments

**Implementation**:
- **CLI Tool** (`app-cli/compare-tables/`): Manual environment comparison

## 🚀 Getting Started

### Prerequisites

- Python 3.6+
- Google Cloud SDK (`gcloud`) configured
- BigQuery API enabled
- Appropriate IAM permissions in your GCP project

### Quick Start

1. **For Development/CLI Usage**:
   ```bash
   cd app-cli
   # See individual tool READMEs for setup instructions
   ```

2. **For Production/Cloud Deployment**:
   ```bash
   cd cloud-native
   # Follow the cloud-native README for deployment
   ```

## 📋 Use Cases

### Column Metadata Management

- **Data Governance**: Ensure all columns have proper descriptions for data discovery
- **Compliance**: Maintain audit trails of metadata changes
- **Team Collaboration**: Centralized metadata management for large teams
- **Documentation**: Automatically keep BigQuery column descriptions up-to-date

### Environment Similarity

- **Deployment Validation**: Verify that all environments have the same table structure
- **Drift Detection**: Identify when environments become out of sync
- **Audit Compliance**: Track environment differences for compliance reporting
- **Release Management**: Ensure successful deployments across environments

## 🔧 Configuration

Both components use environment variables for configuration:

- `PROJECT_ID`: Your Google Cloud Project ID
- `METADATA_TABLE`: BigQuery table containing column metadata
- `JOB_RUN_TABLE`: BigQuery table for logging job executions
- `SLEEP_MSECONDS`: Rate limiting delay between operations

## 📊 Monitoring and Logging

- **Job Execution Logs**: All operations are logged to BigQuery for audit trails
- **Local Logging**: CLI tools support local log files for debugging
- **Error Handling**: Comprehensive error handling with detailed error messages
- **Performance Metrics**: Execution time and statistics for optimization

## 🔐 Security

- Uses Google Cloud service accounts with minimal required permissions
- Environment variables for sensitive configuration
- Audit logging for all operations
- Rate limiting to prevent API quota exhaustion

## 🤝 Contributing

Each component has its own documentation and setup instructions. See individual README files for:
- Detailed setup instructions
- Configuration options
- Usage examples
- Troubleshooting guides

## 📈 Roadmap

- Schema comparison (column types, constraints)
- Automated drift correction
- Integration with CI/CD pipelines
- Web-based dashboard for monitoring
- Support for additional cloud providers 