# main.py
import json
import csv
import os
from pathlib import Path
from datetime import datetime

from interactive import run_guided, run_random, ask
from generator.llm import design_schema, generate_rows
from generator.validate import validate_rows
from generator.dirty import inject_dirty_data
from config import OUTPUT_PATH


def save_csv(rows: list[dict], filepath: str):
    """Save rows to CSV."""
    if not rows:
        print(f"  Warning: no rows to save to {filepath}")
        return
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def save_schema(schema: dict, filepath: str):
    """Save schema as JSON for reproducibility."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2)


def save_generation_report(report: dict, filepath: str):
    """Save a generation summary as txt."""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write("=== Synthetic Data Generation Report ===\n\n")
        for key, value in report.items():
            if isinstance(value, dict):
                f.write(f"{key}:\n")
                for k, v in value.items():
                    f.write(f"  {k}: {v}\n")
            elif isinstance(value, list):
                f.write(f"{key}:\n")
                for item in value:
                    f.write(f"  - {item}\n")
            else:
                f.write(f"{key}: {value}\n")


def main():
    print("\n=== Synthetic Data Generator ===\n")

    # Step 1: Choose mode
    mode = ask(
        "Select mode:",
        options=["guided", "random"]
    )

    # Step 2: Get spec
    if mode == "guided":
        spec = run_guided()
    else:
        spec = run_random()

    # Step 3: Design schema
    print("\nDesigning schema via LLM...")
    schema = design_schema(spec)

    # Step 4: Set up output folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_folder = Path(OUTPUT_PATH) / f"{schema.get('filename_prefix', 'dataset')}_{timestamp}"
    run_folder.mkdir(parents=True, exist_ok=True)

    # Enforce hard caps regardless of LLM output
    schema['rows_per_file'] = min(schema['rows_per_file'], 50)
    schema['num_files'] = min(schema['num_files'], 3)
    if len(schema['fields']) > 7:
        schema['fields'] = schema['fields'][:7]

    # Sanitise field types — model sometimes returns verbose type strings
    valid_types = {"int", "float", "string", "date", "bool"}
    for field in schema['fields']:
        raw_type = field.get('type', 'string').split()[0].strip("(,").lower()
        field['type'] = raw_type if raw_type in valid_types else 'string'

    # Step 5: Save schema
    schema_path = run_folder / "schema.json"
    save_schema(schema, str(schema_path))
    print(f"  Schema saved → {schema_path}")

    # Step 6: Generate files
    dirty_config = spec.get("dirty_config", {"enabled": False})
    all_validation_reports = []
    all_dirty_reports = []
    total_rows = 0

    print(f"\nGenerating {schema['num_files']} file(s)...")

    for i in range(schema['num_files']):
        print(f"\n  File {i + 1} of {schema['num_files']}...")

        # Generate rows
        rows = generate_rows(schema, file_index=i)
        print(f"    {len(rows)} rows generated")

        # Validate
        validation = validate_rows(rows, schema)
        all_validation_reports.append(validation)
        status = "passed" if validation['valid'] else "warnings"
        print(f"    Validation: {status} "
              f"({validation['type_failures']} type failures, "
              f"{validation['missing_field_rows']} missing field rows)")

        # Inject dirty data
        rows, dirty_report = inject_dirty_data(rows, dirty_config)
        all_dirty_reports.append(dirty_report)
        if dirty_config.get("enabled"):
            print(f"    Dirty data: {dirty_report['outliers_injected']} outliers, "
                  f"{dirty_report['nulls_injected']} nulls, "
                  f"{dirty_report['duplicates_injected']} duplicates")

        # Save CSV
        filename = f"{schema.get('filename_prefix', 'data')}_{i + 1:02d}.csv"
        filepath = run_folder / filename
        save_csv(rows, str(filepath))
        print(f"    Saved → {filepath}")
        total_rows += len(rows)

    # Step 7: Save generation report
    generation_report = {
        "timestamp":        timestamp,
        "mode":             mode,
        "industry":         schema.get("industry"),
        "data_type":        schema.get("data_type"),
        "time_period":      schema.get("time_period"),
        "num_files":        schema["num_files"],
        "total_rows":       total_rows,
        "output_folder":    str(run_folder),
        "dirty_data":       dirty_config,
        "validation_summary": {
            "files_passed": sum(1 for r in all_validation_reports if r['valid']),
            "total_type_failures": sum(r['type_failures'] for r in all_validation_reports)
        }
    }

    report_path = run_folder / "generation_report.txt"
    save_generation_report(generation_report, str(report_path))

    # Step 8: Print summary
    print(f"\n{'=' * 45}")
    print(f"Done.")
    print(f"  Industry:    {schema.get('industry')}")
    print(f"  Data type:   {schema.get('data_type')}")
    print(f"  Files:       {schema['num_files']}")
    print(f"  Total rows:  {total_rows}")
    print(f"  Output:      {run_folder}")
    print(f"{'=' * 45}\n")


if __name__ == "__main__":
    main()