import geopandas as gpd
from shapely.geometry import box
import requests
import json
import numpy as np

from services.osm_data_fetcher import OSMDataFetcher


# Read the shapefile
file_path = './repositories/ireti_torino/ireti_torino.shp' 
data = gpd.read_file(file_path)

# Select a geometry (could be Polygon or MultiPolygon)
geometry = data.geometry[1]

osm_data_fetcher = OSMDataFetcher()
osm_data_fetcher.get_substations_by_polygons(geometry)




# # Define the size of the grid
# grid_size = 0.01

# # Get the bounds of the original geometry
# minx, miny, maxx, maxy = geometry.bounds

# # Create a grid of boxes (i.e., small polygons)
# boxes = []
# for x in np.arange(minx, maxx, grid_size):
#     for y in np.arange(miny, maxy, grid_size):
#         boxes.append(box(x, y, x+grid_size, y+grid_size))

# # Intersect the boxes with the original geometry
# small_polygons = [geometry.intersection(b) for b in boxes if geometry.intersects(b)]

# # Now you can loop over the small polygons and make a separate query for each
# for small_poly in small_polygons:
#     # Check if the small polygon is a MultiPolygon
#     if small_poly.geom_type == 'MultiPolygon':
#         for polygon in small_poly.geoms:  # Use .geoms here
#             vertices = [(round(coord[0], 6), round(coord[1], 6)) for coord in polygon.exterior.coords]
#             # Ensure the polygon is closed
#             if vertices[0] != vertices[-1]:
#                 vertices.append(vertices[0])
#             # Build and send the query for each polygon...
#     else:  # It's a Polygon
#         vertices = [(round(coord[0], 6), round(coord[1], 6)) for coord in small_poly.exterior.coords]
#         # Ensure the polygon is closed
#         if vertices[0] != vertices[-1]:
#             vertices.append(vertices[0])
#         # Build and send the query...

#     query = "[out:json];way(poly:'" + ' '.join([f"{vertex[1]} {vertex[0]}" for vertex in vertices]) + "');(._;>;);out;"

#     # Use the built query with Overpass
#     overpass_url = "http://overpass-api.de/api/interpreter"
#     response = requests.get(overpass_url, params={'data': query})

#     # Check the status code of the response
#     if response.status_code == 200:
#         try:
#             # Check if the result has len(response.features) == 1
#             data = response.json()
#             features = data['elements']
#             if len(features) == 1:
#                 print("The result has one feature.")
#             else:
#                 print(f"The result has {len(features)} features.")
#         except json.decoder.JSONDecodeError:
#             print("Failed to decode JSON from response")
#     else:
#         print(f"Request failed with status code {response.status_code}")
#         print("Response content:")
#         print(response.text)  # This will print the response content
