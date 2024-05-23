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
    _model_created = False
    _alpha = 0.5
    _min_alpha = 0
    _max_alpha = 1
    _alpha_step = 0.01
    _offset = 3 #feet
    _line_trash = 50 #feet
    _pole_distance = 100 #feet
    _houses_per_pole = 2
    _min_houses_per_pole = 2
    _max_houses_per_pole = 5
    _buildings_per_cluster = 3
    _min_buildings_per_cluster = 2
    _max_buildings_per_cluster = 10




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



    def lasso_callback(self, polygon):
        xs = [event.geometry['x0'], event.geometry['x0'], event.geometry['x1'], event.geometry['x1']]
        ys = [event.geometry['y0'], event.geometry['y1'], event.geometry['y1'], event.geometry['y0']]
        if isinstance(xs, list):
            Coordinates = []
            for x, y in zip(xs, ys):
                LongLat = self.MetersToLatLon(x, y)
                Coordinates.append(LongLat)
            polygon = geometry.Polygon(Coordinates)
            self.G = ox.graph_from_polygon(polygon, network_type='drive')

            SubstationCoords = self.get_substations_in_polygon(polygon)

            if len(SubstationCoords):
                print(f"{len(SubstationCoords)} Substations found in selected area")
                X = []
                Y = []

                for x, y in SubstationCoords:
                    x, y = self.LatLonToMeters(y, x)
                    X.append(x)
                    Y.append(y)

                self.s1.data = dict(
                    X=X,
                    Y=Y,
                )
                self.subs.data_source = self.s1
                buildingData = self.get_buildings_data(polygon)
                
                Primary = PrimaryModel(self.G, SubstationCoords)
                print("Building primary model")
                Primaries = Primary.build(self.prim_offset, self.prim_pole_distance, self.prim_line_thresh)
                print("Primary model: ", Primaries)
                
                primary_positions = nx.get_node_attributes(Primaries, 'pos')

                print("Building secondary model")
                Secondary = SecondaryModel(buildingData, SubstationCoords)
                secData = Secondary.build(
                    buildingsPerCluster=self.sec_buildings_per_cluster,
                    HousesPerPole=self.sec_houses_per_pole
                )
                print("Secondary model build complete")
            
                
                K = [k.split("_") for k in secData.keys()]
                for B, H in K:
                    B = int(B)
                    H = int(H)
                    infrastructure = secData[f"{B}_{H}"]["infrastructure"]
                    #infrastructure = Secondary.allign_infrastructure_to_road(infrastructure, self.G)
                    infrastructure = Secondary.centroid(infrastructure, self.G, self.alpha_mult)
                    print("Creating secondary model")
                    secondaries, xfmrs, self.xfmr_mapping = Secondary.create_secondaries(infrastructure, secData[f"{B}_{H}"]["buildings"], B, H)
                    print("Secondary model: ", secondaries)
                    self.building_data_ = secData[f"{B}_{H}"]["buildings"]
                    self.complete_model = nx.compose(Primaries, secondaries)
                    self.complete_model = self.stitch_graphs(self.complete_model, xfmrs, primary_positions)
                    print("Complete model: ", self.complete_model)

                    self.plot_graph(self.complete_model)
                self.model_created = True
                print("Network creation is complete!")
            else:
                print("No substation found in selected area")
