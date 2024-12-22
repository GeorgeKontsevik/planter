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
    uinput_spec_num: List[dict], uinput_industry: str, closest_cities, workforce_type=None, list_cities_names=None, city_name=None, city_spec_new=None, added_grads=0) -> pd.DataFrame:
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
    print(workforce_type)
    
    initial_cities = closest_cities.copy()

    # print('\n\n\n\n\n\n INITIAL CITIES\n\n\n\n\n',initial_cities)
    
    if list_cities_names:
        city_names=list_cities_names
    else:
        city_names = closest_cities["region_city"].values # суда новый список

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

    uinput_spec_num_2 = {}
    competitor_industries = []
    competitor_fatories = []

    # print('\n',city_names,'\n')
    mask = grouped_grads.reset_index(drop=False).loc[:, "region_city"].isin(city_names)
    grouped_grads = (
        grouped_grads.reset_index(drop=False)
        .loc[mask, :]
        .set_index(["cluster_center", "region_city", "type", "edu_group_code"])
    ).fillna(10)

    # print(grouped_grads)

    # %%
    ontology.rename(columns={'speciality': 'specialty'}, inplace=True)

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

    # %%
    groups = []

    for k, v in uinput_spec_num_2.items():
        groups += v

    groups = set(groups)

    # %%
    grouped_grads.reset_index(drop=False, inplace=True)
    mask_groups = grouped_grads["edu_group_code"].isin(groups)
    grouped_grads = grouped_grads[mask_groups]
    grouped_grads["id_cv"] = grouped_grads["id_cv"].fillna(10)

    grouped_grads.rename(columns={'id_cv':'cv_count'}, inplace=True)

    # %%
    grouped_grads.loc[grouped_grads["type"] == "ВПО", "type"] = "graduates"
    grouped_grads.loc[grouped_grads["type"] == "СПО", "type"] = "graduates"
    grouped_grads.loc[grouped_grads["type"] == "CV", "type"] = "specialists"

    # print('\n\n\n\n\n\n\n\n\nBEFORE JOIN', grouped_grads, closest_cities)
    grouped_grads = (
        grouped_grads.set_index("cluster_center")
        .groupby(["cluster_center", "type", "edu_group_code"])[
            ["city_capacity_grads_and_cv_sum", "graduates_per_year_forecast", "cv_count"]
        ]
        .sum()
        .join(
            closest_cities[
                ["region_city"]
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

    grouped_grads = grouped_grads.drop(
        columns=[
            "city_capacity_grads_and_cv_sum",
            # "num_in_migration",
            "factories_total",
        ]
    ).rename(columns={"graduates_per_year_forecast": "grads"})

    # print(grouped_grads)

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

    # Output the modified DataFram
    # print(grouped_grads)
    # Шаг 2: Группировка по cluster_center и specialty для подсчета выпускников и специалистов

    

    result = grouped_grads.groupby(['cluster_center', 'specialty']).agg({
        'grads': 'sum',        # Сумма выпускников
        'cv_count': 'sum'      # Сумма специалистов
    }).reset_index()

    # print(result.loc[result['cluster_center']==city_name])

    if city_name:
        for specialty, _ in uinput_spec_num_2.items():
            if specialty not in result.loc[result['cluster_center']==city_name, 'specialty']:
                new_row = pd.DataFrame({
                    'cluster_center': [city_name],
                    'specialty': specialty,
                    'grads': added_grads,
                    # 'grads': result.loc[(result['cluster_center']==city_name)&(result['specialty']==specialty), 'grads'].item(),
                    'cv_count': 10
                })

                # Concatenate the original DataFrame with the new rows
                result = pd.concat([result, new_row], ignore_index=True)


    # Шаг 3: Переименование столбцов для ясности
    result.rename(columns={'grads': 'total_graduates', 'cv_count': 'total_specialists'}, inplace=True)

    # print(result.loc[result['cluster_center']==city_name])

    if list_cities_names:
        result = result[result['cluster_center'].isin(list_cities_names)]
        # print(result)


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
    #     # print(result, initial_cities)
        result = result.merge(initial_cities[['region_city', 'in_out_diff']], left_on='cluster_center', right_on='region_city')

    #     reres['total_specialists'] += reres['in_out_diff']
    #     reres.loc[reres['total_specialists'] < 0, 'total_specialists'] = 0
        

    #     # print("\n\n\n\n\nRERES\n\n\n\n", result,initial_cities, reres)
    #     result = reres

    result.loc[result['cluster_center']==city_name, 'total_specialists'] *= city_spec_new

    

    # Выполняем расчеты
    for spec in result['specialty'].unique():
        if spec in uinput_spec_num:
            factor = uinput_spec_num[spec]
            # print(f"\nОбработка специальности '{spec}' с коэффициентом {factor}")
            
            
            # Логика расчета
            grads_values = result.loc[result['specialty'] == spec, 'total_graduates'].fillna(10) / factor
            specialists_values = result.loc[result['specialty'] == spec, 'total_specialists'].fillna(10) / factor
            
            # Устанавливаем значения напрямую
            result.loc[result['specialty'] == spec, 'prov_graduates'] = round(grads_values,2)
            result.loc[result['specialty'] == spec, 'prov_specialists'] = round(specialists_values,2)
        else:
            print(f"Специальность '{spec}' не найдена в словаре.")
    # print(result)
    # Проверяем итоговый результат
    

    # %%

    # Проверяем и обновляем значения в 'prov_graduates'
    result['prov_graduates'] = np.where(result['prov_graduates'] > 1, 1, result['prov_graduates'])

    # Проверяем и обновляем значения в 'prov_specialists'
    result['prov_specialists'] = np.where(result['prov_specialists'] > 1, 1, result['prov_specialists'])

    # print(result[['specialty','total_graduates']].groupby('specialty').sum())
    # print(result['cluster_center'])
    # print(len(result['cluster_center']))
    # print(len(list_cities_names))

    estimate_city_prov = []
    print(result)

    # %%
    plant_assessment_val = dict()
    for spec in uinput_spec_num:
        # print(result.loc[(result['specialty']==spec) & (result['cluster_center']==city_name)])
        plant_assessment_val[spec] = dict()
        

        plant_assessment_val[spec]['prov_graduates'] =result.loc[  result['specialty']==spec, 'prov_graduates'].sum()

        plant_assessment_val[spec]['prov_specialists'] =  result.loc[result['specialty']==spec, 'prov_specialists'].sum()

        plant_assessment_val[spec]['total_graduates'] =   result.loc[ result['specialty']==spec, 'total_graduates'].sum()

        '''
        BUG FIX WORKAROUND
        '''
        # plant_assessment_val[spec]['total_graduates'] = 0

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

        estimate_city_prov.append(result.loc[(result['specialty']==spec) & (result['cluster_center']==city_name),['prov_graduates', 'prov_specialists']].mean().sum())

    for col in result.columns:
        try:
            result[col] = result[col].round(2)
            # result[col] = result[col].astype(int)
        except Exception:
            pass
    
    def calculate_average_prov(plant_assessment_val, workforce_type=None):
        prov_values = []
        print(plant_assessment_val)
        # Access the "plant" level

        for specialty in plant_assessment_val.values():
            prov_values2 = []
            for key, value in specialty.items():
                if key.startswith("prov_"):
                    print('prov____', workforce_type, key)
                    if workforce_type:
                        if workforce_type !='all' and workforce_type not in key:
                            continue
                    print(prov_values2, '_____')
                    prov_values2.append(value)
            
            value = sum(prov_values2)
            value = 1 if value>1 else value
            prov_values.append(value)
        
        # Calculate the average
        if prov_values:
            print(prov_values)
            avg_prov = sum(prov_values) / len(prov_values)
            avg_prov = 1 if avg_prov>1 else avg_prov
            return round(avg_prov,2)
        else:
            return None  # Return None or some indication if no prov values were found
    est = calculate_average_prov(plant_assessment_val, workforce_type)
    print(est)
    estimate_city_prov = 1 if round(np.mean(estimate_city_prov),2) > 1 else round(np.mean(estimate_city_prov),2)

    from pprint import pprint
    pprint(plant_assessment_val)
    print(est, estimate_city_prov)
    # print(result, plant_assessment_val)
    # print("\nИтоговый DataFrame:")
    # print(result[['specialty', 'total_graduates', 'total_specialists', 'prov_graduates', 'prov_specialists']])
    
    return result, plant_assessment_val, est, estimate_city_prov