# import geopandas as gpd

# # Load the GeoPackage file
# def load_geopackage(file_path):
#     try:
#         gdf = gpd.read_file(file_path)
#         print("GeoPackage loaded successfully!")
#         return gdf
#     except Exception as e:
#         print(f"Error loading GeoPackage: {e}")

# # Function to fetch substation border based on OBJECTID
# def get_substation_border(gdf, border_id):
#     try:
#         # Ensure the ID exists in the GeoDataFrame
#         border = gdf[gdf['OBJECTID'] == border_id]
        
#         if border.empty:
#             raise ValueError(f"No substation border found for ID {border_id}")
        
#         return border
#     except Exception as e:
#         print(e)


# gpkg_file_path = "./repositories/primary_cabins.gpkg"  


# gdf = load_geopackage(gpkg_file_path)

# # Example 
# border_id = 124291  
# border = get_substation_border(gdf, border_id)

# if border is not None:
#     print("Substation border found:", border)



############################
import fiona

# Path to your GPKG file
gpkg_file = './repositories/primary_cabins.gpkg'

# List all layers in the GPKG file
with fiona.Env():
    with fiona.open(gpkg_file, layer=None) as src:
        layers = fiona.listlayers(gpkg_file)

# Print the available layers
print("Available layers:", layers)




# from flask import Flask, request, jsonify
# import geopandas as gpd
# import json
# from services.osm_data_fetcher import OSMDataFetcher  # Assuming you already have this service

# app = Flask(__name__)

# # Initialize OSM Data Fetcher
# osm_data_fetcher = OSMDataFetcher()

# # Load the GeoPackage containing substation borders
# def get_substation_borders(gpkg_path):
#     gdf = gpd.read_file(gpkg_path)
#     return gdf

# # Fetch substation locations from OSM
# def get_substation_locations(polygon):
#     response = osm_data_fetcher.get_substations_by_polygons(polygon)
#     return response

# # Flask POST endpoint
# @app.route('/generate_network', methods=['POST'])
# def generate_network():
#     try:
#         data = request.get_json()

#         # Input: substation border, building geojson, and consumption profile data
#         substation_id = data['substation_id']
#         buildings_geojson = data['buildings']
#         consumption_profile = data['consumption_profile']

#         # Fetch substation borders from GPKG
#         borders_gpkg = './repositories/primary_cabins.gpkg'
#         borders_gdf = get_substation_borders(borders_gpkg)

#         # Fetch substation location from OSM (assuming geometry from borders_gdf)
#         substation_border_geometry = borders_gdf.loc[borders_gdf['OBJECTID'] == substation_id, 'geometry'].values[0]
#         osm_substation_data = get_substation_locations(substation_border_geometry)

#         # Run the SING algorithm (assuming you have this)
#         # Placeholder: You can integrate the SING function with the input
#         grid_geojson = {
#             "type": "FeatureCollection",
#             "features": [
#                 # Fill with your network grid data
#             ]
#         }

#         # Return the generated GeoJSON
#         return jsonify(grid_geojson)

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# # Run the Flask app
# if __name__ == '__main__':
#     app.run(debug=True)
