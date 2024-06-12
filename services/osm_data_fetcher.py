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

        return analysis_result_df


    def analyze_substations_tags_values_by_state(self, state: str, property_names: List[str]):
        query = f"""
            area[name="{state}"]->.searchArea;
            (
                way["power"="substation"](area.searchArea);
            );
            out geom;
        """
        response = self._api.Get(query)

        features_with_coords = [feature for feature in response.features if len(feature.geometry['coordinates']) > 0]
        values_dict: Dict[str, set] = {}
        for property in property_names:
            for feature in features_with_coords:
                property_value = next((
                    property_value for property_key, property_value in feature.properties.items() if property_key == property
                ), None)
                if property_value is not None:
                    if property not in values_dict:
                        values_dict[property] = set() 
                    values_dict[property].add(property_value)

        final_analysis_df = pd.DataFrame(values_dict.items())
        final_analysis_df.to_excel(f'./output/{state}_tags_values_analysis.xlsx')


    # def analyze_substations_tags_values_by_state_distribution(self, state: str, property_names: List[str]):
    #     query = f"""
    #         area[name="{state}"]->.searchArea;
    #         (
    #             way["power"="substation"](area.searchArea);
    #         );
    #         out geom;
    #     """
    #     response = self._api.Get(query)

    #     features_with_coords = [feature for feature in response.features if len(feature.geometry['coordinates']) > 0]
    #     values_dict: Dict[str, set] = {}
    #     distribution_substations = []
    #     for property in property_names:
    #         for feature in features_with_coords:
    #             distribution_substation = next((
    #                 feature for property_key, property_value in feature.properties.items() if property_key == "substation" and property_value == "distribution"
    #             ), None)
    #             if distribution_substation is not None:
    #                 distribution_substations.append(distribution_substation)

    #     print(len(distribution_substations))

    def analyze_substations_tags_values_by_state_distribution(self, state: str, property_names: List[str]):
        query = f"""
             area[name="{state}"]->.searchArea;
            (
                way["power"="substation"](area.searchArea);
            );
            out geom;
        """
        response = self._api.Get(query)

        features_with_coords = [feature for feature in response.features if len(feature.geometry['coordinates']) > 0]
        distribution_substations = []
        for feature in features_with_coords:
            if all(key not in feature.properties for key in ["height", "it:fvg:ctrn:code", "it:fvg:ctrn:revision","operator:wikipedia",
            "disused",'voltage:secondary','voltage:primary',
            "disused:transformer", "abandoned",'utility','disused','industrial','ref:enel:type:connection','tourism','historic','plant:source',
            'operational_status','ruins','demolished:building','building:disused','end_date']):
                for property in property_names:
                    if property in feature.properties and feature.properties[property] == "distribution":
                        distribution_substations.append(feature)

        print(len(distribution_substations))
            
        # Prepare data for CSV
        data_for_csv = []
        for substation in distribution_substations:
            coords = substation.geometry['coordinates']
            data_for_csv.append([substation, coords[0], coords[1]])

        # Convert to DataFrame and save as CSV
        final_analysis_df = pd.DataFrame(data_for_csv, columns=['Substation', 'Longitude', 'Latitude'])
        final_analysis_df.to_csv(f'./output/{state}_distribution_substations.csv', index=False)
