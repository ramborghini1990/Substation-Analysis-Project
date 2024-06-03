import overpass
from shapely import Polygon
from typing import List


class OSMDataFetcher:
    _api = None

    def __init__(self) -> None:
        self._api = overpass.API()
    
    def get_substations_by_polygons(self, polygons: List[Polygon]):
        if polygons.geom_type == 'Polygon':
            bounds = polygons.bounds
            #vertices = [(round(coord[0], 6), round(coord[1], 6)) for coord in polygons.exterior.coords]
        if polygons.geom_type == 'MultiPolygon':
            for polygon in polygons:
                print('HEY BE CAREFUL! REMEMBER TO EXCLUDE THE SMALLER POLYGONS AND KEEP ONLY THE BIG ONE')
                # GEOPANDAS FUNCTION WITHIN
                bounds = polygons.bounds
                #vertices = [(round(coord[0], 6), round(coord[1], 6)) for coord in polygon.exterior.coords]
        
        sw = (bounds[0], bounds[1])
        se = (bounds[2], bounds[1])
        ne = (bounds[2], bounds[3])
        nw = (bounds[0], bounds[3])

        rectangle_coordinates = f'"{sw[1]} {sw[0]} {se[1]} {se[0]} {ne[1]} {ne[0]} {nw[1]} {nw[0]} {sw[1]} {sw[0]}"'

        # coordinates_list = ' '.join([f"{vertex[1]} {vertex[0]}" for vertex in bounds])
        # coordinates_list = '"' + coordinates_list.strip() + '"'

        query = f"way[\"power\"=\"substation\"](poly: {rectangle_coordinates});out geom;"
        response = self._api.Get(query)

        print(response)

