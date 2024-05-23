import math
import pandas as pd
import geopandas as gpd
from shapely import geometry
import os
import osmnx as ox

class RequestHandler:
    _substation_file_path = './repositories/substations.csv'
    _load_profile_file_path = './repositories/load_profiles.csv'
    _export_directory = './output'

    def __init__(self):
        self.origin_shift = 2 * math.pi * 6378137 / 2.0
        self._substations = pd.read_csv(self._substation_file_path, index_col=2)
        self._load_profiles = pd.read_csv(self._load_profile_file_path)
    

    def get_substations(self):
        return self._substations
    
    def insert_filtered_by_polygon_substations(self, polygon):
        # [puts coordinates of the substations inside the polygon in the variable coordinates]
        coordinates_of_substations_in_polygon = []
        for x, y in zip(self._substations["X"].tolist(), self._substations["Y"].tolist()):
            LongLat = self._meters_to_lat_lon(x, y)
            P = geometry.Point(LongLat)
            if P.within(polygon):
                coordinates_of_substations_in_polygon.append(LongLat)
        # [/puts coordinates of the substations inside the polygon in the variable coordinates]

        filtered_substations_file = os.path.join(self._export_directory, "substations.txt")
        textfile = open(filtered_substations_file, "w")
        for element in coordinates_of_substations_in_polygon:
            text = ",".join([str(e) for e in element])
            textfile.write(text + "\n")
        textfile.close()
    
    def get_buildings_data(self, polygon):
        self.building_data = {}
        self.B: gpd.GeoDataFrame = ox.features_from_polygon(polygon, tags={"building": True})
        for idx, row in self.B.iterrows():
            x, y = self._lat_lon_to_meters(
                row["geometry"].centroid.y,
                row["geometry"].centroid.x
            )
            self.building_data[idx[1]] = {
                "X": x,
                "Y": y,
                "Floors": row["building:levels"] if "building:levels" in row else 1,
                "Area": row["geometry"].area,
                "Type": row["building"],
            }
        self.building_data = pd.DataFrame(self.building_data).T

        buildings_file = os.path.join(self._export_directory, "buildings.csv")
        self.building_data.to_csv(buildings_file)

        return self.building_data



    def _meters_to_lat_lon(self, mx, my):
        #"""Converts XY point from Spherical Mercator EPSG:900913 to lat/lon in WGS84 Datum"""

        lon = (mx / self.origin_shift) * 180.0
        lat = (my / self.origin_shift) * 180.0

        lat = 180 / math.pi * (2 * math.atan(math.exp(lat * math.pi / 180.0)) - math.pi / 2.0)
        return lon, lat
    
    def _lat_lon_to_meters(self, lat, lon):
        #"""Converts given lat/lon in WGS84 Datum to XY in Spherical Mercator EPSG:900913"""

        mx = lon * self.origin_shift / 180.0
        my = math.log(math.tan((90 + lat) * math.pi / 360.0)) / (math.pi / 180.0)

        my = my * self.origin_shift / 180.0
        return mx, my

