import requests
import csv
import datetime
import os

# Configuration
OVERPASS_URL = "http://overpass-api.de/api/interpreter"
OUTPUT_FILE = "data/entities/raw_imports/osm_import_batch_1.csv"
SCHEMA_HEADERS = [
    "entity_id", "entity_name", "legal_name", "sector", "sub_sector",
    "parent_organization", "property_manager", "address_line_1",
    "city", "state", "zip_code", "latitude", "longitude",
    "asset_status", "verification_source", "last_updated"
]

def fetch_osm_data(area_name="New York"):
    """
    Queries Overpass API for hospitals and universities in a specific area.
    """
    print(f"Fetching Critical Infrastructure for: {area_name}...")
    
    # Overpass QL query: Fetch nodes/ways/relations with amenity=hospital or university
    query = f"""
    [out:json][timeout:25];
    area[name="{area_name}"]->.searchArea;
    (
      node["amenity"~"hospital|university"](area.searchArea);
      way["amenity"~"hospital|university"](area.searchArea);
      relation["amenity"~"hospital|university"](area.searchArea);
    );
    out center;
    """
    
    response = requests.get(OVERPASS_URL, params={'data': query})
    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code}")
        return []
        
    return response.json().get('elements', [])

def map_to_schema(element, index):
    """
    Maps raw OSM JSON data to the Transparency 2025 Master Schema.
    """
    tags = element.get('tags', {})
    
    # Determine coordinates (Node vs Way/Relation center)
    lat = element.get('lat') or element.get('center', {}).get('lat')
    lon = element.get('lon') or element.get('center', {}).get('lon')

    # Schema Mapping Logic
    entity_name = tags.get('name', 'Unknown Entity')
    
    # Sector determination
    amenity = tags.get('amenity', '')
    if amenity == 'hospital':
        sector = 'Healthcare'
        sub_sector = 'Hospital'
    elif amenity == 'university':
        sector = 'Education'
        sub_sector = 'University'
    else:
        sector = 'Other'
        sub_sector = amenity

    # Transparency Fields (The core value of this project)
    parent_org = tags.get('operator', tags.get('brand', 'Unknown'))
    
    # Address Handling
    addr_street = tags.get('addr:street', '')
    addr_number = tags.get('addr:housenumber', '')
    full_address = f"{addr_number} {addr_street}".strip()
    
    row = {
        "entity_id": f"OSM-IMP-{index:05d}",
        "entity_name": entity_name,
        "legal_name": tags.get('official_name', entity_name), # Fallback to name
        "sector": sector,
        "sub_sector": sub_sector,
        "parent_organization": parent_org,
        "property_manager": "Unknown", # OSM rarely has this, requires manual research later
        "address_line_1": full_address if full_address else "Needs Verification",
        "city": tags.get('addr:city', ''),
        "state": tags.get('addr:state', ''),
        "zip_code": tags.get('addr:postcode', ''),
        "latitude": lat,
        "longitude": lon,
        "asset_status": "Active",
        "verification_source": "OpenStreetMap",
        "last_updated": datetime.date.today().isoformat()
    }
    return row

def main():
    # Ensure directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # Fetch Data (Example: San Francisco)
    # In production, loop through a list of target cities
    raw_data = fetch_osm_data("San Francisco")
    
    processed_rows = []
    for i, element in enumerate(raw_data):
        # Filter out unnamed entries which are usually minor metadata points
        if 'name' in element.get('tags', {}):
            processed_rows.append(map_to_schema(element, i+1))
    
    # Write to CSV
    try:
        with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=SCHEMA_HEADERS)
            writer.writeheader()
            writer.writerows(processed_rows)
        print(f"Success! Imported {len(processed_rows)} entities to {OUTPUT_FILE}")
        print("Next Step: Run validate_data.py to check for missing addresses.")
    except IOError as e:
        print(f"File Error: {e}")

if __name__ == "__main__":
    main()
