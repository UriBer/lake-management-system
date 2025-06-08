# Lake Management System - Column Description Updater

This application connects to Google BigQuery to update column descriptions based on metadata stored in a separate BigQuery table. It reads configuration parameters from a `.env` file to ensure sensitive information and configuration are easily managed.

## Setup Instructions
Follow these steps to set up and run the application:

### 1. Create and Configure `.env` File

Create a file named `.env` in the `app-cli/` directory. This file will store your BigQuery project ID, metadata table names, and other configuration. Add the following content to it, replacing the placeholder values with your actual project and table details:

```
PROJECT_ID=your=project-id
METADATA_TABLE=datasetname.tablename
JOB_RUN_TABLE=datasetname.job_runs
SLEEP_SECONDS=2
```

-   `PROJECT_ID`: Your Google Cloud Project ID where your BigQuery datasets are located.
-   `METADATA_TABLE`: The full path to your metadata table (e.g., `your_dataset.your_metadata_table`) please create a dataset for governance metadata, e.g.: governance_metadata.
-   `JOB_RUN_TABLE`: The full path to the table where job run logs will be stored (under the dataset you created).
-   `SLEEP_SECONDS`: The delay in seconds between BigQuery ALTER commands to avoid rate limits.

### 2. Install Dependencies

Navigate to the `app-cli/` directory in your terminal and install the required Python packages using `pip`:

```bash
pip install -r app-cli/requirements.txt
```
Please make sure you have authorized against your BigQuery account.

### 3. Run the Application

Once the `.env` file is configured and dependencies are installed, you can run the application from the `app-cli/` directory:

```bash
python main.py
```

The application will connect to BigQuery, fetch metadata, update column descriptions, and log the job run results.
