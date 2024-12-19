import geopandas as gpd
import pandas as pd
import numpy as np
from typing import List
from math import ceil

# uinput_industry -- input industry
# uinput_spec_num -- input dict of specs and their num

# grouped_cv -- main data
# ontology -- industry-specialiy matching
# cities -- just to filter


# --- START ---
"""
Эта штука завязана на входных профессиях и индустрии,
поэтому нужно каждый раз пересчитывать -- мб можно оптимизировать и пересчитывать только часть
но имхо оно и так быстро
"""




def do_estimate(
    uinput_spec_num: List[dict], uinput_industry: str, closest_cities, workforce_type=None) -> pd.DataFrame:
    """
    Perform competitor analysis and enrich the grouped_grads DataFrame with competitor-related metrics.

    Args:
        uinput_spec_num (dict): User input mapping specialties to their respective numbers.
        uinput_industry (str): The target industry for the analysis.
        ontology (pd.DataFrame): DataFrame containing information about specialties and industries.
        cities (pd.DataFrame): DataFrame containing city data.
        grouped_grads (pd.DataFrame): DataFrame containing graduate and city metrics.

    Returns:
        pd.DataFrame: Enriched grouped_grads DataFrame with additional metrics.
    """
    initial_cities = closest_cities.copy()

    cv = pd.read_parquet('api/app/data/cv.gzip').rename(
        columns={"hh_name": "specialty"})
    ontology = pd.read_pickle("api/app/data/new_ontology.pkl")

    grouped_grads = pd.read_pickle("api/app/data/grouped_grads.pkl")

    uinput_spec_num_0 = dict()

    try:
        for k in uinput_spec_num:
            uinput_spec_num_0[k['specialty'].value] = k['count']
    except Exception:
        for k in uinput_spec_num:
            uinput_spec_num_0[k['specialty']] = k['count']


    uinput_spec_num = uinput_spec_num_0
    # print('\n\n\n\n', uinput_spec_num)
    YEAR = 2021
    cv = cv[cv["year"] == YEAR]

    uinput_spec_num_2 = {}
    competitor_industries = []
    competitor_fatories = []

    city_names = closest_cities["region_city"].values

    mask = grouped_grads.reset_index(drop=False).loc[:, "cluster_center"].isin(city_names)
    grouped_grads = (
        grouped_grads.reset_index(drop=False)
        .loc[mask, :]
        .set_index(["cluster_center", "region_city", "type", "edu_group_code"])
    )

    mask = cv["region_city"].isin(city_names)
    cv = cv[mask]

    # %%
    ontology.rename(columns={'speciality': 'specialty'}, inplace=True)
    cv = cv.merge(ontology[["specialty", "edu_group_code"]], on="specialty")
    cv["type"] = "CV"
    # --- START ---
    """
    Эта штука завязана на входных профессиях и индустрии,
    поэтому нужно каждый раз пересчитывать -- мб можно оптимизировать и пересчитывать только часть
    но имхо оно и так быстро
    """

    uinput_spec_num_2 = dict()
    competitor_industries = list()
    competitor_fatories = list()

    for k in uinput_spec_num:
        uinput_spec_num_2[k] = (
            ontology.loc[ontology["specialty"] == k, "edu_group_id"]
            .drop_duplicates()
            .values.tolist()
        )
        competitor_industries += (
            ontology.loc[ontology["specialty"] == k, "industry_code"]
            .drop_duplicates()
            .tolist()
            )
        
    # print('\n\n\n\n\n', uinput_spec_num_2)
    # --- START ---

    competitor_industries = set(competitor_industries)

    try:
        competitor_industries.remove(uinput_industry)
    except Exception:
        pass


    grad_col = []
    fact_col = []

    for col in closest_cities.columns:
        if "factor" in col in col:
            fact_col.append(col)

        if "factor" in col and any(industry in col for industry in competitor_industries):
            competitor_fatories.append(col)

        if "grad" in col in col:
            grad_col.append(col)

    closest_cities["competitors_factories_num"] = closest_cities[competitor_fatories].sum(axis=1)

    # print(competitor_industries)
    # print(grad_col, fact_col, competitor_fatories)

    # %%
    # uinput_spec_num_2

    # %%
    groups = []

    for k, v in uinput_spec_num_2.items():
        groups += v

    # %%
    groups = set(groups)

    # print('\n',groups, '\n')

    # %%
    # groups

    # %%
    cv.drop_duplicates(subset=["specialty", "edu_group_code"])

    # %%
    # grouped_grads

    # %%
    grouped_grads.reset_index(drop=False, inplace=True)
    mask_groups = grouped_grads["edu_group_code"].isin(groups)
    grouped_grads = grouped_grads[mask_groups]

    # print(grouped_grads.head().iloc[:,2:])

    # %%
    # grouped_grads

    # %%
    # grouped_grads.loc[grouped_grads["type"] == "ВПО"]
    grouped_grads.rename(columns={'id_cv':'cv_count'}, inplace=True)

    # %%
    grouped_grads.loc[grouped_grads["type"] == "ВПО", "type"] = "graduates"
    grouped_grads.loc[grouped_grads["type"] == "СПО", "type"] = "graduates"
    grouped_grads.loc[grouped_grads["type"] == "CV", "type"] = "specialists"

    grouped_grads = (
        grouped_grads.set_index("cluster_center")
        .groupby(["cluster_center", "type", "edu_group_code"])[
            ["city_capacity_grads_and_cv_sum", "graduates_per_year_forecast", "cv_count"]
        ]
        .sum()
        .join(
            closest_cities[
                ["region_city", "population"]
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

    # grouped_grads

    # %%
    # grouped_grads["working_population"] = (
    #     (grouped_grads["population"] * 0.65).round(0).astype(int)
    # )
    # print(grouped_grads)

    grouped_grads.drop(columns=["population"], inplace=True)

    grouped_grads = grouped_grads.drop(
        columns=[
            "city_capacity_grads_and_cv_sum",
            # "num_in_migration",
            # "working_population",
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
    # uinput_spec_num

    # %%
    # uinput_spec_num_2

    # # %%
    # plant_attr_coef

    # %%
    # grouped_grads
    # print(grouped_grads.head(3))
    # %%
    # Шаг 1: Создание нового столбца 'specialty' на основе словаря
    def map_specialty(edu_code):
        specialties = []  # Create a list to collect specialties
        for specialty, codes in uinput_spec_num_2.items():
            if edu_code in codes:
                specialties.append(specialty)  # Append to list if found
        return specialties if specialties else ['Другое']  # Return 'Другое' if no specialties found

    # Apply the function to get a column of lists
    grouped_grads['specialty'] = grouped_grads['edu_group_code'].apply(map_specialty)

    # Now explode the DataFrame to create new rows for each specialty
    grouped_grads = grouped_grads.explode('specialty').reset_index(drop=True)

    # Output the modified DataFrame
    # print(grouped_grads)

    # Шаг 2: Группировка по cluster_center и specialty для подсчета выпускников и специалистов
    result = grouped_grads.groupby(['cluster_center', 'specialty']).agg({
        'grads': 'sum',        # Сумма выпускников
        'cv_count': 'sum'      # Сумма специалистов
    }).reset_index()

    # print(result)

    # Шаг 3: Переименование столбцов для ясности
    result.rename(columns={'grads': 'total_graduates', 'cv_count': 'total_specialists'}, inplace=True)


    # %%
    # uinput_spec_num

    # %%
    # Инициализируем колонки числовыми значениями
    result['prov_graduates'] = pd.NA  # Используем Pandas NA
    result['prov_specialists'] = pd.NA

    # Проверяем ключи и значения
    # print("Словарь uinput_spec_num:")
    # print(uinput_spec_num)

    # print("\nУникальные специальности:")
    if 'in_out_diff' in initial_cities.columns:
        # print(result, initial_cities)
        reres = result.merge(initial_cities[['region_city', 'in_out_diff']], left_on='cluster_center', right_on='region_city')

        reres['total_specialists'] += reres['in_out_diff']
        reres.loc[reres['total_specialists'] < 0, 'total_specialists'] = 0
        result = reres

        # print("\n\n\n\n\nRERES\n\n\n\n", reres)

    # Выполняем расчеты
    for spec in result['specialty'].unique():
        if spec in uinput_spec_num:
            factor = uinput_spec_num[spec]
            # print(f"\nОбработка специальности '{spec}' с коэффициентом {factor}")
            
            
            # Логика расчета
            grads_values = result.loc[result['specialty'] == spec, 'total_graduates'].fillna(0) / factor
            specialists_values = result.loc[result['specialty'] == spec, 'total_specialists'].fillna(0) / factor
            
            # Устанавливаем значения напрямую
            result.loc[result['specialty'] == spec, 'prov_graduates'] = round(grads_values,2)
            result.loc[result['specialty'] == spec, 'prov_specialists'] = round(specialists_values,2)
        else:
            print(f"Специальность '{spec}' не найдена в словаре.")
    # print(result)
    # Проверяем итоговый результат
    # print("\nИтоговый DataFrame:")
    # print(result[['specialty', 'total_graduates', 'total_specialists', 'prov_graduates', 'prov_specialists']])

    # %%

    # Проверяем и обновляем значения в 'prov_graduates'
    result['prov_graduates'] = np.where(result['prov_graduates'] > 1, 1, result['prov_graduates'])

    # Проверяем и обновляем значения в 'prov_specialists'
    result['prov_specialists'] = np.where(result['prov_specialists'] > 1, 1, result['prov_specialists'])

    # %%
    plant_assessment_val = dict()
    for spec in uinput_spec_num:
        plant_assessment_val[spec] = dict()

        plant_assessment_val[spec]['prov_graduates'] =result.loc[  result['specialty']==spec, 'prov_graduates'].sum()

        plant_assessment_val[spec]['prov_specialists'] =  result.loc[result['specialty']==spec, 'prov_specialists'].sum()

        plant_assessment_val[spec]['total_graduates'] =   result.loc[ result['specialty']==spec, 'total_graduates'].sum()

        plant_assessment_val[spec]['total_specialists'] = result.loc[result['specialty']==spec, 'total_specialists'].sum()

        if plant_assessment_val[spec]['prov_graduates']>1:
            plant_assessment_val[spec]['prov_graduates'] = 1

        if plant_assessment_val[spec]['prov_specialists']>1:
            plant_assessment_val[spec]['prov_specialists'] = 1

        if workforce_type:
            if workforce_type=='all':
                plant_assessment_val[spec]['all'] = ceil(plant_assessment_val[spec]['total_specialists'] + plant_assessment_val[spec]['total_graduates'])
            elif workforce_type=='graduates':
                plant_assessment_val[spec]['all'] = ceil(plant_assessment_val[spec]['total_graduates'])
            elif workforce_type=='specialists':
                plant_assessment_val[spec]['all'] = ceil(plant_assessment_val[spec]['total_specialists'])

    for col in result.columns:
        try:
            result[col] = round(result[col])
            result[col] = result[col].astype(int)
        except Exception:
            pass

    return result, plant_assessment_val