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
result = fuzz.ratio("string1", "string2")  

def lev(str1, str2):
    return fuzz.ratio(str1, str2)


operator_map = {
    "AcegasApsAmga Spa": ['Acegas APS', 'Acegas Aps'],
    'AMAIE SPA': ['Aamaie'],
    'ARETI SPA': ['Areti'],
    "ASM Vercelli spa": [],
    'Assem SPA': ['Assem'],
    "Azienda Intercomunale Rotaliana Spa - SB": [],
    'AZIENDA RETI ELETTRICHE SRL': ['A2A', 'A2A Reti Elettriche'],
    "AZIENDA SPECIALIZZATA SETTORE MULTISERVIZI S.P.A.": [],
    "Dea Spa": [],
    "DEVAL": ['Deval'],
    "DISTRIBUZIONE ELETTRICA ADRIATICA SRL": [],
    'e-distribuzione S.p.A.': ['Enel Distribuzione S.p.a.', 'E-Distribuzione S.p.A.', 'Enel', 'EnelProduzione', 'ENEL', 'Enel Distribuzione SPA', 'Enel Distribuzione', 'e-distribuzione'],
    "EDYNA SRL": ['EDYNA'],
    "E.U.M. SOC. COOP. PER L'ENERGIA E L'AMBIENTE MOSO S.C.R.L.": ['Eum'],
    "INRETE Distribuzione Energia S.p.A.": ['INRETE S.p.A.'],
    'Terni Distribuzione Elettrica': ['ASM Terni'],
    'Ireti spa': ['IRETI'],
    "LD RETI S.R.L.": [],
    "RetiPiù Srl": [],
    "SECAB SOCIETÀ COOPERATIVA": [],
    "SET DISTRIBUZIONE": ['SET Distribuzione', 'Set Distribuzione', 'SET'],
    "Società Cooperativa Elettrica di Distribuzione Campo Tures": ['Azienda Comunale Campo Tures'],
    'Unareti S.p.A.': ['Unareti S.p.A.','Unareti'],
    'ASM Bressanone S.p.A.': ['ASM Bressanone Spa'],
    'V-RETI': [],
}

def fetch_substation_border(gpkg_file, border_id):
    print(f"Loading GeoPackage file {gpkg_file}...")
    gdf = gpd.read_file(gpkg_file, layer='primary_cabins')
    print(f"GeoDataFrame loaded with {len(gdf)} rows.")
    border = gdf[gdf['OBJECTID'] == border_id]
    if border.empty:
        raise ValueError(f"No border found with OBJECTID {border_id}")
    print(f"Border fetched: {border.geometry.iloc[0]}")
    return border.geometry.iloc[0]

def fetch_substations_within_border(border_geom):
    print(f"Fetching substations within border geometry of type {border_geom.geom_type}...")
    fetcher = OSMDataFetcher()
    if border_geom.geom_type == 'Polygon':
        data = fetcher.get_substations_by_polygons(border_geom)
    elif border_geom.geom_type == 'MultiPolygon':
        largest_polygon = max(border_geom, key=lambda poly: poly.area)
        data = fetcher.get_substations_by_polygons(largest_polygon)
    else:
        raise ValueError("Unsupported geometry type")
    
    features = data.get('features', [])
    print("Data fetched from OSM:", data)

    print(f"Fetched {len(features)} substations.")
    return features

def select_substation(substations, operator_map):
    print("Selecting substation...")
    for substation in substations:
        print("Substation properties:", substation['properties'])
        print("Operator being matched:", operator)

        if isinstance(substation, dict) and 'properties' in substation:
            operator = substation['properties'].get('operator', '').strip()
            for key, values in operator_map.items():
                if any(lev(operator, value) < 6 for value in values):
                    print(f"Selected substation: {substation}")
                    return substation
        else:
            print("Substation is not in the expected format or missing 'properties' key")
    raise ValueError("No suitable substation found")

def run_sing_algorithm(substation, border_geom, buildings_geojson):
    print(f"Running SING algorithm with substation {substation['id']}...")
    substations = [{
        'id': substation['id'],
        'latitude': substation['geometry'].y,
        'longitude': substation['geometry'].x
    }]
    
    sing_algorithm = model.Model(
        Buildings={},  # Replace with actual data
        Circuit="Circuit",
        Model="Model",
        File="File",
        HV=11,
        MV=0.4,
        PC="PCConductor",
        SC="SCConductor"
    )
    
    primary_cabin = PrimaryModel(border_geom, substations)
    secondary_cabin = SecondaryModel(substation['geometry'])
    request_handler = RequestHandler(buildings_geojson)

    result = sing_algorithm.run(primary_cabin, secondary_cabin, request_handler)
    print("SING algorithm result:", result)

    print("SING algorithm finished. Saving result...")
    with open('output.geojson', 'w') as f:
        json.dump(result, f)


def test_osm_fetcher():
    fetcher = OSMDataFetcher()
    # Replace with actual coordinates
    test_polygon = shape({'type': 'Polygon', 'coordinates': [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]]})
    data = fetcher.get_substations_by_polygons(test_polygon)
    print("Test data fetched:", data)

def main():
    print("Starting the process...")
    gpkg_file = './repositories/primary_cabins.gpkg'
    border_id = 124291  
    buildings_geojson = './repositories/primary_cabins.geojson'
    

    if not os.path.exists(gpkg_file):
        print(f"GeoPackage file does not exist: {gpkg_file}")

    if not os.path.exists(buildings_geojson):
        print(f"GeoJSON file does not exist: {buildings_geojson}")

    try:
        print(f"Fetching border geometry for ID {border_id}...")
        border_geom = fetch_substation_border(gpkg_file, border_id)
        print("Border geometry fetched.")
        print(f"Fetching substations within border...")
        substations = fetch_substations_within_border(border_geom)
        print("Substations fetched.")
        if not substations:
            raise ValueError("No substations found within the border")
        
        print(f"Selecting substation...")
        substation = select_substation(substations, operator_map)
        print("Substation selected.")
        print(f"Running SING algorithm...")
        run_sing_algorithm(substation, border_geom, buildings_geojson)
        
        print("Process completed successfully. Output saved to 'output.geojson'.")
    
    
    except Exception as e:
        print("An error occurred:")
        import traceback
        traceback.print_exc()




if __name__ == "__main__":
    main()