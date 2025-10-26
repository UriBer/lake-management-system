"""
Table Compare Module - Compare data between two BigQuery tables.
"""

from google.cloud import bigquery
from google.api_core.exceptions import NotFound, BadRequest

from . import get_project_id, parse_table_reference, format_table_ref, log

def get_schema_dict(schema):
    """Convert BigQuery schema to dictionary."""
    return {field.name: (field.field_type, field.mode) for field in schema}

def detect_join_keys(schema_a, schema_b):
    """Detect potential join keys between two schemas."""
    candidates = []
    for field in schema_a:
        if field in schema_b:
            type_a, mode_a = schema_a[field]
            type_b, mode_b = schema_b[field]
            if type_a == type_b and "REPEATED" not in (mode_a, mode_b):
                candidates.append(field)
    return candidates

def compare_table_data(client, table_a, table_b, join_keys, sample_limit=10):
    """Compare data between two tables using join keys."""
    if not join_keys:
        print("❌ No common fields found to join tables.")
        return
    
    print(f"🔍 Comparing data using join keys: {', '.join(join_keys)}")
    
    # Build join condition
    join_condition = " AND ".join([f"A.{col} = B.{col}" for col in join_keys])
    
    # Count total records in each table
    count_a_query = f"SELECT COUNT(*) as count FROM `{table_a}`"
    count_b_query = f"SELECT COUNT(*) as count FROM `{table_b}`"
    
    try:
        count_a = list(client.query(count_a_query).result())[0]["count"]
        count_b = list(client.query(count_b_query).result())[0]["count"]
        
        print(f"📊 Record counts:")
        print(f"  Table A: {count_a:,} records")
        print(f"  Table B: {count_b:,} records")
        
    except Exception as e:
        print(f"❌ Error getting record counts: {e}")
        return
    
    # Find records only in A
    only_a_query = f"""
    SELECT {', '.join([f"A.{col}" for col in join_keys])}
    FROM `{table_a}` A
    LEFT JOIN `{table_b}` B ON {join_condition}
    WHERE B.{join_keys[0]} IS NULL
    LIMIT {sample_limit}
    """
    
    # Find records only in B
    only_b_query = f"""
    SELECT {', '.join([f"B.{col}" for col in join_keys])}
    FROM `{table_b}` B
    LEFT JOIN `{table_a}` A ON {join_condition}
    WHERE A.{join_keys[0]} IS NULL
    LIMIT {sample_limit}
    """
    
    # Find common records
    common_query = f"""
    SELECT COUNT(*) as count
    FROM `{table_a}` A
    INNER JOIN `{table_b}` B ON {join_condition}
    """
    
    try:
        # Records only in A
        print(f"\n🔍 Records only in Table A:")
        result_a = client.query(only_a_query).result()
        records_a = list(result_a)
        if records_a:
            print(f"  Found {len(records_a)} sample records (showing first {min(5, len(records_a))}):")
            for i, record in enumerate(records_a[:5]):
                key_values = [str(record[col]) for col in join_keys]
                print(f"    {i+1}. {' AND '.join([f'{k}={v}' for k, v in zip(join_keys, key_values)])}")
        else:
            print("  ✅ No records found only in Table A")
        
        # Records only in B
        print(f"\n🔍 Records only in Table B:")
        result_b = client.query(only_b_query).result()
        records_b = list(result_b)
        if records_b:
            print(f"  Found {len(records_b)} sample records (showing first {min(5, len(records_b))}):")
            for i, record in enumerate(records_b[:5]):
                key_values = [str(record[col]) for col in join_keys]
                print(f"    {i+1}. {' AND '.join([f'{k}={v}' for k, v in zip(join_keys, key_values)])}")
        else:
            print("  ✅ No records found only in Table B")
        
        # Common records count
        common_result = client.query(common_query).result()
        common_count = list(common_result)[0]["count"]
        print(f"\n📊 Common records: {common_count:,}")
        
        # Summary
        print(f"\n📈 Comparison Summary:")
        print(f"  Records only in A: {len(records_a)} (sample)")
        print(f"  Records only in B: {len(records_b)} (sample)")
        print(f"  Common records: {common_count:,}")
        
    except Exception as e:
        print(f"❌ Error comparing data: {e}")

def main(args):
    """Main function for table-compare command."""
    # Get configuration
    project_id = get_project_id(args.project)
    
    # Parse table references
    project_a, dataset_a, table_a = parse_table_reference(args.table_a, project_id)
    project_b, dataset_b, table_b = parse_table_reference(args.table_b, project_id)
    
    table_ref_a = format_table_ref(project_a, dataset_a, table_a)
    table_ref_b = format_table_ref(project_b, dataset_b, table_b)
    
    print(f"🚀 Comparing table data:")
    print(f"  Table A: {table_ref_a}")
    print(f"  Table B: {table_ref_b}")
    
    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=project_id)
    except Exception as e:
        print(f"❌ Error connecting to BigQuery: {e}")
        return 1
    
    # Get table schemas
    try:
        table_obj_a = client.get_table(table_ref_a)
        table_obj_b = client.get_table(table_ref_b)
        
        schema_a = get_schema_dict(table_obj_a.schema)
        schema_b = get_schema_dict(table_obj_b.schema)
        
    except NotFound as e:
        print(f"❌ Table not found: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error fetching table information: {e}")
        return 1
    
    # Detect join keys
    join_keys = detect_join_keys(schema_a, schema_b)
    
    if not join_keys:
        print("❌ No suitable join keys found for data comparison")
        print("Tables must have at least one common field with matching types")
        return 1
    
    print(f"🔑 Detected join keys: {', '.join(join_keys)}")
    
    # Compare data
    compare_table_data(client, table_ref_a, table_ref_b, join_keys)
    
    print(f"\n🏁 Table comparison complete!")
    return 0
