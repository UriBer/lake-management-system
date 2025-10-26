"""
Schema Compare Module - Compare schemas between two BigQuery tables.
"""

from google.cloud import bigquery
from google.api_core.exceptions import NotFound, BadRequest

from . import get_project_id, parse_table_reference, format_table_ref, log

def get_schema_dict(schema):
    """Convert BigQuery schema to dictionary."""
    return {field.name: (field.field_type, field.mode) for field in schema}

def get_row_count(client, table_ref):
    """Get row count for a table."""
    query = f"SELECT COUNT(*) AS row_count FROM `{table_ref}`"
    result = client.query(query).result()
    return list(result)[0]["row_count"]

def compare_schemas(schema_a, schema_b):
    """Compare two schemas and return differences."""
    keys_a = set(schema_a.keys())
    keys_b = set(schema_b.keys())

    only_in_a = keys_a - keys_b
    only_in_b = keys_b - keys_a
    in_both = keys_a & keys_b

    differences = {
        "only_in_a": {f: schema_a[f] for f in only_in_a},
        "only_in_b": {f: schema_b[f] for f in only_in_b},
        "different_definitions": {}
    }

    for f in in_both:
        if schema_a[f] != schema_b[f]:
            differences["different_definitions"][f] = {
                "table_a": schema_a[f],
                "table_b": schema_b[f]
            }

    return differences

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

def compare_data_records(client, table_a, table_b, join_keys, sample_limit=5):
    """Compare data records between two tables."""
    if not join_keys:
        print("\n❌ No common fields found to join tables.")
        return

    key_expr = " AND ".join([f"A.{col} = B.{col}" for col in join_keys])
    
    # Find records only in A
    query_only_a = f"""
    SELECT {', '.join([f"A.{col}" for col in join_keys])}
    FROM `{table_a}` A
    LEFT JOIN `{table_b}` B ON {key_expr}
    WHERE B.{join_keys[0]} IS NULL
    LIMIT {sample_limit}
    """
    
    # Find records only in B
    query_only_b = f"""
    SELECT {', '.join([f"B.{col}" for col in join_keys])}
    FROM `{table_b}` B
    LEFT JOIN `{table_a}` A ON {key_expr}
    WHERE A.{join_keys[0]} IS NULL
    LIMIT {sample_limit}
    """
    
    # Find mismatched records
    query_mismatch = f"""
    SELECT {', '.join([f"A.{col}" for col in join_keys])}
    FROM `{table_a}` A
    INNER JOIN `{table_b}` B ON {key_expr}
    WHERE A.{join_keys[0]} != B.{join_keys[0]}
    LIMIT {sample_limit}
    """
    
    try:
        print(f"\n🔎 Heuristic Data Comparison (Join on: {', '.join(join_keys)})")
        
        # Records only in A
        result_a = client.query(query_only_a).result()
        records_a = list(result_a)
        if records_a:
            print(f"  ❗ ONLY_IN_A: {len(records_a)} records")
            for record in records_a[:3]:  # Show first 3
                key_values = [str(record[col]) for col in join_keys]
                print(f"    {' AND '.join([f'{k}={v}' for k, v in zip(join_keys, key_values)])}")
        
        # Records only in B
        result_b = client.query(query_only_b).result()
        records_b = list(result_b)
        if records_b:
            print(f"  ❗ ONLY_IN_B: {len(records_b)} records")
            for record in records_b[:3]:  # Show first 3
                key_values = [str(record[col]) for col in join_keys]
                print(f"    {' AND '.join([f'{k}={v}' for k, v in zip(join_keys, key_values)])}")
        
        # Mismatched records
        result_mismatch = client.query(query_mismatch).result()
        records_mismatch = list(result_mismatch)
        if records_mismatch:
            print(f"  ❗ MISMATCHED: {len(records_mismatch)} records")
            for record in records_mismatch[:3]:  # Show first 3
                key_values = [str(record[col]) for col in join_keys]
                print(f"    {' AND '.join([f'{k}={v}' for k, v in zip(join_keys, key_values)])}")
        
        if not (records_a or records_b or records_mismatch):
            print("  ✅ No differences found in data records")
            
    except Exception as e:
        print(f"  ❌ Error comparing data records: {e}")

def main(args):
    """Main function for schema-compare command."""
    # Get configuration
    project_id = get_project_id(args.project)
    
    # Parse table references
    project_a, dataset_a, table_a = parse_table_reference(args.table_a, project_id)
    project_b, dataset_b, table_b = parse_table_reference(args.table_b, project_id)
    
    table_ref_a = format_table_ref(project_a, dataset_a, table_a)
    table_ref_b = format_table_ref(project_b, dataset_b, table_b)
    
    print(f"🚀 Comparing schemas:")
    print(f"  Table A: {table_ref_a}")
    print(f"  Table B: {table_ref_b}")
    
    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=project_id)
    except Exception as e:
        print(f"❌ Error connecting to BigQuery: {e}")
        return 1
    
    # Get schemas and row counts
    try:
        table_obj_a = client.get_table(table_ref_a)
        table_obj_b = client.get_table(table_ref_b)
        
        schema_a = get_schema_dict(table_obj_a.schema)
        schema_b = get_schema_dict(table_obj_b.schema)
        
        row_count_a = get_row_count(client, table_ref_a)
        row_count_b = get_row_count(client, table_ref_b)
        
    except NotFound as e:
        print(f"❌ Table not found: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error fetching table information: {e}")
        return 1
    
    # Compare schemas
    differences = compare_schemas(schema_a, schema_b)
    
    # Print results
    print("\n" + "="*80)
    print("📊 BigQuery Schema & Row Count Comparison Report")
    print("="*80)
    print(f"Table A: {table_ref_a}")
    print(f"Table B: {table_ref_b}")
    
    print(f"\n🧮 Row count:")
    print(f"  - {table_ref_a}: {row_count_a:,} rows")
    print(f"  - {table_ref_b}: {row_count_b:,} rows")
    
    # Fields only in A
    if differences["only_in_a"]:
        print(f"\n🟨 Fields only in Table A:")
        for field, (field_type, mode) in differences["only_in_a"].items():
            print(f"  - {field}: ('{field_type}', '{mode}')")
    
    # Fields only in B
    if differences["only_in_b"]:
        print(f"\n🟦 Fields only in Table B:")
        for field, (field_type, mode) in differences["only_in_b"].items():
            print(f"  - {field}: ('{field_type}', '{mode}')")
    
    # Fields with different definitions
    if differences["different_definitions"]:
        print(f"\n🔁 Fields with different definitions:")
        for field, definitions in differences["different_definitions"].items():
            print(f"  - {field}:")
            print(f"      Table A: {definitions['table_a']}")
            print(f"      Table B: {definitions['table_b']}")
    
    print("="*80)
    
    # Ask if user wants to compare data records
    try:
        user_input = input("\nDo you want to compare data records? (y/n): ").lower().strip()
        if user_input in ['y', 'yes']:
            join_keys = detect_join_keys(schema_a, schema_b)
            if join_keys:
                compare_data_records(client, table_ref_a, table_ref_b, join_keys)
            else:
                print("\n❌ No suitable join keys found for data comparison")
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
        return 130
    
    print(f"\n🏁 Schema comparison complete!")
    return 0
