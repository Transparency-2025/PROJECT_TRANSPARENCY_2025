import requests
import csv
import json
from typing import List, Dict

class DublinApartmentExtractor:
    """Extract apartment blocks from OpenStreetMap data for Dublin areas."""
    
    OVERPASS_URL = "http://overpass-api.de/api/interpreter"
    
    # Predefined area codes for Dublin regions (OSM relation IDs)
    DUBLIN_AREAS = {
        "Dublin City": "1955",
        "South Dublin": "3718588",
        "Fingal (North Dublin)": "1971803",
        "Dún Laoghaire-Rathdown": "1968917",
        "Co. Dublin": "1971803,3718588,1968917,1955"  # Combined
    }
    
    # Dublin postal districts (approximate bounding boxes)
    DUBLIN_POSTAL = {
        "Dublin 1": (53.344, -6.268, 53.358, -6.245),
        "Dublin 2": (53.335, -6.268, 53.348, -6.245),
        "Dublin 3": (53.355, -6.268, 53.375, -6.220),
        "Dublin 4": (53.315, -6.268, 53.335, -6.220),
        "Dublin 5": (53.365, -6.190, 53.390, -6.140),
        "Dublin 6": (53.310, -6.290, 53.330, -6.250),
        "Dublin 7": (53.345, -6.300, 53.365, -6.265),
        "Dublin 8": (53.330, -6.290, 53.345, -6.265),
    }
    
    def build_overpass_query(self, area_name: str) -> str:
        """Build Overpass QL query for apartment buildings."""
        
        # Check if it's a postal district (use bounding box)
        if area_name in self.DUBLIN_POSTAL:
            bbox = self.DUBLIN_POSTAL[area_name]
            query = f"""
            [out:json][timeout:60];
            (
              node["building"="apartments"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
              way["building"="apartments"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
              relation["building"="apartments"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
              
              node["building"="residential"]["residential"="apartments"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
              way["building"="residential"]["residential"="apartments"]({bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]});
            );
            out center tags;
            """
        # Use named area (county/city level)
        elif area_name in self.DUBLIN_AREAS:
            area_id = self.DUBLIN_AREAS[area_name]
            if "," in area_id:  # Multiple areas (Co. Dublin)
                area_queries = []
                for aid in area_id.split(","):
                    area_queries.append(f'area({aid})->.a{aid};')
                    area_queries.append(f'(node["building"="apartments"](area.a{aid});')
                    area_queries.append(f'way["building"="apartments"](area.a{aid});')
                    area_queries.append(f'relation["building"="apartments"](area.a{aid}););')
                
                query = f"""
                [out:json][timeout:120];
                {"".join(area_queries)}
                out center tags;
                """
            else:
                query = f"""
                [out:json][timeout:90];
                area({area_id})->.searchArea;
                (
                  node["building"="apartments"](area.searchArea);
                  way["building"="apartments"](area.searchArea);
                  relation["building"="apartments"](area.searchArea);
                  
                  node["building"="residential"]["residential"="apartments"](area.searchArea);
                  way["building"="residential"]["residential"="apartments"](area.searchArea);
                );
                out center tags;
                """
        else:
            raise ValueError(f"Unknown area: {area_name}")
        
        return query
    
    def query_overpass(self, query: str) -> List[Dict]:
        """Execute Overpass API query and return results."""
        try:
            response = requests.post(
                self.OVERPASS_URL,
                data={"data": query},
                timeout=120
            )
            response.raise_for_status()
            data = response.json()
            return data.get("elements", [])
        except requests.exceptions.RequestException as e:
            print(f"Error querying Overpass API: {e}")
            return []
    
    def extract_apartment_info(self, elements: List[Dict]) -> List[Dict]:
        """Extract relevant information from OSM elements."""
        apartments = []
        
        for element in elements:
            tags = element.get("tags", {})
            
            # Get coordinates
            if "center" in element:
                lat = element["center"]["lat"]
                lon = element["center"]["lon"]
            elif "lat" in element and "lon" in element:
                lat = element["lat"]
                lon = element["lon"]
            else:
                lat, lon = None, None
            
            apartment_info = {
                "name": tags.get("name", "Unnamed"),
                "address": self._format_address(tags),
                "postcode": tags.get("addr:postcode", ""),
                "building_levels": tags.get("building:levels", ""),
                "apartments": tags.get("apartments", ""),
                "latitude": lat,
                "longitude": lon,
                "osm_id": element.get("id", ""),
                "osm_type": element.get("type", "")
            }
            
            apartments.append(apartment_info)
        
        return apartments
    
    def _format_address(self, tags: Dict) -> str:
        """Format address from OSM tags."""
        address_parts = []
        
        if "addr:housenumber" in tags:
            address_parts.append(tags["addr:housenumber"])
        if "addr:street" in tags:
            address_parts.append(tags["addr:street"])
        if "addr:city" in tags:
            address_parts.append(tags["addr:city"])
        
        return ", ".join(address_parts) if address_parts else ""
    
    def export_to_csv(self, apartments: List[Dict], filename: str):
        """Export apartment data to CSV file."""
        if not apartments:
            print("No apartment data to export.")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = apartments[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(apartments)
        
        print(f"Exported {len(apartments)} apartments to {filename}")
    
    def get_apartments(self, area_name: str, output_file: str = None):
        """Main method to extract and export apartment data."""
        print(f"Querying OpenStreetMap for apartments in {area_name}...")
        
        query = self.build_overpass_query(area_name)
        elements = self.query_overpass(query)
        
        print(f"Found {len(elements)} apartment buildings.")
        
        apartments = self.extract_apartment_info(elements)
        
        if output_file is None:
            output_file = f"{area_name.replace(' ', '_').replace(',', '')}_apartments.csv"
        
        self.export_to_csv(apartments, output_file)
        
        return apartments


# Example usage
if __name__ == "__main__":
    extractor = DublinApartmentExtractor()
    
    # Show available areas
    print("Available areas:")
    print("Postal Districts:", list(extractor.DUBLIN_POSTAL.keys()))
    print("Counties/Cities:", list(extractor.DUBLIN_AREAS.keys()))
    print()
    
    # Example: Extract apartments from Dublin 1
    area = "Dublin 1"
    apartments = extractor.get_apartments(area)
    
    # Print first few results
    print(f"\nFirst 5 apartment blocks in {area}:")
    for apt in apartments[:5]:
        print(f"  - {apt['name']} ({apt['address']})")