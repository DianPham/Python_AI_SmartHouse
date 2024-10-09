import geopandas as gpd
import json

# Define file paths to the shapefiles
city_shapefile = 'geo/gadm41_VNM_1.shp'  # Admin Level 1 (Provinces)
district_shapefile = 'geo/gadm41_VNM_2.shp'  # Admin Level 2 (Districts)

# Load the city shapefile (Admin Level 1) for provinces
cities_gdf = gpd.read_file(city_shapefile)

# Load the district shapefile (Admin Level 2) for districts
districts_gdf = gpd.read_file(district_shapefile)

# Ensure both GeoDataFrames have the same CRS (Coordinate Reference System)
districts_gdf = districts_gdf.to_crs(cities_gdf.crs)

# Function to convert district GeoDataFrame to nested JSON within provinces
def combine_provinces_districts(cities_gdf, districts_gdf):
    # Prepare a dictionary to hold the final result
    districts_list = []
    # Loop over each province (Admin Level 1)
    for _, province_row in cities_gdf.iterrows():  # Corrected iterrows() usage
        province_name = province_row['NAME_1'].lower()  # Convert province name to lowercase
        # Get all districts that belong to the current province and convert the names to lowercase for matching
        province_districts = districts_gdf[districts_gdf['NAME_1'].str.lower() == province_name]
        
        # # Extract districts details     
        for _, district_row in province_districts.iterrows():
            district_name = district_row['NAME_2'].lower()  # Convert district name to lowercase
        #     district_centroid = district_row.geometry.centroid  # Centroid for lat/long of the district

        #     districts_list.append({
        #         'name': district_name,
        #         'latitude': district_centroid.y,
        #         'longitude': district_centroid.x,
        #         'province': province_name
        #     })
            print("- " + district_name)
        
        # Add province and its nested districts to the combined_data list
    
    return districts_list

# Combine provinces and districts into one structure
combined_json = combine_provinces_districts(cities_gdf, districts_gdf)

# Save the data to JSON files, ensuring lowercase is preserved
with open('provinces_with_districts_lowercase.json', 'w', encoding='utf-8') as f:
    json.dump(combined_json, f, ensure_ascii=False, indent=4)

print("Conversion complete. JSON files saved.")
