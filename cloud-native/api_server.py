#!/usr/bin/env python3
"""
Unified API Server for Lake Management System CLI

Exposes all CLI commands as HTTP endpoints for Cloud Run deployment.
Supports scheduled execution via Cloud Scheduler.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import subprocess
import os
import sys
import json
import io
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime

app = FastAPI(
    title="Lake Management System API",
    description="Unified API for all BigQuery lake management operations",
    version="2.0.0"
)

# Add modules path
sys.path.insert(0, "/workspace")

class CommandRequest(BaseModel):
    """Base request model for CLI commands."""
    command: str
    project_id: Optional[str] = None
    args: Optional[Dict[str, Any]] = None  # Additional command-specific arguments


# ============================================================================
# Update Metadata Request (legacy support)
# ============================================================================

class UpdateRequest(BaseModel):
    project_id: str
    metadata_table: str
    job_run_table: str
    sleep_ms: Optional[int] = 1000
    max_workers: Optional[int] = 5


# ============================================================================
# Dataset Hierarchy Request
# ============================================================================

class DatasetHierarchyRequest(BaseModel):
    project_id: str
    include_views: Optional[bool] = False
    compare: Optional[str] = None
    output: Optional[str] = None
    format: Optional[str] = "json"  # json, tree, both
    max_tables: Optional[int] = None
    bq_table: Optional[str] = None
    batch_mgmt_table: Optional[str] = None
    batch_id: Optional[str] = None
    compare_latest: Optional[bool] = False
    compare_batch_id: Optional[str] = None
    compare_date: Optional[str] = None


# ============================================================================
# BigQuery Alerts Request
# ============================================================================

class BQAlertsRequest(BaseModel):
    project_id: str
    batch_mgmt_table: Optional[str] = None
    alerts_table: Optional[str] = None


# ============================================================================
# Table List Request
# ============================================================================

class TableListRequest(BaseModel):
    project_id: Optional[str] = None
    dataset: str
    include_views: Optional[bool] = False
    verbose: Optional[bool] = False
    output: Optional[str] = None


# ============================================================================
# Schema Compare Request
# ============================================================================

class SchemaCompareRequest(BaseModel):
    table_a: str
    table_b: str
    project_id: Optional[str] = None


# ============================================================================
# Table Compare Request
# ============================================================================

class TableCompareRequest(BaseModel):
    table_a: str
    table_b: str
    project_id: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================

def create_env_file(request: BaseModel, base_env: Optional[Dict[str, str]] = None) -> str:
    """Create a temporary .env file from request parameters."""
    env_path = "/tmp/.env"
    env_vars = base_env or {}
    
    # Extract project_id if present
    if hasattr(request, 'project_id') and request.project_id:
        env_vars['PROJECT_ID'] = request.project_id
    
    # Extract metadata table if present
    if hasattr(request, 'metadata_table') and request.metadata_table:
        env_vars['METADATA_TABLE'] = request.metadata_table
    
    # Extract job run table if present
    if hasattr(request, 'job_run_table') and request.job_run_table:
        env_vars['JOB_RUN_TABLE'] = request.job_run_table
    
    # Extract sleep_ms if present
    if hasattr(request, 'sleep_ms') and request.sleep_ms:
        env_vars['SLEEP_MSECONDS'] = str(request.sleep_ms)
    
    # Extract max_workers if present
    if hasattr(request, 'max_workers') and request.max_workers:
        env_vars['MAX_PARALLEL_WORKERS'] = str(request.max_workers)
    
    # Extract batch_mgmt_table if present
    if hasattr(request, 'batch_mgmt_table') and request.batch_mgmt_table:
        env_vars['BATCH_MGMT_TABLE'] = request.batch_mgmt_table
    
    # Extract alerts_table if present
    if hasattr(request, 'alerts_table') and request.alerts_table:
        env_vars['ALERTS_TABLE'] = request.alerts_table
    
    # Write to file
    with open(env_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    return env_path


def build_args_list(request: BaseModel, base_args: Optional[List[str]] = None) -> List[str]:
    """Build command-line argument list from request."""
    args = base_args or []
    
    # Add project_id if present
    if hasattr(request, 'project_id') and request.project_id:
        args.extend(["--project", request.project_id])
    
    # Add include_views if present and True
    if hasattr(request, 'include_views') and request.include_views:
        args.append("--include-views")
    
    # Add verbose if present and True
    if hasattr(request, 'verbose') and request.verbose:
        args.append("--verbose")
    
    # Add output if present
    if hasattr(request, 'output') and request.output:
        args.extend(["--output", request.output])
    
    # Dataset hierarchy specific
    if isinstance(request, DatasetHierarchyRequest):
        if request.format and request.format != "json":
            args.extend(["--format", request.format])
        if request.max_tables:
            args.extend(["--max-tables", str(request.max_tables)])
        if request.bq_table:
            args.extend(["--bq-table", request.bq_table])
        if request.batch_mgmt_table:
            args.extend(["--batch-mgmt-table", request.batch_mgmt_table])
        if request.batch_id:
            args.extend(["--batch-id", request.batch_id])
        if request.compare_latest:
            args.append("--compare-latest")
        if request.compare_batch_id:
            args.extend(["--compare-batch-id", request.compare_batch_id])
        if request.compare_date:
            args.extend(["--compare-date", request.compare_date])
        if request.compare:
            args.extend(["--compare", request.compare])
    
    # Schema/Table compare specific
    if isinstance(request, (SchemaCompareRequest, TableCompareRequest)):
        args.append(request.table_a)
        args.append(request.table_b)
    
    # Table list specific
    if isinstance(request, TableListRequest):
        args.extend(["--dataset", request.dataset])
    
    # BQ alerts specific
    if isinstance(request, BQAlertsRequest):
        if request.batch_mgmt_table:
            args.extend(["--batch-mgmt-table", request.batch_mgmt_table])
        if request.alerts_table:
            args.extend(["--alerts-table", request.alerts_table])
    
    return args


def run_cli_module(module_name: str, command_name: str, request: BaseModel) -> Dict[str, Any]:
    """
    Run a CLI module programmatically by creating argparse-compatible args.
    
    Args:
        module_name: Python module name (e.g., "update_metadata")
        command_name: CLI command name (e.g., "update-metadata")
        request: Request object with command parameters
    """
    try:
        # Create .env file
        env_path = create_env_file(request)
        
        # Import the module
        module = __import__(f"modules.{module_name}", fromlist=["main"])
        
        # Create argparse Namespace object from request
        # Modules use argparse, so we need to create a compatible namespace
        class Args:
            def __init__(self, data: dict):
                for key, value in data.items():
                    # Convert snake_case to the format argparse expects
                    setattr(self, key, value)
        
        # Build args dict from request
        args_dict = {}
        request_dict = request.dict(exclude_none=True)
        
        # Convert request fields to argparse-style attributes
        for key, value in request_dict.items():
            # Keep original key (CLI modules expect --format, not format_style)
            args_dict[key] = value
        
        # Special handling for project_id -> project
        if 'project_id' in args_dict:
            args_dict['project'] = args_dict.pop('project_id')
        
        args = Args(args_dict)
        
        # Capture stdout/stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        # Set environment variables
        env = {**os.environ.copy()}
        env['ENV_PATH'] = env_path
        if hasattr(request, 'project_id') and request.project_id:
            env['PROJECT_ID'] = request.project_id
        
        # Temporarily set environment
        old_env = os.environ.copy()
        os.environ.update(env)
        
        try:
            # Run the module's main function
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                return_code = module.main(args)
            
            stdout = stdout_capture.getvalue()
            stderr = stderr_capture.getvalue()
        finally:
            # Restore environment
            os.environ.clear()
            os.environ.update(old_env)
        
        if return_code != 0:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": f"Command failed with return code {return_code}",
                    "stdout": stdout,
                    "stderr": stderr
                }
            )
        
        return {
            "status": "success",
            "return_code": return_code,
            "stdout": stdout,
            "stderr": stderr,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Module {module_name} not found: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        raise HTTPException(
            status_code=500,
            detail=f"Error running command: {str(e)}\nTraceback: {traceback.format_exc()}"
        )


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Lake Management System API",
        "version": "2.0.0",
        "endpoints": {
            "update-metadata": "/update-metadata",
            "dataset-hierarchy": "/dataset-hierarchy",
            "bq-alerts": "/bq-alerts",
            "table-list": "/table-list",
            "schema-compare": "/schema-compare",
            "table-compare": "/table-compare",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/update-metadata")
async def update_metadata(req: UpdateRequest):
    """Update column metadata (legacy endpoint for backward compatibility)."""
    env_path = create_env_file(req)
    
    try:
        # Use subprocess for update_metadata (legacy support)
        result = subprocess.run(
            ["python3", "update_column_descriptions.py", "--log"],
            env={**os.environ, "ENV_PATH": env_path},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd="/workspace"
        )

        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)

        return {
            "status": "success",
            "stdout": result.stdout,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/dataset-hierarchy")
async def dataset_hierarchy(req: DatasetHierarchyRequest):
    """Run dataset hierarchy analysis."""
    return run_cli_module("dataset_hierarchy", "dataset-hierarchy", req)


@app.post("/bq-alerts")
async def bq_alerts(req: BQAlertsRequest):
    """Run BigQuery alerts detection."""
    return run_cli_module("bq_alerts", "bq-alerts", req)


@app.post("/table-list")
async def table_list(req: TableListRequest):
    """Extract table list to CSV."""
    return run_cli_module("table_list", "table-list", req)


@app.post("/schema-compare")
async def schema_compare(req: SchemaCompareRequest):
    """Compare table schemas."""
    return run_cli_module("schema_compare", "schema-compare", req)


@app.post("/table-compare")
async def table_compare(req: TableCompareRequest):
    """Compare table data."""
    return run_cli_module("table_compare", "table-compare", req)


@app.post("/command")
async def run_command(req: CommandRequest):
    """
    Generic command endpoint that accepts command name and arguments.
    
    Example:
    {
        "command": "dataset-hierarchy",
        "project_id": "my-project",
        "args": {
            "format": "tree",
            "batch_mgmt_table": "dataset.batch_management"
        }
    }
    """
    try:
        # Map command names to module names and request classes
        command_map = {
            "dataset-hierarchy": ("dataset_hierarchy", DatasetHierarchyRequest),
            "bq-alerts": ("bq_alerts", BQAlertsRequest),
            "table-list": ("table_list", TableListRequest),
            "schema-compare": ("schema_compare", SchemaCompareRequest),
            "table-compare": ("table_compare", TableCompareRequest),
            "update-metadata": ("update_metadata", UpdateRequest),
        }
        
        if req.command not in command_map:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown command: {req.command}. Available: {list(command_map.keys())}"
            )
        
        module_name, request_class = command_map[req.command]
        
        # Build request object
        request_data = {"project_id": req.project_id or os.getenv("PROJECT_ID")}
        if req.args:
            request_data.update(req.args)
        
        request_obj = request_class(**request_data)
        
        return run_cli_module(module_name, req.command, request_obj)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
