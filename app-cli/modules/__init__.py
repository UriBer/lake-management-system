"""
Shared utilities and configuration for Lake Management System CLI modules.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env files
def load_config():
    """Load configuration from .env files."""
    # Try to load from app-cli directory first
    app_cli_dir = Path(__file__).parent.parent
    env_file = app_cli_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    # Also try to load from current directory
    load_dotenv()

def get_project_id(project_arg: Optional[str] = None) -> str:
    """Get project ID from argument or environment."""
    if project_arg:
        return project_arg
    
    project_id = os.getenv("PROJECT_ID")
    if not project_id:
        sys.exit("❌ PROJECT_ID must be set in .env file or provided via --project")
    
    return project_id

def parse_table_reference(table_ref: str, default_project: str) -> tuple[str, str, str]:
    """
    Parse table reference into project, dataset, table components.
    
    Args:
        table_ref: Table reference in format "project.dataset.table" or "dataset.table"
        default_project: Default project to use if not specified
    
    Returns:
        Tuple of (project, dataset, table)
    """
    parts = table_ref.split('.')
    
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    elif len(parts) == 2:
        return default_project, parts[0], parts[1]
    else:
        sys.exit(f"❌ Invalid table reference format: {table_ref}. Use 'project.dataset.table' or 'dataset.table'")

def format_table_ref(project: str, dataset: str, table: str) -> str:
    """Format table components into full reference."""
    return f"{project}.{dataset}.{table}"

def log(message: str, verbose: bool = False):
    """Print message if verbose mode is enabled."""
    if verbose:
        print(f"ℹ️  {message}")

# Initialize configuration when module is imported
load_config()
