import overpass
import pandas as pd
from shapely import Polygon
from typing import Dict, List


class OSMDataFetcher:
    _api = None

    def __init__(self) -> None:
        self._api = overpass.API()
    
    def get_substations_by_polygons(self, multi_polygon: Polygon):
        if multi_polygon.geom_type == 'Polygon':
            bounds = multi_polygon.bounds
            #vertices = [(round(coord[0], 6), round(coord[1], 6)) for coord in polygons.exterior.coords]
        if multi_polygon.geom_type == 'MultiPolygon':
            for polygon in multi_polygon:
                print('HEY BE CAREFUL! REMEMBER TO EXCLUDE THE SMALLER POLYGONS AND KEEP ONLY THE BIG ONE')
                # GEOPANDAS FUNCTION WITHIN
                bounds = multi_polygon.bounds
                #vertices = [(round(coord[0], 6), round(coord[1], 6)) for coord in polygon.exterior.coords]
        
        sw = (bounds[0], bounds[1])
        se = (bounds[2], bounds[1])
        ne = (bounds[2], bounds[3])
        nw = (bounds[0], bounds[3])

        rectangle_coordinates = f'"{sw[1]} {sw[0]} {se[1]} {se[0]} {ne[1]} {ne[0]} {nw[1]} {nw[0]} {sw[1]} {sw[0]}"'

        query = f"way[\"power\"=\"substation\"](poly: {rectangle_coordinates});out geom;"
        response = self._api.Get(query)

        return response

    def analyze_substations_tags_by_state(self, state: str):
        query = f"""
            area[name="{state}"]->.searchArea;
            (
                way["power"="substation"](area.searchArea);
            );
            out geom;
        """
        response = self._api.Get(query)

        features_with_coords = [feature for feature in response.features if len(feature.geometry['coordinates']) > 0]

        number_of_substations_found = len(features_with_coords)
        properties = {
            property for feature in features_with_coords for property in feature.properties
        }

        property_summary_dict: Dict[str, int] = {}
        for property in properties:
            for feature in features_with_coords:
                if property in feature.properties:
                    property_summary_dict[property] = property_summary_dict.get(property, 0) + 1

        analysis_result_df = pd.DataFrame(property_summary_dict.items())
        analysis_result_df.columns = ['property name', 'number of occurences']
        analysis_result_df.to_excel(f'./output/{state}_substation_analysis.xlsx')
