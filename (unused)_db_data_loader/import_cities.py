import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine
from geoalchemy2 import WKTElement
import os

# Database connection settings
DB_URI = "postgresql+psycopg2://username:password@localhost:5432/trud"

def main():
    # Connect to the database
    engine = create_engine(DB_URI)
    
    # Create the cities table
    create_table_sql = """
    CREATE TABLE cities (
        id SERIAL PRIMARY KEY,
        region_city TEXT NOT NULL,
        population INTEGER,
        factories_total INTEGER,
        median_salary INTEGER,
        harsh_climate BOOLEAN,
        migrations_from_each_city FLOAT,
        ueqi_residential_current FLOAT,
        ueqi_street_networks_current FLOAT,
        ueqi_green_spaces_current FLOAT,
        ueqi_public_and_business_infrastructure_current FLOAT,
        ueqi_social_and_leisure_infrastructure_current FLOAT,
        ueqi_citywide_space_current FLOAT,
        geometry GEOMETRY(Point, 4326)
    );
    """
    with engine.connect() as connection:
        connection.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        connection.execute(create_table_sql)
    
    # Load the CSV data
    csv_path = "cities.csv"
    df = pd.read_csv(csv_path)

    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.GeoSeries.from_wkt(df['geometry']),
        crs="EPSG:4326"
    )

    # Add WKTElement for PostGIS
    gdf['geometry'] = gdf['geometry'].apply(lambda geom: WKTElement(geom.wkt, srid=4326))

    # Push data to PostgreSQL
    gdf.to_postgis("cities", engine, if_exists="replace", index=False)

    print("✅ Cities imported successfully!")

if __name__ == "__main__":
    main()