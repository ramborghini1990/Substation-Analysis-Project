import geopandas as gpd
import json
from shapely.geometry import shape
import sys
sys.path.append('./services')
import os
import model
from osm_data_fetcher import OSMDataFetcher
from model import Model  
from primary import PrimaryModel  
from secondary import SecondaryModel  
from request_handler import RequestHandler  
from fuzzywuzzy import fuzz



# def test_osm_fetcher():
#     fetcher = OSMDataFetcher()
#     test_polygon = shape({'type': 'Polygon', 'coordinates': [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]]})
#     data = fetcher.get_substations_by_polygons(test_polygon)
#     print("Test data fetched:", data)


border_id = 124291  


def main():
    try:
        request_handler = RequestHandler()
        request_handler.build_grid(124291)
    except Exception as e:
        print("An error occurred:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()