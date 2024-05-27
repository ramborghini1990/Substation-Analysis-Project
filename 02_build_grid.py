

from services.request_handler import RequestHandler

from shapely import Polygon

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


request_handler = RequestHandler()
request_handler.build_grid(selected_area_polygon)
# Plot the graph on OpenStreetMap
request_handler.plot_on_osm(request_handler.complete_model)


print('Program ended')