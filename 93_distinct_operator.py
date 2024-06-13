from services.osm_data_fetcher import OSMDataFetcher
from services.osm_data_fetcher import names

osmDataFetcher = OSMDataFetcher()

distinct_operators = osmDataFetcher.get_distinct_operators('./repositories/italia_distribution_substations.csv')

# print(distinct_operators)

compared_operator = osmDataFetcher.compare_operators_with_names(distinct_operators, names)

print(f'compared operators: {compared_operator}')
