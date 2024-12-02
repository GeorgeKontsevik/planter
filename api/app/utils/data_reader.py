import pickle
import pandas as pd
import geopandas as gpd

ontology = pd.read_csv( 
    "api/app/data/ontology.csv",
    index_col=0,
)
grads = pd.read_pickle(
    "api/app/data/grouped_grads.pkl",
)
cv = pd.read_parquet("api/app/data/cv.gzip").rename(columns={"hh_name": "speciality"})
cities = gpd.read_parquet("api/app//data/cities.parquet")

with open(
    "api/app/data/model.pkl", "rb"
) as file:  # Открываем файл в бинарном режиме для чтения
    model = pickle.load(file)  # Загружаем модель


# with open(
#     "api/app/data/scaler_x.pkl", "rb"
# ) as file:  # Открываем файл в бинарном режиме для чтения
#     scaler_x = pickle.load(file)  # Загружаем модель
