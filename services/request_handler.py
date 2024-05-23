import math
import mpu
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import geometry
import os
import osmnx as ox
import networkx as nx

from services.primary import PrimaryModel
from services.secondary import SecondaryModel

class RequestHandler:
    _substation_file_path = './repositories/substations.csv'
    _load_profile_file_path = './repositories/load_profiles.csv'
    _export_directory = './output'
    _model_created = False

    # [input variables]
    _alpha = 0.5
    _min_alpha = 0
    _max_alpha = 1
    _alpha_step = 0.01
    _offset = 3 #feet
    _line_treshold = 50 #feet
    _pole_distance = 100 #feet
    _houses_per_pole = 2
    _min_houses_per_pole = 2
    _max_houses_per_pole = 5
    _buildings_per_cluster = 3
    _min_buildings_per_cluster = 2
    _max_buildings_per_cluster = 10
    # [/input variables]

    def __init__(self):
        self.origin_shift = 2 * math.pi * 6378137 / 2.0
        self._substations = pd.read_csv(self._substation_file_path, index_col=2)
        self._load_profiles = pd.read_csv(self._load_profile_file_path)
    

    def get_substations(self):
        return self._substations
    
    def get_substations_in_polygon(self, polygon):
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
        return coordinates_of_substations_in_polygon
    
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

    def build_grid(self, polygon):

        self.G = ox.graph_from_polygon(polygon, network_type='drive')

        substation_coords = self.get_substations_in_polygon(polygon)

        if len(substation_coords):
            print(f"{len(substation_coords)} Substations found in selected area")
            X = []
            Y = []

            for x, y in substation_coords:
                x, y = self._lat_lon_to_meters(y, x)
                X.append(x)
                Y.append(y)

            building_data = self.get_buildings_data(polygon)
            
            Primary = PrimaryModel(self.G, substation_coords)
            print("Building primary model")
            Primaries = Primary.build(self._offset, self._pole_distance, self._line_treshold)
            print("Primary model: ", Primaries)
            
            primary_positions = nx.get_node_attributes(Primaries, 'pos')

            print("Building secondary model")
            Secondary = SecondaryModel(building_data, substation_coords)
            sec_data = Secondary.build(
                buildingsPerCluster=self._buildings_per_cluster,
                HousesPerPole=self._houses_per_pole
            )
            print("Secondary model build complete")
        
            
            K = [k.split("_") for k in sec_data.keys()]
            for B, H in K:
                B = int(B)
                H = int(H)
                infrastructure = sec_data[f"{B}_{H}"]["infrastructure"]
                #infrastructure = Secondary.allign_infrastructure_to_road(infrastructure, self.G)
                infrastructure = Secondary.centroid(infrastructure, self.G, self._alpha)
                print("Creating secondary model")
                secondaries, xfmrs, self.xfmr_mapping = Secondary.create_secondaries(infrastructure, sec_data[f"{B}_{H}"]["buildings"], B, H)
                print("Secondary model: ", secondaries)
                self.complete_model = nx.compose(Primaries, secondaries)
                self.complete_model = self.stitch_graphs(self.complete_model, xfmrs, primary_positions)
                print("Complete model: ", self.complete_model)

                self.plot_graph(self.complete_model)
            self.model_created = True
            print("Network creation is complete!")
        else:
            print("No substation found in selected area")
    
    def plot_graph(self, graph):
        xs = []
        ys = []
        for u, v in graph.edges():
            u_attr = graph.nodes[u]["pos"]
            x1, y1 = self._lat_lon_to_meters(u_attr[1], u_attr[0])
            v_attr = graph.nodes[v]["pos"]
            x2, y2 = self._lat_lon_to_meters(v_attr[1], v_attr[0])
            xs.append([x1 + self._offset, x2 + self._offset])
            ys.append([y1 + self._offset, y2 + self._offset])

        return

    def stitch_graphs(self, G, xfmr, primaries):
        for u , u_pos in xfmr.items():
            D = np.inf
            v_f = None
            for v, v_pos in primaries.items():
                d = mpu.haversine_distance(np.flip(u_pos), np.flip(v_pos))
                if d < D:
                    D = d
                    v_f = v
            attrs = {"length": D}
            G.add_edge(u, v_f, **attrs)
        return G