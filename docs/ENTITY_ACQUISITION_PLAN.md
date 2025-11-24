# **Entity Acquisition Strategy: Transparency 2025**

**Owner:** Data Governance Team

**Objective:** Create the single source of truth for commercial, residential, and institutional entities involved in the ecosystem.

**Target Metric:** 99% accuracy on "Parent Company" and "Physical Address" fields.

## **1. Data Schema & Standardization**

Before gathering data, we must adhere to the **Master Schema** (see data/entities/templates/master\_schema.csv).

### **Critical Definitions**

* **Entity:** The specific physical location or local business unit (e.g., "Starbucks \- 5th Ave").  
* **Parent Organization:** The legal owner or holding company (e.g., "Starbucks Corporation").  
* **Operator:** The party managing the day-to-day (e.g., "Greystar Property Management").

## **2. Execution Phases (Sprints)**

We will execute this in 4 distinct sprints to manage complexity.

### **Sprint 1: Critical Infrastructure (High Visibility)**

**Targets:** Hospitals, Universities, Government Buildings.

* **Sources:**
* * Department of Education/Health datasets.  
  * "OpenStreetMap" (OSM) queries for tags amenity=hospital and amenity=university.  
* **Validation:** Verify against official government accreditation lists.

### **Sprint 2: Large Scale Commercial (Retail & Tech)**

**Targets:** Big Box Retailers, Tech Campuses, HQ Offices.

* **Sources:** * Fortune 500 location lists.  
  * Stock market annual reports (10-K filings) listing real estate assets.  
  * Glassdoor/LinkedIn location data.  
* **Transparency Check:** Must identify if the building is *owned* or *leased* (crucial for transparency).

### **Sprint 3: The Residential Web (Complex)**

**Targets:** Apartment Complexes, Property Management Companies, HOAs.

* **Challenge:** This is the most opaque sector. LLCs often hide true ownership.  
* **Strategy:**  
  1. Scrape major rental listing sites for distinct building names.  
  2. Cross-reference with County Tax Assessor databases to find the "Taxpayer Name" (often the true owner).  
  3. Link "Property Managers" to specific addresses.

### **Sprint 4: Hospitality & Transit**

**Targets:** Hotels, Transit Hubs, Logistics Centers.

* **Sources:** Hotel star rating registries, Chamber of Commerce listings.

## **3. Tooling & Automation**

To avoid manual entry of thousands of rows, we will use the following workflows:

1. **Ingestion Scripts:** Python scripts (to be built) that ingest CSV exports from OpenStreetMap and map them to our master\_schema.csv.  
2. **Deduplication Logic:** \* *Rule:* If Address \+ ZipCode match, flag as duplicate.  
   * *Rule:* Fuzzy matching on names (e.g., "St. Marys" vs "Saint Mary's").

## **4. Quality Assurance (QA) Checklist**

Before merging any data into the main branch:

* \[ \] **Completeness:** Does every entry have a physical address?  
* \[ \] **Uniqueness:** Are there duplicate IDs?  
* \[ \] **Classification:** Is the Sector field strictly from the approved list?  
* \[ \] **Privacy:** Ensure no personal residential addresses (single-family homes) are accidentally included.
