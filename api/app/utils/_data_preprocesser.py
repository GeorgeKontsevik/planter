from api.app.utils.data_reader import cv
from api.app.utils.data_reader import ontology
from api.app.utils.data_reader import grads
from api.app.utils.data_reader import cities
from api.app.utils.constants import YEAR

cv = cv[cv["year"] == YEAR]
cv = cv.merge(ontology[["speciality", "edu_group_code"]], on="speciality")
cv["type"] = "CV"
grouped_cv = (
    cv.groupby(["cluster_center", "region_city", "type", "edu_group_code"])["id_cv"]
    .count()
    .to_frame()
)
grads.dropna(subset="edu_group", inplace=True)
grouped_grads = (
    grads.groupby(["cluster_center", "region_city", "type", "edu_group_code"])[
        "graduates_per_year_forecast"
    ]
    .sum()
    .to_frame()
)
grouped_grads = grouped_grads.join(grouped_cv, how="outer")
grouped_grads["total"] = grouped_grads["graduates_per_year_forecast"].fillna(
    0
) + grouped_grads["id_cv"].fillna(0)

grouped_grads = grouped_grads.join(
    cities[["region_city", "population", "num_in_migration"]]
    .rename(columns={"region_city": "cluster_center"})
    .set_index("cluster_center"),
    how="left",
)

grouped_grads = (
    grouped_grads.reset_index(drop=False)
    .groupby(["cluster_center", "type"])[["total"]]
    .sum()
    .join(
        cities[["region_city", "population", "num_in_migration"]]
        .rename(columns={"region_city": "cluster_center"})
        .set_index("cluster_center"),
        how="left",
    )
)

grouped_grads.reset_index(drop=False, inplace=True)

grouped_grads = grouped_grads.merge(
    grouped_grads[grouped_grads["type"] != "CV"]
    .groupby("cluster_center")[["total"]]
    .sum()
    .rename(columns={"total": "edu_total"})
    .reset_index(),
    how="outer",
).fillna(0)

grouped_grads.to_pickle("../data/grouped_grads.pkl")

# uinput_industry = ["Добыча нефти и газа"]
# uinput_spec_num = {"Машинист": 200, "Оператор, аппаратчик": 300}
# uinput_spec_num_2 = dict()
# for k in uinput_spec_num.keys():
#     uinput_spec_num_2[k] = (
#         ontology.loc[ontology["speciality"] == k, "edu_group_id"]
#         .drop_duplicates()
#         .values
#     )
