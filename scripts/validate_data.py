import csv
import sys

# Configuration
INPUT_FILE = "data/entities/raw_imports/osm_import_batch_1.csv"
REQUIRED_FIELDS = ["entity_name", "sector", "address_line_1", "latitude", "longitude"]
APPROVED_SECTORS = ["Healthcare", "Education", "Retail", "Residential", "Technology", "Hospitality"]

def validate_csv(filepath):
    print(f"Starting Validation for: {filepath}")
    issues = []
    seen_ids = set()
    seen_locations = set() # For duplicate detection (Lat+Lon)
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2): # Start at 2 for header
                
                # 1. Check Completeness (Missing Required Fields)
                for field in REQUIRED_FIELDS:
                    if not row.get(field) or row.get(field).strip() == "" or row.get(field) == "Needs Verification":
                        issues.append(f"Row {row_num}: Missing or Invalid '{field}' - {row.get('entity_name', 'Unknown')}")

                # 2. Check Sector Classification
                if row.get('sector') not in APPROVED_SECTORS:
                    issues.append(f"Row {row_num}: Invalid Sector '{row.get('sector')}'")

                # 3. Check ID Uniqueness
                e_id = row.get('entity_id')
                if e_id in seen_ids:
                    issues.append(f"Row {row_num}: Duplicate Entity ID found '{e_id}'")
                seen_ids.add(e_id)

                # 4. Check Location Duplicates (Fuzzy Logic)
                # Rounding lat/lon to 4 decimal places detects entities at exact same location
                try:
                    loc_key = (round(float(row['latitude']), 4), round(float(row['longitude']), 4))
                    if loc_key in seen_locations:
                        issues.append(f"Row {row_num}: Potential Physical Duplicate at {loc_key} - {row.get('entity_name')}")
                    seen_locations.add(loc_key)
                except (ValueError, TypeError):
                    pass # Handled by field check above

    except FileNotFoundError:
        print(f"Error: File {filepath} not found.")
        return

    # Report Results
    print("\n--- VALIDATION REPORT ---")
    if issues:
        print(f"FAILED: Found {len(issues)} issues.")
        for issue in issues:
            print(f"[x] {issue}")
        sys.exit(1) # Exit with error code
    else:
        print("PASSED: Data is clean and ready for merge.")
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        validate_csv(sys.argv[1])
    else:
        validate_csv(INPUT_FILE)
