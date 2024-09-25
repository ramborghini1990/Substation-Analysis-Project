from fuzzywuzzy import fuzz
from shapely.geometry import shape
import math
import mpu
import numpy as np
import pandas as pd
import pickle
import geopandas as gpd
from shapely import geometry
import os
import osmnx as ox
import networkx as nx
from osm_data_fetcher import OSMDataFetcher
from repositories.operator_map import operator_map
from repositories.substation_borders_repo import SubstationBorderRepo
from services.model import Model
from services.primary import PrimaryModel
from services.secondary import SecondaryModel

class RequestHandler:
    _substation_borders_file_path = './repositories/primary_cabins.gpkg'



    _substation_file_path = './repositories/substations.csv'
    _load_profile_file_path = './repositories/load_profiles.csv'
    _export_directory = './output'
    _model_created = False

    # [non engineering input variables]
    _file_name = 'test'
    _circuit_name = 'grid'
    # [/non engineering input variables]

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
    _hv_voltage = 115
    _mv_voltage = 12.47
    _primary_conductor = '2/0  ACSR'
    _secondary_conductor = '4  ACSR'
    # [/input variables]


    _substation_border_repo = None
    _fetcher = None

    def __init__(self):
        self.origin_shift = 2 * math.pi * 6378137 / 2.0
        self._substation_border_repo = SubstationBorderRepo(self._substation_borders_file_path)
        self._fetcher = OSMDataFetcher()
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
    
    def fetch_substations_within_border(self, border_geom):
        if border_geom.geom_type == 'Polygon':
            data = self._fetcher.get_substations_by_polygons(border_geom)
        elif border_geom.geom_type == 'MultiPolygon':
            largest_polygon = max(border_geom, key=lambda poly: poly.area)
            data = self._fetcher.get_substations_by_polygons(largest_polygon)
        else:
            raise ValueError("Unsupported geometry type")
        
        features = data.get('features', [])

        print(f"Fetched {len(features)} substations.")
        return features
    
    def select_substation(self, substations):
        print("Selecting substation...")

        if len(substations) == 1:
            return substations[0]
        
        def lev(str1, str2):
            return fuzz.ratio(str1, str2)
        
        for substation in substations:
            print("Substation properties:", substation['properties'])

            if isinstance(substation, dict) and 'properties' in substation:
                operator = substation['properties'].get('operator', '').strip()
                for key, values in operator_map.items():
                    if any(lev(operator, value) < 6 for value in values):
                        print(f"Selected substation: {substation}")
                        return substation
            else:
                return substations[0]
        raise ValueError("No substation found")
    

    def build_grid(self, border_id):
        polygon = self._substation_border_repo.fetch_substation_border(border_id)

        substations_in_polygon = self.fetch_substations_within_border(polygon)
        substation = self.select_substation(substations_in_polygon)
        print(f"Original substation geometry: {substation['geometry']}")

        # substation_coords = substation['geometry']['coordinates'] # substation_coords must be the centroid of the current substation coordinates
    
         # Convert the substation's geometry to a Shapely object to compute the centroid
        substation_shape = shape(substation['geometry']) 
        substation_centroid = substation_shape.centroid
    
        # Extract the coordinates of the centroid
        substation_coords = (substation_centroid.x, substation_centroid.y)
    
        print(f"Calculated centroid: {substation_coords}")

        self.G = ox.graph_from_polygon(polygon, network_type='drive')

        if len(substation_coords):
            print(f"Substation found in selected area at centroid: {substation_coords}")
            X = []
            Y = []
            
            # Converting the centroid coordinates to meters
            x, y = self._lat_lon_to_meters(substation_coords[1], substation_coords[0])
            X.append(x)
            Y.append(y)

            building_data = self.get_buildings_data(polygon)
            
            Primary = PrimaryModel(self.G, substation_coords)
            print("Building primary model")
            Primaries = Primary.build(self._offset, self._pole_distance, self._line_treshold)
            print("Primary model: ", Primaries)
            
            primary_positions = nx.get_node_attributes(Primaries, 'pos')


        # self.G = ox.graph_from_polygon(polygon, network_type='drive')

        # if len(substation_coords):
        #     print(f"{len(substation_coords)} Substations found in selected area")
        #     X = []
        #     Y = []

        #     for x, y in substation_coords:
        #         x, y = self._lat_lon_to_meters(y, x)
        #         X.append(x)
        #         Y.append(y)

        #     building_data = self.get_buildings_data(polygon)
            
        #     Primary = PrimaryModel(self.G, substation_coords)
        #     print("Building primary model")
        #     Primaries = Primary.build(self._offset, self._pole_distance, self._line_treshold)
        #     print("Primary model: ", Primaries)
            
        #     primary_positions = nx.get_node_attributes(Primaries, 'pos')

            print("Building secondary model")
            Secondary = SecondaryModel(building_data, substation_coords)
            sec_data = Secondary.build(
                buildingsPerCluster=[self._buildings_per_cluster],
                HousesPerPole=[self._houses_per_pole]
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

                # self.plot_graph(self.complete_model)
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

    def plot_on_osm(self, G):
        # Convert the graph into GeoDataFrame
        gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)

        # Create a Folium map
        m = folium.Map(location=[39.9526, -75.1652], zoom_start=14)

        # Add the edges to the map
        for _, row in gdf_edges.iterrows():
            start = row['u']
            end = row['v']
            coords = [[G.nodes[start]['y'], G.nodes[start]['x']], [G.nodes[end]['y'], G.nodes[end]['x']]]
            folium.PolyLine(coords, color='blue', weight=2).add_to(m)

        # Save the map to an HTML file
        m.save('map.html')

    def button_clicked(self):
        if self.model_created:
            model_path = os.path.join(self._export_directory, f"{self._file_name}.gpickle")
            with open(model_path, 'wb') as f:
                pickle.dump(self.complete_model, f, pickle.HIGHEST_PROTOCOL)
            M = Model(
                Buildings=self.xfmr_mapping,
                Circuit=self._circuit_name,
                Model=self.complete_model,
                File=self._file_name,
                HV=self._hv_voltage,
                MV=self._mv_voltage,
                PC=self._primary_conductor,
                SC=self._secondary_conductor,
            )
            M.Write(self._export_directory, self._load_profiles)
            print("Model is valid")
        else:
            print("There is no model")
