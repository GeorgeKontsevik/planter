# import geopandas as gpd
from shapely.geometry import Point
import h3

from api.app.constants import (
    H3_RESOLUTION,
    HEX_SIZE_KM,
    CAR_SPEED_KMH,
)


# Define a function to convert lat/lon to H3 index at a specific resolution
def point_to_h3(point):
    return h3.geo_to_h3(point.y, point.x, H3_RESOLUTION)


# Function to find N closest cities using H3 k-ring
def find_n_closest_cities(
    point: Point,
    gdf_cities,
    search_radius_in_h,
):
    # Convert search_radius_in_h to kilometers
    search_radius_in_km = search_radius_in_h * CAR_SPEED_KMH

    n_hex_in_hours_accss = int(
        search_radius_in_km / HEX_SIZE_KM
    )  # Calculate the number of hexagons that fit in the distance

    # Convert the point to an H3 index
    point_h3 = point_to_h3(point)

    # Find nearby hexagons within a K-ring (radius in hexes)
    nearby_hexes_h3_index_list = h3.k_ring(
        point_h3, k=n_hex_in_hours_accss
    )  # Adjust 'k' for the search radius

    # Filter cities that fall within these hexagons
    selected_n_nearby_cities_gdf = gdf_cities[
        gdf_cities["h3_index"].isin(nearby_hexes_h3_index_list)
    ]

    cols_to_keep = [
        "region_city",
        "city_category",
        "population",
        "harsh_climate",
        "ueqi_score",
        "ueqi_residential",
        "ueqi_street_networks",
        "ueqi_green_spaces",
        "ueqi_public_and_business_infrastructure",
        "ueqi_social_and_leisure_infrastructure",
        "ueqi_citywide_space",
        "factories_total",
        "estimate",
        "h3_index",
        # "duration",
        "geometry",
    ]

    selected_n_nearby_cities_gdf = selected_n_nearby_cities_gdf.loc[:, cols_to_keep]

    # Return the N closest cities (no distance calculation, just based on H3 proximity)
    return selected_n_nearby_cities_gdf


# # Function to explore the point and nearby cities on an interactive map
# def explore_closest_cities(point, closest_cities):
#     # Find the N closest cities

#     # Create a GeoDataFrame for the target point
#     # gdf_point = gpd.GeoDataFrame(geometry=[point], crs=gdf_cities.crs)

#     # Create a base map centered on the point
#     m = folium.Map(location=[point.y, point.x], zoom_start=10)

#     # Add the target point to the map
#     folium.Marker(
#         [point.y, point.x], popup="Target Point", icon=folium.Icon(color="red")
#     ).add_to(m)

#     # Add the closest cities to the map
#     folium.GeoJson(closest_cities.to_crs(3857).buffer(5000).to_crs(4326)).add_to(m)
