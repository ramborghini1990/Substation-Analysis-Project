# import osmnx as ox
# import matplotlib.pyplot as plt

# # Specify the name of the city and country
# place_name = "Philadelphia, USA"

# # Fetch OSM street network from the location
# graph = ox.graph_from_place(place_name)

# # Plot the streets
# fig, ax = ox.plot_graph(graph)

# plt.show()


# import osmnx as ox
# from shapely.geometry import Polygon
# import folium

# # Specify the coordinates for the corners of your polygon
# AOI_polygon = Polygon([
#     (-75.214609, 39.943027),  # Southwest corner
#     (-75.124528, 39.943027),  # Southeast corner
#     (-75.124528, 39.972463),  # Northeast corner
#     (-75.214609, 39.972463)   # Northwest corner
# ])

# # Fetch OSM street network from the location
# graph = ox.graph_from_polygon(AOI_polygon, network_type='all')

# # Plot the streets
# m = ox.plot_graph_folium(graph)

# # Save the map to an HTML file
# m.save('map.html')
from services.request_handler import RequestHandler

from shapely import Polygon
import osmnx as ox

print('Starting the program')

# [input variable population]
latitude = 39.9526
longitude = -75.1652

# Creating the square around Philadelphia
polygon_coordinates = [
    (longitude - 0.005, latitude + 0.01),  # Top-left
    (longitude + 0.005, latitude + 0.01),  # Top-right
    (longitude + 0.005, latitude - 0.01),  # Bottom-right
    (longitude - 0.005, latitude - 0.01)   # Bottom-left
]
selected_area_polygon = Polygon(polygon_coordinates)
# [/input variable population]

# import overpass
# try:
#     api = overpass.API(timeout=900)
#     response = api.Get(f'node["power" = "substation"]({longitude - 0.005},{latitude - 0.01},{longitude + 0.005},{latitude + 0.01}); out;')
#     print(response)
# except Exception as ex:
#     print(ex.args)

import overpy
import overpass

# Initialize Overpass API
api = overpass.API()

# Define the coordinates for Philadelphia
min_lat = 39.8670041
max_lat = 40.1379919
min_lon = -75.280284
max_lon = -74.955762

# Define the query
query = f"""
  node["power" = "substation"]
"""

# Send the query
response = api.Get(query)
print(response)

# Print the{ results}
for node in response.nodes:
    print(f"Found substation at {node}")

