from google.cloud import bigquery
import argparse

def get_schema_dict(schema):
    return {field.name: (field.field_type, field.mode) for field in schema}

def get_row_count(client, table_ref):
    query = f"SELECT COUNT(*) AS row_count FROM `{table_ref}`"
    result = client.query(query).result()
    return list(result)[0]["row_count"]

def compare_schemas(schema_a, schema_b):
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
    candidates = []
    for field in schema_a:
        if field in schema_b:
            type_a, mode_a = schema_a[field]
            type_b, mode_b = schema_b[field]
            if type_a == type_b and "REPEATED" not in (mode_a, mode_b):
                candidates.append(field)
    return candidates

def compare_data_records(client, table_a, table_b, join_keys, sample_limit=5):
    if not join_keys:
        print("\n❌ No common fields found to join tables.")
        return

    key_expr = " AND ".join([f"A.{col} = B.{col}" for col in join_keys])
    key_select = ", ".join([f"A.{col}" for col in join_keys])

    query = f"""
    WITH a_only AS (
      SELECT {key_select}
      FROM `{table_a}` A
      LEFT JOIN `{table_b}` B ON {key_expr}
      WHERE B.{join_keys[0]} IS NULL
      LIMIT {sample_limit}
    ),
    b_only AS (
      SELECT {key_select}
      FROM `{table_b}` B
      LEFT JOIN `{table_a}` A ON {key_expr}
      WHERE A.{join_keys[0]} IS NULL
      LIMIT {sample_limit}
    ),
    mismatched AS (
      SELECT {key_select}
      FROM `{table_a}` A
      JOIN `{table_b}` B ON {key_expr}
      WHERE TO_JSON_STRING(A) != TO_JSON_STRING(B)
      LIMIT {sample_limit}
    )
    SELECT 'only_in_a' AS type, * FROM a_only
    UNION ALL
    SELECT 'only_in_b' AS type, * FROM b_only
    UNION ALL
    SELECT 'mismatched' AS type, * FROM mismatched
    """
    results = list(client.query(query).result())

    print("\n🔎 Heuristic Data Comparison (Join on: {})".format(", ".join(join_keys)))
    if not results:
        print("✔ All records match across the tables.")
    else:
        for row in results:
            row_type = row["type"]
            keys = ", ".join(f"{k}={row[k]}" for k in join_keys)
            print(f"  ❗ {row_type.upper()}: {keys}")

def print_report(table_a, table_b, count_a, count_b, differences):
    print("=" * 80)
    print("📊 BigQuery Schema & Row Count Comparison Report")
    print("=" * 80)
    print(f"Table A: {table_a}")
    print(f"Table B: {table_b}")
    print(f"\n🧮 Row count:")
    print(f"  - {table_a}: {count_a:,} rows")
    print(f"  - {table_b}: {count_b:,} rows\n")

    print("🟨 Fields only in Table A:")
    if differences["only_in_a"]:
        for f, defn in differences["only_in_a"].items():
            print(f"  - {f}: {defn}")
    else:
        print("  ✔ No extra fields in Table A.")

    print("\n🟦 Fields only in Table B:")
    if differences["only_in_b"]:
        for f, defn in differences["only_in_b"].items():
            print(f"  - {f}: {defn}")
    else:
        print("  ✔ No extra fields in Table B.")

    print("\n🔁 Fields with different definitions:")
    if differences["different_definitions"]:
        for f, defs in differences["different_definitions"].items():
            print(f"  - {f}:")
            print(f"      Table A: {defs['table_a']}")
            print(f"      Table B: {defs['table_b']}")
    else:
        print("  ✔ No fields with differing types or modes.")
    print("=" * 80)

def main(table_a, table_b, project_id=None):
    client = bigquery.Client(project=project_id)

    schema_a = client.get_table(table_a).schema
    schema_b = client.get_table(table_b).schema

    schema_a_dict = get_schema_dict(schema_a)
    schema_b_dict = get_schema_dict(schema_b)

    differences = compare_schemas(schema_a_dict, schema_b_dict)

    count_a = get_row_count(client, table_a)
    count_b = get_row_count(client, table_b)

    print_report(table_a, table_b, count_a, count_b, differences)
    #ask user if they want to compare data records
    compare_data = input("Do you want to compare data records? (y/n): ")
    if compare_data == "y":
        join_keys = detect_join_keys(schema_a_dict, schema_b_dict)
        if not join_keys:
            print("\n⚠️ No valid common join keys found.")
        else:
            compare_data_records(client, table_a, table_b, join_keys[:1])  # try with top candidate

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare schemas, row counts, and records of two BigQuery tables.")
    parser.add_argument("table_a", help="Fully qualified table A (e.g. project.dataset.table)")
    parser.add_argument("table_b", help="Fully qualified table B (e.g. project.dataset.table)")
    parser.add_argument("--project", help="Optional GCP project ID")

    args = parser.parse_args()
    main(args.table_a, args.table_b, args.project)