#!/usr/bin/env python3
"""
Lake Management System - Unified CLI

A unified command-line interface for all BigQuery utilities in the Lake Management System.

Usage:
    lake-cli <command> [options]
    
Examples:
    lake-cli table-list --dataset my_dataset
    lake-cli schema-compare table1 table2
    lake-cli table-compare table1 table2
    lake-cli update-metadata --log
"""

import sys
import argparse
from pathlib import Path

# Add the app-cli directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def setup_main_parser():
    """Setup the main argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="lake-cli",
        description="Lake Management System - Unified CLI for BigQuery utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available commands:
  table-list      Extract table information from BigQuery datasets to CSV
  schema-compare  Compare schemas between two BigQuery tables
  table-compare   Compare data between two BigQuery tables
  update-metadata Update column descriptions from metadata table

Examples:
  lake-cli table-list --dataset my_dataset
  lake-cli schema-compare table1 table2
  lake-cli table-compare table1 table2
  lake-cli update-metadata --log

For help on specific commands:
  lake-cli <command> --help
        """
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="Lake Management System CLI v1.0.0"
    )
    
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        metavar="<command>"
    )
    
    return parser, subparsers

def setup_table_list_parser(subparsers):
    """Setup parser for table-list command."""
    parser = subparsers.add_parser(
        "table-list",
        help="Extract table information from BigQuery datasets to CSV",
        description="Extract table information from a specific BigQuery dataset and export to CSV format."
    )
    
    parser.add_argument(
        "--dataset", 
        required=True,
        help="BigQuery dataset name to extract tables from"
    )
    
    parser.add_argument(
        "--project",
        help="BigQuery project ID (defaults to PROJECT_ID from .env)"
    )
    
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output CSV file path (defaults to dataset_tables_YYYYMMDD_HHMMSS.csv)"
    )
    
    parser.add_argument(
        "--include-views",
        action="store_true",
        help="Include views in addition to tables"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    return parser

def setup_schema_compare_parser(subparsers):
    """Setup parser for schema-compare command."""
    parser = subparsers.add_parser(
        "schema-compare",
        help="Compare schemas between two BigQuery tables",
        description="Compare field definitions, types, and modes between two BigQuery tables."
    )
    
    parser.add_argument(
        "table_a",
        help="First table to compare (format: project.dataset.table or dataset.table)"
    )
    
    parser.add_argument(
        "table_b", 
        help="Second table to compare (format: project.dataset.table or dataset.table)"
    )
    
    parser.add_argument(
        "--project",
        help="BigQuery project ID (defaults to PROJECT_ID from .env)"
    )
    
    return parser

def setup_table_compare_parser(subparsers):
    """Setup parser for table-compare command."""
    parser = subparsers.add_parser(
        "table-compare",
        help="Compare data between two BigQuery tables",
        description="Compare data records between two BigQuery tables using heuristic join keys."
    )
    
    parser.add_argument(
        "table_a",
        help="First table to compare (format: project.dataset.table or dataset.table)"
    )
    
    parser.add_argument(
        "table_b",
        help="Second table to compare (format: project.dataset.table or dataset.table)"
    )
    
    parser.add_argument(
        "--project",
        help="BigQuery project ID (defaults to PROJECT_ID from .env)"
    )
    
    return parser

def setup_update_metadata_parser(subparsers):
    """Setup parser for update-metadata command."""
    parser = subparsers.add_parser(
        "update-metadata",
        help="Update column descriptions from metadata table",
        description="Update BigQuery column descriptions from a metadata table using parallel processing."
    )
    
    parser.add_argument(
        "--log",
        action="store_true",
        help="Write execution log to local file"
    )
    
    return parser

def main():
    """Main entry point for the unified CLI."""
    parser, subparsers = setup_main_parser()
    
    # Setup subcommand parsers
    setup_table_list_parser(subparsers)
    setup_schema_compare_parser(subparsers)
    setup_table_compare_parser(subparsers)
    setup_update_metadata_parser(subparsers)
    
    # Parse arguments
    args = parser.parse_args()
    
    # If no command provided, show help
    if not args.command:
        parser.print_help()
        return 1
    
    # Import and run the appropriate module
    try:
        if args.command == "table-list":
            from modules.table_list import main as table_list_main
            return table_list_main(args)
        
        elif args.command == "schema-compare":
            from modules.schema_compare import main as schema_compare_main
            return schema_compare_main(args)
        
        elif args.command == "table-compare":
            from modules.table_compare import main as table_compare_main
            return table_compare_main(args)
        
        elif args.command == "update-metadata":
            from modules.update_metadata import main as update_metadata_main
            return update_metadata_main(args)
        
        else:
            print(f"❌ Unknown command: {args.command}")
            return 1
            
    except ImportError as e:
        print(f"❌ Error importing module: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
