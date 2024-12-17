# %%
import geopandas as gpd
import pandas as pd

pd.set_option("display.max_columns", 500)
pd.set_option("display.width", 1000)

# cities = gpd.read_feather(
#     "/Users/test/Documents/code/IL2/factory_loc_service/examples/closest_cities.feather"
# )
cities = gpd.read_parquet(
    "/Users/test/Documents/code/IL2/factory_loc_service/api/app/data/cities.parquet"
)

uinput_industry = "oil_and_gas_ext"
plant_attr_coef = 0.1
uinput_spec_num = {"Машинист": 200, "Оператор, аппаратчик": 300}
# city_names = cities["region_city"].values
city_names = [
    "Ростовская область, Азов",
    "Ростовская область, Аксай",
    "Ростовская область, Батайск",
    "Ростовская область, Белая Калитва",
    "Ростовская область, Зверево",
    "Ростовская область, Каменск-Шахтинский",
    "Ростовская область, Новочеркасск",
    "Ростовская область, Ростов-на-Дону",
    "Ростовская область, Таганрог",
    "Краснодарский край, Тихорецк",
    "Ростовская область, Шахты",
]

# %%
# print(uinput_industry, uinput_spec_num, city_names)

# %%
ontology = pd.read_pickle(
    "/Users/test/Documents/code/IL2/factory_loc_service/api/app/data/new_ontology.pkl"
)

grouped_grads = pd.read_pickle(
    "/Users/test/Documents/code/IL2/factory_loc_service/api/app/data/grouped_grads.pkl"
)

cv = pd.read_parquet("../api/app/data/cv.gzip").rename(
    columns={"hh_name": "speciality"}
)
YEAR = 2021
cv = cv[cv["year"] == YEAR]

# %%
mask = grouped_grads.reset_index(drop=False).loc[:, "cluster_center"].isin(city_names)
grouped_grads = (
    grouped_grads.reset_index(drop=False)
    .loc[mask, :]
    .set_index(["cluster_center", "region_city", "type", "edu_group_code"])
)

mask = cv["region_city"].isin(city_names)
cv = cv[mask]

# %%
# ontology = pd.read_csv(
#     "/Users/test/Documents/code/IL2/industrial-location/api/app/data/ontology.csv",
#     index_col=0,
# )

# ontology.loc[ontology["industry_code"] == "mining_oil_gas", "industry_code"] = (
#     "oil_and_gas_ext"
# )
# ontology.loc[ontology["industry_code"] == "mmining_coal_ores", "industry_code"] = (
#     "coal_and_metal_ext"
# )
# ontology.loc[ontology["industry_code"] == "mech_engineering", "industry_code"] = (
#     "machinery"
# )
# ontology.loc[ontology["industry_code"] == "shipbuilding", "industry_code"] = (
#     "shipbuilding"
# )
# ontology.loc[ontology["industry_code"] == "aircraft_engineering", "industry_code"] = (
#     "aircraft_and_space"
# )
# ontology.loc[ontology["industry_code"] == "non_ferrous_metallurgy", "industry_code"] = (
#     "nonferrous_metallurgy"
# )
# ontology.loc[ontology["industry_code"] == "ferrous_metallurgy", "industry_code"] = (
#     "ferrous_metallurgy"
# )
# ontology.loc[ontology["industry_code"] == "chemical", "industry_code"] = "chemicals"
# ontology.loc[ontology["industry_code"] == "pharma", "industry_code"] = "pharmacy"
# ontology.loc[ontology["industry_code"] == "electronics", "industry_code"] = (
#     "electronics"
# )

# %%
# ontology["industry_code"].unique()

# %%
# ontology.to_pickle("new_ontology.pkl")

# %%
cv = cv.merge(ontology[["speciality", "edu_group_code"]], on="speciality")
cv["type"] = "CV"
grouped_cv = (
    cv.groupby(["cluster_center", "region_city", "type", "edu_group_code"])["id_cv"]
    .count()
    .to_frame()
)
cv.head(3)

# %%
# grads = pd.read_csv("graduates.csv")
# grads.dropna(subset="edu_group", inplace=True)
# grouped_grads = (
#     grads.groupby(["cluster_center", "region_city", "type", "edu_group_code"])[
#         "graduates_per_year_forecast"
#     ]
#     .sum()
#     .to_frame()
# )
# grouped_grads = grouped_grads.join(grouped_cv, how="outer")
# grouped_grads["city_capacity_grads_and_cv_sum"] = grouped_grads[
#     "graduates_per_year_forecast"
# ].fillna(0) + grouped_grads["id_cv"].fillna(0)
# grouped_grads.to_pickle("grouped_grads.pkl")

# %%
# --- START ---
"""
Эта штука завязана на входных профессиях и индустрии,
поэтому нужно каждый раз пересчитывать -- мб можно оптимизировать и пересчитывать только часть
но имхо оно и так быстро
"""

uinput_spec_num_2 = dict()
competitor_industries = list()
competitor_fatories = list()


for k in uinput_spec_num.keys():
    uinput_spec_num_2[k] = (
        ontology.loc[ontology["speciality"] == k, "edu_group_id"]
        .drop_duplicates()
        .values.tolist()
    )
    competitor_industries += (
        ontology.loc[ontology["speciality"] == k, "industry_code"]
        .drop_duplicates()
        .tolist()
    )
# --- START ---

competitor_industries = set(competitor_industries)
competitor_industries.remove(uinput_industry)


grad_col = []
fact_col = []

for col in cities.columns:
    if "factor" in col and uinput_industry in col:
        fact_col.append(col)

    if "factor" in col and any(industry in col for industry in competitor_industries):
        competitor_fatories.append(col)

    if "grad" in col and uinput_industry in col:
        grad_col.append(col)

cities["competitors_factories_num"] = cities[competitor_fatories].sum(axis=1)

print(competitor_industries)
print(grad_col, fact_col, competitor_fatories)

# %%
uinput_spec_num_2

# %%
groups = []

for k, v in uinput_spec_num_2.items():
    groups += v

# %%
groups = set(groups)

# %%
groups

# %%
cv.drop_duplicates(subset=["speciality", "edu_group_code"])

# %%
grouped_grads

# %%
grouped_grads.reset_index(drop=False, inplace=True)
mask_groups = grouped_grads["edu_group_code"].isin(groups)
grouped_grads = grouped_grads[mask_groups]

# %%
grouped_grads

# %%
grouped_grads.loc[grouped_grads["type"] == "ВПО"]

# %%
grouped_grads.loc[grouped_grads["type"] == "ВПО", "type"] = "СПО"
grouped_grads.loc[grouped_grads["type"] == "СПО", "type"] = "graduates"
grouped_grads.loc[grouped_grads["type"] == "CV", "type"] = "specialists"

grouped_grads = (
    grouped_grads.set_index("cluster_center")
    .groupby(["cluster_center", "type", "edu_group_code"])[
        ["city_capacity_grads_and_cv_sum", "graduates_per_year_forecast", "cv_count"]
    ]
    .sum()
    .join(
        cities[
            ["region_city", "population", "num_in_migration"]
            + grad_col
            + fact_col
            + ["factories_total"]
            + ["competitors_factories_num"]
        ]
        .rename(columns={"region_city": "cluster_center"})
        .set_index("cluster_center"),
        how="left",
    )
)

grouped_grads

# %%
grouped_grads["working_population"] = (
    (grouped_grads["population"] * 0.65).round(0).astype(int)
)

grouped_grads.drop(columns=["population"], inplace=True)

grouped_grads = grouped_grads.drop(
    columns=[
        "city_capacity_grads_and_cv_sum",
        "num_in_migration",
        "working_population",
        "factories_total",
    ]
).rename(columns={"graduates_per_year_forecast": "grads"})

# %%
"""
Получается что миграции которые мы растим влияют только на кол-во резюме
Условимся что изначально у нас все находится в равновесии
Как только мы меняем что-то -- у нас кол-во резюме умножается на процент изменения входящей миграции (было 100 - стало 200 -- умножаем на 2)
"""

# %%
grouped_grads.loc[
    grouped_grads["competitors_factories_num"] == 0, "competitors_factories_num"
] = 1

# %%
grouped_grads["grads"] = (
    grouped_grads["grads"] / grouped_grads["competitors_factories_num"]
)
grouped_grads["cv_count"] = (
    grouped_grads["cv_count"] / grouped_grads["competitors_factories_num"]
)

# %%
grouped_grads.reset_index(inplace=True)

# %%
uinput_spec_num

# %%
uinput_spec_num_2

# %%
plant_attr_coef

# %%
grouped_grads

# %%
# Шаг 1: Создание нового столбца 'speciality' на основе словаря
def map_specialty(edu_code):
    for specialty, codes in uinput_spec_num_2.items():
        if edu_code in codes:
            return specialty
    return 'Другое'  # Если не нашли специальность

grouped_grads['speciality'] = grouped_grads['edu_group_code'].apply(map_specialty)

# Шаг 2: Группировка по cluster_center и speciality для подсчета выпускников и специалистов
result = grouped_grads.groupby(['cluster_center', 'speciality']).agg({
    'grads': 'sum',        # Сумма выпускников
    'cv_count': 'sum'      # Сумма специалистов
}).reset_index()

# Шаг 3: Переименование столбцов для ясности
result.rename(columns={'grads': 'total_graduates', 'cv_count': 'total_specialists'}, inplace=True)


# %%
uinput_spec_num

# %%
# Инициализируем колонки числовыми значениями
result['prov_graduates'] = pd.NA  # Используем Pandas NA
result['prov_specialists'] = pd.NA

# Проверяем ключи и значения
# print("Словарь uinput_spec_num:")
# print(uinput_spec_num)

# print("\nУникальные специальности:")
# print(result['speciality'].unique())

# Выполняем расчеты
for spec in result['speciality'].unique():
    if spec in uinput_spec_num:
        factor = uinput_spec_num[spec]
        # print(f"\nОбработка специальности '{spec}' с коэффициентом {factor}")
        
        # Логика расчета
        grads_values = result.loc[result['speciality'] == spec, 'total_graduates'].fillna(0) / factor
        specialists_values = result.loc[result['speciality'] == spec, 'total_specialists'].fillna(0) / factor
        
        # Устанавливаем значения напрямую
        result.loc[result['speciality'] == spec, 'prov_graduates'] = round(grads_values,2)
        result.loc[result['speciality'] == spec, 'prov_specialists'] = round(specialists_values,2)
    else:
        print(f"Специальность '{spec}' не найдена в словаре.")

# Проверяем итоговый результат
# print("\nИтоговый DataFrame:")
# print(result[['speciality', 'total_graduates', 'total_specialists', 'prov_graduates', 'prov_specialists']])

# %%
import numpy as np

# Проверяем и обновляем значения в 'prov_graduates'
result['prov_graduates'] = np.where(result['prov_graduates'] > 1, 1, result['prov_graduates'])

# Проверяем и обновляем значения в 'prov_specialists'
result['prov_specialists'] = np.where(result['prov_specialists'] > 1, 1, result['prov_specialists'])

# %%
result

# %%
"""
(!) Сейчас есть всё кроме непосредственной оценки (!)
А ну и задаваемое кол-во специалистов пока не учитывается
Но это следствие из отсутствия реализации расчета оценки

Эту таблицу практически в таком виде и планирую отдавать

Из того что обсуждали с СА:
условно выпускников взвесить по кол-ву предприятий тк их число ту мач большое
"""

# %%


# %%
# grouped_grads

# %%
""" ------------------------- FINISH HERE -------------------------------- """


