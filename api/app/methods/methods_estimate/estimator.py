import geopandas as gpd
import pandas as pd

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


def closest_city_params(
    uinput_spec_num: dict, uinput_industry: str, grouped_grads, ontology, cities
) -> pd.DataFrame:
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
    uinput_spec_num_2 = {}
    competitor_industries = []
    competitor_fatories = []

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

    # Remove the input industry from the competitors
    competitor_industries = set(competitor_industries)
    competitor_industries.discard(uinput_industry)

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

    # Enrich grouped_grads
    grouped_grads = (
        grouped_grads.reset_index(drop=False)
        .groupby(["cluster_center", "type"])[["city_capacity_grads_and_cv_sum", "count"]]
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

    grouped_grads[
        [
            "num_in_migration",
            "graduates_oil_and_gas_ext",
            "factories_oil_and_gas_ext",
            "factories_total",
            "city_capacity_grads_and_cv_sum",
            "population",
            "competitors_factories_num",
        ]
    ] = (
        grouped_grads[
            [
                "num_in_migration",
                "graduates_oil_and_gas_ext",
                "factories_oil_and_gas_ext",
                "factories_total",
                "city_capacity_grads_and_cv_sum",
                "population",
                "competitors_factories_num",
            ]
        ]
        .round(0)
        .fillna(0)
        .astype(int)
    )

    grouped_grads["working_population"] = (
        (grouped_grads["population"] * 0.65).round(0).astype(int)
    )

    return grouped_grads