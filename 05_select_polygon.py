import geopandas as gpd
from shapely.geometry import Polygon
import requests
import json

# Read the shapefile
file_path = '.\repositories\ireti_torino\ireti_torino.shp' 
data = gpd.read_file(file_path)

# Select a polygon
# Assuming you want the first polygon
polygon = data.geometry[0]

# Extract vertices from the polygon
# The exterior.coords property of a Polygon object gives the coordinates
vertices = list(polygon.exterior.coords)

# Build the query
query = "[out:json];(poly:'"
for vertex in vertices:
    query += f"{vertex[1]} {vertex[0]} "
query += "')->.a;(way(pivot.a);>;);out;"

# Use the built query with Overpass
overpass_url = "http://overpass-api.de/api/interpreter"
response = requests.get(overpass_url, params={'data': query})

# Check if the result has len(response.features) == 1
data = response.json()
features = data['elements']
if len(features) == 1:
    print("The result has one feature.")
else:
    print(f"The result has {len(features)} features.")
