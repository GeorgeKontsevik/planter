# %% [markdown]
# # НУЖНО ПОНЯТЬ НУЖНО ЛИ И МОЖНО ЛИ ВЗВЕШИВАТЬ
# # МИГРАЦИЮ В ГОРОД по специалистам в городе
# ### или не фильтровать а как-то менять их параметры МИГРАЦИИ В ГОРОД
# %%
import warnings
import geopandas as gpd
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
from skmob.models.gravity import Gravity
import skmob
import json
import numpy as np
import random
import shapely
import folium
from shapely.geometry import LineString
import pickle
from api.app.methods.methods_estimate.estimator import do_estimate

from fastapi import HTTPException
# Initialize pandarallel
# pandarallel.initialize(progress_bar=False)

# Suppress FutureWarning messages
# warnings.simplefilter(action="ignore", category=FutureWarning)

np.random.seed(0)
random.seed(0)

# %%
METRIC_CRS = 3857
DEGREE_CRS = 4326

DISTANCE_TRASHOLD_METERS=.75e6

POPULATION_WEIGHT_COEFF = 1
FACTORY_SALARY_W_COEFF = 3
CITY_PARAMS_W_COEFF = 3
BAD_CLIMATE_W_COEFF = 3

MIN_FLOW_VALUE = 1


"""
да тут правда странные коэффициенты
но мне кажется у меня есть объяснение почему
- птому что модель делает фит к тем данным которые есть и на них генерит
- данные ну такое да
- чтобы это как-то подружить здесь и далее применяются некоторые ходы
по манипуляции с данными, чтобы в итоге всё вместе выглядело норм.

- из минусов -- немного криво генерятся потоки в том плане что в среднем
значения около 115 чел. С другой стороны это вроде ок тк есть пусть и небольшое но существующее различие
между более сильными и более слабыми потоками (в целом как это и должно быть) 

(! ! !)
также тут в (для) для текущего проекта (!) сделано значительное допущение:
стоит ограничение на потоки (но уже после фита / расчета те происходит удаление потоков)
по расстоянию в 250 км -- с идеей показать только ближайшие взаимодействия

Тк именно в этом прокте важно смотреть такие взаимдействия и миграции условно
через пол страны в данном случае нет смысла смотреть тк проект не про это
"""
DESTINATION_EXP_COEFF = 5
ORIGIN_EXP_COEFF = 1
DETERRENCE_FUNC_COEFF = -1

# %%
cols = [
    "population",
    "factories_total",
    "median_salary",
    "ueqi_residential",
    "ueqi_street_networks",
    "ueqi_green_spaces",
    "ueqi_public_and_business_infrastructure",
    "ueqi_social_and_leisure_infrastructure",
    "ueqi_citywide_space",
    "harsh_climate",
]

cols_to_round = ["city_attractiveness_coeff", "population"]

# %%
def define_model():
    gravity = Gravity(
        deterrence_func_type="power_law",
        gravity_type="globally constrained",
        destination_exp=DESTINATION_EXP_COEFF,
        origin_exp=ORIGIN_EXP_COEFF,
        deterrence_func_args=[DETERRENCE_FUNC_COEFF],
    )

    return gravity


def drop_cities_no_population(df):
    assert "population" in df.columns, "population is not in df.columns"

    mask_not_empty_population_col = df["population"] > 0
    return df.loc[mask_not_empty_population_col, :]


def normalize_outflow_by_pop_mil(df):

    POPULATION_NORMALIZATION_VALUE = 1e6

    assert (
        "migrations_from_each_city" in df.columns and "population" in df.columns
    ), "migrations_from_each_city or population are not in df.columns"

    return df["migrations_from_each_city"] * (
        df["population"] / POPULATION_NORMALIZATION_VALUE
    )


def define_scaler():
    return MinMaxScaler()


def scale_cities_attrs(df, cols_to_scale, scaler, fit=True):
    """
    скейлить думаю тоже можно один раз
    потом сохранить скейлер и только для измененных параметров использовать
    """

    if fit:
        return scaler.fit_transform(
            df.loc[
                :,
                cols_to_scale,
            ]
        )

    else:
        df = df.T
        return scaler.transform(
            df.loc[
                :,
                cols_to_scale,
            ]
        )


def calculate_attractiveness(df):
    """
    это как будто тоже один раз и потом просто пересчитывать для одного города

    Почему вес/привлекательность так сделано? Взвешиваются отдельно фабрики-зарплаты, качества города и климат.
    + Я попробовал по-разному их взвешивать (и задавать различные значения для гравити-модели)
    и такая комюинация показала себя лучше всего. Можно считать это экспертной оценкой.
    """

    assert all(
        param in df.columns
        for param in [
            "factories_total",
            "median_salary",
            "ueqi_residential",
            "ueqi_green_spaces",
            "ueqi_public_and_business_infrastructure",
            "ueqi_social_and_leisure_infrastructure",
            "ueqi_citywide_space",
            "harsh_climate",
        ]
    )

    city_attractiveness_coeff = round(
        # POPULATION_WEIGHT_COEFF * df["population"]
        FACTORY_SALARY_W_COEFF
        * (df["factories_total"] + df["median_salary"])
        * CITY_PARAMS_W_COEFF
        + (
            +df["ueqi_residential"]
            + df["ueqi_street_networks"]
            + df["ueqi_green_spaces"]
            + df["ueqi_public_and_business_infrastructure"]
            + df["ueqi_social_and_leisure_infrastructure"]
            + df["ueqi_citywide_space"]
        )
        + (1 - df["harsh_climate"])
        # * BAD_CLIMATE_W_COEFF
        + 1,
        0,
    )

    return city_attractiveness_coeff


def filter_od_matrix_resetted(df):
    """
    вот это кстати можно и один раз сделать
    """

    assert all(param in df.columns for param in ["origin", "destination"])

    mask_od_origin_not_destination = df["origin"] != df["destination"]

    # mask_flow_not_supersmall = od_matrix_reset["flow"] > MIN_FLOW_VALUE
    return df.loc[mask_od_origin_not_destination, :]


def reset_od_matrix(od_matrix):
    """
    тоже можно делать один раз
    """
    # Reset index to have 'origin' as a column
    od_matrix_reset = od_matrix.reset_index()
    od_matrix_reset.rename(columns={"region_city": "origin"}, inplace=True)

    od_matrix_reset = pd.melt(
        od_matrix_reset, id_vars=["origin"], var_name="destination", value_name="flow"
    )

    return od_matrix_reset


def check_filter_cities_in_od_matrix(df, od_df):
    """
    тоже будто можно один раз сделать
    """
    assert "region_city" in df and all(
        param in od_df for param in ["origin", "destination"]
    )

    mask_cities_in_od = df["region_city"].isin(
        set(od_df["origin"].to_list() + od_df["destination"].to_list())
    )

    return df.loc[mask_cities_in_od, :]


def make_flow_df(od_df, df_with_od_geoms):
    """
    тоже можно делать один раз
    """
    fdf = skmob.FlowDataFrame(
        data=od_df,
        origin="origin",
        destination="destination",
        flow="flow",
        tessellation=df_with_od_geoms,
        tile_id="region_city",
    )

    return fdf


def fit_flow_df(fdf, gravity) -> None:
    gravity.fit(fdf, relevance_column="city_attractiveness_coeff")


def generate_flows(df, gravity):
    """
    генерирует таблицу с OD и потоком между

    !!! нужно пересчитыват какждый раз при изменении параметров города

    """
    try:
        assert all(
            param in df.columns
            for param in ["city_attractiveness_coeff", "region_city", "norm_outflow"]
        )
    except Exception as ex:
        raise AssertionError
    # df.to_pickle('api/app/df.pkl')
    try:
        
        fdf_fitted = gravity.generate(
            df,
            relevance_column="city_attractiveness_coeff",
            tot_outflows_column="norm_outflow",
            out_format="flows",
            tile_id_column="region_city",
        )
    except Exception as e:
        print('\n\n\n\n',e)

    return pd.DataFrame(fdf_fitted).sort_values(by=["flow", "destination"])


def inverse_scale_df(df, cols, scaler):
    return pd.DataFrame(scaler.inverse_transform(df.loc[:, cols]), columns=cols)


def tailor_geometries(gdf):
    GRID_SIZE = 0.001
    return shapely.set_precision(gdf["geometry"].array, grid_size=GRID_SIZE)


def post_processing(gdf: pd.DataFrame):

    assert all(attr in gdf.columns for attr in ["geometry", "flow"])

    MINIMAL_FLOW = 1e-20  # anything beyond is a noise
    MAXIMAL_FLOW = 3  # anything beyond is a noise
    # DISTANCE_TRASHOLD_METERS = (
    #     .75e6  # 250km as a max value for potential migration, exper evaluation
    # )
    # res["attr_diff"] = res["destination_attr"] - res["origin_attr"]
    gdf["distance"] = (
        gpd.GeoSeries(gdf["geometry"], crs=DEGREE_CRS).to_crs(METRIC_CRS).length
    )
    mask6 = (
        (gdf["distance"] < DISTANCE_TRASHOLD_METERS)
        & (gdf["flow"] > MINIMAL_FLOW)
        & (gdf["flow"] < MAXIMAL_FLOW)
    )
    gdf.loc[:, "big_flows"] = (np.log(gdf.loc[:, "flow"] + 5) ** 10).astype(
        int
    )  # some empirical constants
    gdf.loc[:, "scaled_flows_forvis"] = round(
        np.log(gdf.loc[:, "big_flows"]) / 1e2, 3
    )  # some empirical constants

    return gdf, mask6


def join_od_params(fdf_with_flows, cities):

    df_links = fdf_with_flows.merge(
        cities[["region_city", "city_attractiveness_coeff", "population"]].rename(
            columns={
                "region_city": "destination",
                "city_attractiveness_coeff": "destination_attr",
            }
        ),
        left_on="destination",
        right_on="destination",
    ).merge(
        cities[["region_city", "city_attractiveness_coeff"]].rename(
            columns={
                "city_attractiveness_coeff": "origin_attr",
                "region_city": "origin",
            }
        ),
        left_on="origin",
        right_on="origin",
    )

    return df_links


# Define the function that uses the pre-constructed dictionary
def create_linestring(row, geometry_dict):
    origin = row["origin"]
    destination = row["destination"]

    # Check if both origin and destination exist in the dictionary
    if origin in geometry_dict and destination in geometry_dict:
        return LineString([geometry_dict[origin], geometry_dict[destination]])
    return None


def make_od_linestring_geom(fdf_fitted_df, init_cities):
    """
    Геометрии ставятся один раз --- БРАТЬ ИЗ ФАЙЛА
    """

    # Create a dictionary that maps region cities to their geometries for faster access
    city_geometry_dict = init_cities.set_index("region_city")["geometry"].to_dict()
    # Apply the function in parallel
    return fdf_fitted_df.parallel_apply(
        lambda row: create_linestring(row, city_geometry_dict), axis=1
    )


def make_folium_map(gdf_links, cities, region_poly=None):
    assert all(
        attr in gdf_links.columns
        for attr in [
            "geometry",
            "scaled_flows_forvis",
            "origin",
            "destination",
            "big_flows",
        ]
    )

    assert isinstance(gdf_links, gpd.GeoDataFrame)
    assert isinstance(cities, gpd.GeoDataFrame)

    m = gdf_links[
        ["geometry", "scaled_flows_forvis", "origin", "destination", "big_flows"]
    ].explore(
        scheme="Percentiles",
        column="big_flows",
        cmap="Accent_r",
        style_kwds={
            "style_function": lambda feature: {
                "weight": (
                    feature["properties"]["scaled_flows_forvis"] + 1
                ),  # Set line width based on the attribute
                "opacity": 0.3,  # Adjust opacity if necessary
            }
        },
        control_scale=True,
        vmin=10,
        vmax=2.5e2,
        tiles="Cartodb dark_matter",
    )

    # Create a style function for circle markers
    def style_function(x, min_radius=1, max_radius=10):

        # Get the value for the chosen parameter
        flows_in_value = x["flows_in"]  # Default to 1 to avoid log(0) errors
        flows_out_value = x["flows_out"]  # Default to 1 to avoid log(0) errors

        # Compute the logarithmic value (base 10 or natural log)
        log_flows_in_value = np.sqrt(
            flows_in_value
        )  # Natural logarithm, you can use np.log10() for base 10

        # Compute the logarithmic value (base 10 or natural log)
        log_flows_out_value = np.sqrt(
            flows_out_value
        )  # Natural logarithm, you can use np.log10() for base 10

        # Normalize the log value to adjust the circle radius
        # Ensure the log value is scaled between min_radius and max_radius
        # marker_radius = min(max(flows_in_value, min_radius), max_radius)
        # border_radius = min(max(flows_out_value, min_radius), max_radius)

        return folium.CircleMarker(
            location=[x["geometry"].y, x["geometry"].x],
            radius=flows_in_value / 500,  # Adjust radius as needed
            # weight=log_flows_out_value / 5,
            popup=x[["region_city", "flows_in", "flows_out"]],
            fill=True,
            # fill_color="white",
            weight=1,
            color="white",
            opacity=1,  # Set border opacity
            fill_color="black",
            fill_opacity=0.01,
        ).add_to(m)

    # Apply the function to each feature in GeoJson
    cities.apply(lambda row: style_function(row), axis=1)

    # Create an HTML title element
    title_text = "Все потоки без разделения по профессиям"
    title_html = f"""
        <div style="
            position: fixed; 
            top: 10%;  
            left: 20%; 
            transform: translateX(-50%);
            background-color: transparent; 
            color: white; 
            font-size: 20px; 
            font-weight: bold;
            z-index: 1000;">
            {title_text}
        </div>
        """

    if isinstance(region_poly, gpd.GeoDataFrame):

        # Add the GeoDataFrame as a GeoJSON layer with borders only
        folium.GeoJson(
            region_poly.geometry.item().boundary,
            name="geojson",
            style_function=lambda feature: {
                "fillOpacity": 0,  # No fill
                # "fill_color": "yellow",
                "color": "white",  # Border color
                "weight": 0.4,  # Border thickness
            },
        ).add_to(m)

    # Add the title element to the map
    m.get_root().html.add_child(folium.Element(title_html))
    # Add layer control to toggle GeoJSON layer visibility
    folium.LayerControl().add_to(m)

    return m

# %%
class WorkForceFlows:
    def __init__(self):
        self.cols = [
            "population",
            "factories_total",
            "median_salary",
            "ueqi_residential",
            "ueqi_street_networks",
            "ueqi_green_spaces",
            "ueqi_public_and_business_infrastructure",
            "ueqi_social_and_leisure_infrastructure",
            "ueqi_citywide_space",
            "harsh_climate",
        ]
        self.cols_to_round = ["city_attractiveness_coeff", "population"]

        # Flag for tracking which stages need recalculation
        self.pipeline_stages = {
            1: False,
            2: False,
            3: False,
            4: False,
            5: False,
            6: False,
            7: False,
            8: False,
        }

        # Track initial state of cities
        self.initial_cities_state = None
        self.initial_links_state = None
        self.prev_cities_state = None  # Track the last saved state (for comparison)
        self.prev_links_state = None
        self.current_cities_state = None  # Track the current state of cities
        self.current_links_state = None
        self.scaled_cities = None
        self.update_city_name = None
        self.update_city_name_idx = None
        self.updated_city_params = None
        self.fdf = None
        self.od_linestrings = None

    def __getitem__(self, key):
        return getattr(self, key, f"Property '{key}' not found")

    def __setitem__(self, key, value):
        if hasattr(self, key):
            print("Warning: rewriting existing attribute")
        setattr(self, key, value)

    def save_initial_state(self):
        """Save the initial state of cities dataframe."""
        if self.initial_cities_state is None:
            self.initial_cities_state = self.cities.copy()
            self.initial_links_state = self.gdf_links.copy()
            print("Initial cities state saved.")

    def save_previous_state(self):
        """Save the previous state of cities dataframe."""
        self.prev_cities_state = self.cities.copy()
        self.prev_links_state = self.gdf_links.copy()

    def save_current_state(self):
        """Save the previous state of cities dataframe."""
        self.current_cities_state = self.cities.copy()
        self.current_links_state = self.gdf_links.copy()

    def compare_city_states(self):
        """Compare two states of the cities DataFrame or any other DataFrame."""
        # You can compare the full dataframe or specific columns
        if hasattr(self, "current_cities_state") and hasattr(
            self, "initial_cities_state"
        ):
            diff_cities = self.current_cities_state[
                ["flows_in", "flows_out", "region_city", "geometry"]
            ].merge(
                self.initial_cities_state[
                    ["flows_in", "flows_out", "region_city"]
                ].rename(
                    columns={"flows_in": "flows_in_prev", "flows_out": "flows_out_prev"}
                )
            )

            diff_cities["in_diff"] = (
                diff_cities["flows_in"] - diff_cities["flows_in_prev"]
            )

            diff_cities["out_diff"] = (
                diff_cities["flows_out"] - diff_cities["flows_out_prev"]
            )

            diff_cities["in_out_diff"] = (
                diff_cities["in_diff"] - diff_cities["out_diff"]
            )

            # Set a threshold for filtering small fluctuations
            threshold = 3  # Adjust this value based on your data
            # Filter out points with 'in_out_diff' below the threshold
            mask_fluctuation = diff_cities["in_out_diff"].abs() <= threshold
            diff_cities.loc[mask_fluctuation, "in_out_diff"] = 0

            return diff_cities[
                ["region_city", "geometry", "in_out_diff", "in_diff", "out_diff"]
            ].to_crs(DEGREE_CRS)
        else:
            print("Both states must be DataFrame objects.")
            return False

    def compare_link_states(self):
        """Compare two states of the cities DataFrame or any other DataFrame."""
        # You can compare the full dataframe or specific columns
        if hasattr(self, "current_cities_state") and hasattr(
            self, "initial_links_state"
        ):
            diff_links = (
                self.initial_links_state[
                    [
                        "origin",
                        "destination",
                        "big_flows",
                        "geometry",
                        "scaled_flows_forvis",
                    ]
                ]
                .rename(columns={"big_flows": "init_flows"})
                .merge(
                    self.current_links_state[["origin", "destination", "big_flows"]],
                )
            )

            diff_links["big_flows"] = diff_links["big_flows"] - diff_links["init_flows"]

            # Set a threshold for filtering small fluctuations
            threshold = 3  # Adjust this value based on your data
            # Filter out points with 'in_out_diff' below the threshold
            mask_fluctuation = diff_links["big_flows"].abs() <= threshold
            diff_links.loc[mask_fluctuation, "big_flows"] = 0

            return diff_links.drop(columns=["init_flows"])
        else:
            print("Both states must be DataFrame objects.")
            return False

    def reset_state(self):
        """Reset to the initial state of cities."""
        if self.initial_cities_state is not None:
            self.cities = self.initial_cities_state.copy()
            print("Cities state reset to the initial state.")
        else:
            print("No initial state to reset to.")

    @classmethod
    def make_scaler(cls):
        cls.scaler = define_scaler()

    @classmethod
    def make_model(cls):
        cls.model = define_model()

    def mark_stage_dirty(self, stage_number):
        # Mark a stage and all subsequent stages as needing rerun
        for stage in range(stage_number, max(self.pipeline_stages.keys()) + 1):
            self.pipeline_stages[stage] = False

    def run_cities_pipeline_stage_1(self, force=False):
        if not force:
            if not self.pipeline_stages[1]:
                if hasattr(self, "cities"):
                    self.cities = drop_cities_no_population(self.cities)
                    self.cities["norm_outflow"] = normalize_outflow_by_pop_mil(self.cities)
                    self.pipeline_stages[1] = True
                    self.mark_stage_dirty(2)  # Mark later stages as needing rerun
                else:
                    warnings.warn("Please provide 'cities' data")
            else:
                print("Skipping: Stage 1 has already been run")
        else:
            if hasattr(self, "cities"):
                self.cities = drop_cities_no_population(self.cities)
                self.cities["norm_outflow"] = normalize_outflow_by_pop_mil(self.cities)
                self.pipeline_stages[1] = True
                self.mark_stage_dirty(2)  # Mark later stages as needing rerun
            else:
                warnings.warn("Please provide 'cities' data")

    def run_cities_pipeline_stage_2(self):
        if not self.pipeline_stages[2]:
            if hasattr(self, "cities"):
                self.init_cities = self.cities.copy().to_crs(DEGREE_CRS)
                self.init_cities["geometry"] = tailor_geometries(self.init_cities)
                self.pipeline_stages[2] = True
                self.mark_stage_dirty(3)  # Stage 3 depends on Stage 2
            else:
                warnings.warn("Please provide 'cities' data")
        else:
            print("Skipping: Stage 2 has already been run")

    def run_cities_pipeline_stage_3(self):
        if not self.pipeline_stages[3]:
            if hasattr(self, "cities") and hasattr(self, "od"):
                self.od_matrix_reset = reset_od_matrix(self["od"])
                self.od_matrix_reset = filter_od_matrix_resetted(self.od_matrix_reset)
                self.od_matrix_reset.reset_index(drop=True, inplace=True)
                # self.cities = check_filter_cities_in_od_matrix(
                #     self.cities, self.od_matrix_reset
                # )
                self.pipeline_stages[3] = True
                self.mark_stage_dirty(4)  # Stage 4 depends on Stage 3
            else:
                warnings.warn("Please provide 'cities' and 'od' data")
        else:
            print("Skipping: Stage 3 has already been run")

    def run_cities_pipeline_stage_4(self):
        if not self.pipeline_stages[4]:
            if hasattr(self, "cities") and hasattr(self, "scaler"):

                self.cities.loc[:, self.cols] = scale_cities_attrs(
                    self.cities, self.cols, self.scaler, fit=True
                )
                self.scaled_cities = self.cities.copy()
                self.cities["city_attractiveness_coeff"] = calculate_attractiveness(
                    self.cities
                )
                self.init_cities["city_attractiveness_coeff"] = self.cities[
                    "city_attractiveness_coeff"
                ].copy()

                self.pipeline_stages[4] = True
                self.mark_stage_dirty(5)  # Stage 5 depends on Stage 4
            else:
                warnings.warn("Please provide 'cities' data and a scaler")
        else:
            print("Skipping: Stage 4 has already been run")

    def run_cities_pipeline_stage_5(self):
        if not self.pipeline_stages[5]:
            if hasattr(self, "cities") and hasattr(self, "od_matrix_reset"):

                self.fdf = make_flow_df(self.od_matrix_reset, self.cities)
                self.cities.loc[:, self.cols] = inverse_scale_df(
                    self.cities, self.cols, self.scaler
                )
                self.cities.loc[:, self.cols_to_round] = self.cities.loc[
                    :, self.cols_to_round
                ].astype(int)
                self.pipeline_stages[5] = True
                self.mark_stage_dirty(6)  # Stage 6 depends on Stage 5
            else:
                warnings.warn("Please provide 'cities' and 'od_matrix_reset' data")
        else:
            print("Skipping: Stage 5 has already been run")

    def run_cities_pipeline_stage_6(self):
        if not self.pipeline_stages[6]:
            if hasattr(self, "fdf") and hasattr(self, "init_cities"):
                # fit_flow_df(self.fdf, self.model)  # Fit the model with flow data
                self.fdf_fitted_df = generate_flows(self.cities, self.model)
                self.pipeline_stages[6] = True
                self.mark_stage_dirty(7)  # Stage 7 depends on Stage 6
            else:
                warnings.warn("Please provide 'fdf' and 'init_cities' data")
        else:
            print("Skipping: Stage 6 has already been run")

    def run_cities_pipeline_stage_7(self):
        if not self.pipeline_stages[7]:
            if hasattr(self, "fdf_fitted_df") and hasattr(self, "init_cities"):
                self.od_linestrings = make_od_linestring_geom(
                    self.fdf_fitted_df, self.init_cities
                )
                self.fdf_fitted_df["geometry"] = self.od_linestrings
                self.pipeline_stages[7] = True
                self.mark_stage_dirty(8)  # Stage 8 depends on Stage 7
            else:
                warnings.warn("Please provide 'fdf_fitted_df' and 'init_cities' data")
        else:
            print("Skipping: Stage 7 has already been run")

    def run_cities_pipeline_stage_8(self):
        if not self.pipeline_stages[8]:
            if hasattr(self, "fdf_fitted_df") and hasattr(self, "init_cities"):
                self.df_links = join_od_params(self.fdf_fitted_df, self.cities)
                self.df_links, self.mask_distance_flow = post_processing(self.df_links)
                self.gdf_links = gpd.GeoDataFrame(
                    self.df_links[self.mask_distance_flow], crs=DEGREE_CRS
                )
                self.gdf_links["geometry"] = tailor_geometries(self.gdf_links)
                self.pipeline_stages[8] = True

                flows_grouped_out = (
                    (
                        self.gdf_links.drop(columns=["destination", "geometry"])
                        .groupby("origin")
                        .sum()
                        .reset_index(drop=False)
                    )
                    .loc[:, ["origin", "big_flows"]]
                    .rename(columns={"big_flows": "flows_out", "origin": "region_city"})
                )

                flows_grouped_in = (
                    (
                        self.gdf_links.drop(columns=["origin", "geometry"])
                        .groupby("destination")
                        .sum()
                        .reset_index(drop=False)
                    )
                    .loc[:, ["destination", "big_flows"]]
                    .rename(
                        columns={"big_flows": "flows_in", "destination": "region_city"}
                    )
                )

                self.cities = self.cities.merge(flows_grouped_in, how="left").merge(
                    flows_grouped_out, how="left"
                )

                self.save_initial_state()
                self.save_current_state()

            else:
                warnings.warn("Please provide 'fdf_fitted_df' and 'cities' data")
        else:
            print("Skipping: Stage 8 has already been run")

    # -----------------------------------------------------------------
    def run_cities_pipeline_stage_4_upd(self):
        self.run_cities_pipeline_stage_1(force=True)
        if not self.pipeline_stages[4]:
            if hasattr(self, "cities") and hasattr(self, "scaler"):
                if self.update_city_name:

                    self.scaled_cities.loc[self.update_city_name_idx, self.cols] = (
                        scale_cities_attrs(
                            self.cities.loc[self.update_city_name_idx, :].to_frame(),
                            self.cols,
                            self.scaler,
                            fit=False,
                        )
                    )

                    self.cities.loc[
                        self.update_city_name_idx, "city_attractiveness_coeff"
                    ] = calculate_attractiveness(
                        self.scaled_cities.loc[self.update_city_name_idx, :]
                        .to_frame()
                        .T
                    ).item()
                    print('\n\nAttr:', self.cities.loc[
                        self.update_city_name_idx, "city_attractiveness_coeff"
                    ])
                    self.pipeline_stages[4] = True
                    self.mark_stage_dirty(5)  # Stage 5 depends on Stage 4
            else:
                warnings.warn("Please provide 'cities' data and a scaler")
        else:
            print("Skipping: Stage 4 has already been run")

    def run_cities_pipeline_stage_5_upd(self):
        if not self.pipeline_stages[5]:
            if hasattr(self, "cities") and hasattr(self, "od_matrix_reset"):

                self.cities.loc[self.update_city_name_idx, self.cols_to_round] = (
                    self.cities.loc[
                        self.update_city_name_idx, self.cols_to_round
                    ].astype(int)
                )

                self.pipeline_stages[5] = True
                self.mark_stage_dirty(6)  # Stage 6 depends on Stage 5
            else:
                warnings.warn("Please provide 'cities' and 'od_matrix_reset' data")
        else:
            print("Skipping: Stage 5 has already been run")

    def run_cities_pipeline_stage_6_upd(self):
        if not self.pipeline_stages[6]:
            if hasattr(self, "fdf") and hasattr(self, "init_cities"):

                # fit_flow_df(self.fdf, self.model)  # Fit the model with flow data
                
                self.fdf_fitted_df = generate_flows(self.cities, self.model)
                # except Exception as ex:
                    # print('\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n',ex)

                self.pipeline_stages[6] = True
                self.mark_stage_dirty(7)  # Stage 7 depends on Stage 6
            else:
                warnings.warn("Please provide 'fdf' and 'init_cities' data")
        else:
            print("Skipping: Stage 6 has already been run")

    def run_cities_pipeline_stage_7_upd(self):
        if not self.pipeline_stages[7]:
            fitted_df = getattr(self, "fdf_fitted_df", None)
            if fitted_df is not None:
                # Use direct assignment to avoid unnecessary copies
                fitted_df["geometry"] = self.od_linestrings
                self.pipeline_stages[7] = True
                self.mark_stage_dirty(8)  # Marking stage 8 as dependent

            else:
                warnings.warn("Please provide 'fdf_fitted_df' and 'init_cities' data")
        else:
            print("Skipping: Stage 7 has already been run")

    def run_cities_pipeline_stage_8_upd(self):
        if not self.pipeline_stages[8]:
            fitted_df = getattr(self, "fdf_fitted_df", None)
            cities_df = getattr(self, "cities", None)

            if fitted_df is not None and cities_df is not None:
                self.df_links = join_od_params(fitted_df, cities_df)
                # Perform post-processing and get masks in a single step if possible
                self.df_links, self.mask_distance_flow = post_processing(self.df_links)

                # Create GeoDataFrame directly without reassignment
                self.gdf_links = gpd.GeoDataFrame(
                    self.df_links.loc[self.mask_distance_flow], crs=DEGREE_CRS
                )
                self.gdf_links["geometry"] = tailor_geometries(self.gdf_links)

                self.pipeline_stages[8] = True

                # Optimize groupby operations by using fewer temporary DataFrames
                flows_out = (
                    self.gdf_links.drop(columns=["destination", "geometry"])
                    .groupby("origin", as_index=False)["big_flows"]
                    .sum()
                    .rename(columns={"big_flows": "flows_out", "origin": "region_city"})
                )

                # Drop columns in place to minimize data copying
                if "flows_in" in cities_df.columns:
                    cities_df.drop(columns=["flows_in", "flows_out"], inplace=True)

                flows_in = (
                    self.gdf_links.drop(columns=["origin", "geometry"])
                    .groupby("destination", as_index=False)["big_flows"]
                    .sum()
                    .rename(
                        columns={"big_flows": "flows_in", "destination": "region_city"}
                    )
                )

                # Merge flows more efficiently
                self.cities = cities_df.merge(flows_in, how="left").merge(
                    flows_out, how="left"
                )

                self.save_current_state()

            else:
                warnings.warn("Please provide 'fdf_fitted_df' and 'cities' data")
        else:
            print("Skipping: Stage 8 has already been run")

    # -----------------------------------------------------------------

    def update_city_params(self, city_name, new_params):
        # Check if the city exists in the DataFrame

        self.save_previous_state()

        self.update_city_name = city_name
        self.updated_city_params = new_params
        

        if city_name in self.cities["region_city"].values:
            # Update the DataFrame for the specific city
            self.update_city_name_idx = self.cities[
                self.cities["region_city"] == city_name
            ].index.item()

            self.cities.loc[self.update_city_name_idx, new_params.keys()] = (
                [float(p) for p in new_params.values()]
            )
            print(f"Updated parameters for {city_name}")
            # Mark relevant stages as dirty
            self.mark_stage_dirty(
                4
            )  # Stage 4 needs rerunning after updating city params
        else:
            print(f"City {city_name} not found in the DataFrame.")

    def recalculate_after_update(self):
        """
        Updates city parameters and recalculates the pipeline from Stage 4 to Stage 8.

        :param city_name: Name of the city whose parameters need to be updated
        :param new_params: Dictionary of the new parameters to update the city with
        """

        # Step 2: Re-run necessary pipeline stages after update
        print("Recalculating after updating parameters")

        self.run_cities_pipeline_stage_4_upd()  # Recalculate Stage 4
        print('stage 4 done')
        self.run_cities_pipeline_stage_5_upd()  # Recalculate Stage 5
        print('stage 5 done')
        self.run_cities_pipeline_stage_6_upd()  # Recalculate Stage 6
        print('stage 6 done')
        self.run_cities_pipeline_stage_7_upd()  # Recalculate Stage 7
        print('stage 7 done')
        self.run_cities_pipeline_stage_8_upd()  # Recalculate Stage 8
        print('stage 8 done')

        print(f"Recalculation complete.")

    def to_pickle(self, filename):
        """Save the whole class instance to a pickle file."""
        with open(filename, "wb") as f:
            pickle.dump(self, f)
        print(f"Class instance saved to {filename}")

    @staticmethod
    def from_pickle(filename):
        """Load the class instance from a pickle file."""
        with open(filename, "rb") as f:
            instance = pickle.load(f)
        print(f"Class instance loaded from {filename}")
        return instance

#------------------------------------------------------------------
"""
TODO: REFACTOR
"""

import __main__
__main__.WorkForceFlows = WorkForceFlows

DEGREE_CRS = 4326
METRIC_CRS = 3857

import os
import pickle
import geopandas as gpd
import json

# Load or initialize WorkForceFlows
filename = "wff_1812.pkl"
directory = "api/app/data"


# Check if the file exists in the specified directory

if filename in os.listdir(directory):
    
    filepath = os.path.join(directory, 'scaler_wff1812.pkl')
    with open(filepath, "rb") as f:
        scaler_x = pickle.load(f)

    filepath = os.path.join(directory, 'gravity_wff.pkl')
    with open(filepath, "rb") as f:
        model_gravity = pickle.load(f)

    filepath = os.path.join(directory, 'cities.parquet')
    cities = gpd.read_parquet(filepath)

    filepath = os.path.join(directory, 'fdf_fitted1812.parquet')
    # fdf_fitted = gpd.read_parquet(filepath)

    
    filepath = os.path.join(directory, filename)
    wff = WorkForceFlows.from_pickle(filepath)
    
    wff['scaler'] = scaler_x
    wff['model'] = model_gravity
    # wff['fdf_fitted_df'] = fdf_fitted
    
else:
    raise FileNotFoundError(f"The file {filename} was not found in the directory {directory}.")


def get_initial_original_cities(wff, city_name):
    original_flows_mask = wff.gdf_links['destination'].isin([city_name])

    original_flows = wff.gdf_links[original_flows_mask]

    original_cities = wff.cities.to_crs(DEGREE_CRS).loc[wff.cities['region_city'].isin(original_flows['origin'])]  

    return original_cities, original_flows


def do_reflow(city_name, updated_params:dict=None, industry=None, specs=None, workforce_type=None,list_cities_names=None):
    wff['cities'] = cities
# %%
    try:
        """
        FIX THAT AREA THING
        """

        area = wff.initial_cities_state.loc[wff.initial_cities_state['region_city']==city_name, 'geometry'].to_frame().to_crs(METRIC_CRS).buffer(DISTANCE_TRASHOLD_METERS).item()

        # Update parameters and recalculate if needed
        if updated_params:
            city_mask = wff.cities["region_city"] == city_name
            wff.update_city_params(city_name, updated_params)
            wff.recalculate_after_update()
            new_city_val = wff.cities.loc[city_mask,["flows_in", "flows_out"]].values.tolist()
            
            city_spec_new = new_city_val[0][0] / new_city_val[0][1]

            # Generate differences
            diff = wff.compare_city_states()
            diff_links = wff.compare_link_states()

            mask_links = diff_links["big_flows"] > 0
            mask_links2 = diff_links['destination'] == city_name
            links_diff = diff_links[mask_links & mask_links2]
            
            # print(diff, diff_links[mask_links & mask_links2].iloc[:,:])

            # Apply masks and save GeoJSONs
            # mask2 = diff['region_city'].isin(links_diff['destination'])
            cities_diff = links_diff.loc[:,['origin', 'big_flows']]
            cities_diff['big_flows']*=-1
            cities_diff.rename(columns={'origin':'region_city', 'big_flows':'in_out_diff'}, inplace=True)

            # Apply masks and save GeoJSONs
            mask2 = diff['region_city'].isin(links_diff['origin'])
            cities_diff_ret = diff[mask2].dropna()
            

            links_diff = links_diff[(links_diff['origin'].isin(cities_diff_ret['region_city'])) \
                                    & (links_diff['destination'].isin([city_name]))]

            for col in cities_diff.columns:
                try:
                    cities_diff[col] = cities_diff[col].round(0).astype(int)
                except Exception as ex:
                    print(ex,'__int')
                    # pass
            
            for v in new_city_val:
                for k in v:
                    try:
                        k = int(k)
                    except Exception:
                        pass

            for k,v in updated_params.items():
                try:
                    # print(v)
                    v = int(round(v))
                    # print(v)
                    updated_params[k] = v
                except Exception:
                    pass

            try:
                del updated_params['population']
            except Exception:
                pass


            original_flows_mask = wff.gdf_links['destination'].isin([city_name])


            original_flows = wff.gdf_links[original_flows_mask]


            original_cities = wff.cities.loc[wff.cities['region_city'].isin(original_flows['origin'].tolist() + [city_name])].to_crs(METRIC_CRS)

            # print('ORIGINAL', original_cities)

            original_cities=original_cities[original_cities['geometry'].within(area)]

            cities_diff = cities_diff[cities_diff['region_city'].isin(original_cities['region_city'])]


            # mask_links = diff_links["big_flows"] > 0
            # mask_links2 = diff_links['origin'] == city_name
            # links_diff = diff_links[mask_links & mask_links2]

            closest_cities = original_cities.merge(cities_diff[['region_city', 'in_out_diff']], on='region_city', how='left')[['region_city', 'in_out_diff', 'factories_total']]

            val =abs(closest_cities.loc[closest_cities['region_city']!=city_name, 'in_out_diff'].sum()*-1 - links_diff['big_flows'].sum())

            closest_cities.loc[closest_cities['region_city']==city_name, 'in_out_diff'] = val


            # print(closest_cities.loc[closest_cities['region_city']==city_name, 'in_out_diff'])

            
            # print(updated_params, new_city_val)
            # print('\n\n\n\nGO\n\n\n\n',original_cities.merge(cities_diff[['region_city', 'in_out_diff']], on='region_city', how='right'))
            # print(list_cities_names,'\n', cities_diff[['region_city', 'in_out_diff']], original_cities, '\n', original_cities[original_cities['region_city'].isin(list_cities_names)].merge(cities_diff[['region_city', 'in_out_diff']], on='region_city', how='left'))
            # print(original_cities[['region_city', 'factories_total']])
            # print(cities_diff_ret)
            cities_diff_ret = cities_diff_ret[cities_diff_ret['region_city'].isin(original_cities['region_city'])]

            try:
                params, plant_assessment_val, estimate, estimate_city_prov = do_estimate(
                    uinput_spec_num=specs,
                    uinput_industry=industry,
                    closest_cities=closest_cities, workforce_type=workforce_type, list_cities_names=list_cities_names, city_name=city_name, city_spec_new=city_spec_new)
                # print(original_cities.columns)
                # original_cities=gpd.GeoDataFrame(original_cities, geometry='geometry') 
                # original_cities=original_cities[original_cities['geometry'].within(area)]

            except Exception as ex:
                print(ex, '___do_estimate')
                raise ex
            # print(plant_assessment_val, cities_diff)
            # original_cities = original_cities['region_city'].isin(original_flows['origin'])
    
            # updated_params['estimate'] = 0


            original_cities2 = original_cities.merge(params.drop(columns=['region_city']), left_on='region_city', right_on='cluster_center', how='left').set_index('region_city').fillna(0)

            # Step 2: Group by 'region_city' and aggregate specialists and their values into dictionaries
            original_cities = original_cities.merge(original_cities2.groupby('region_city').apply(
                lambda x: {
                    row['specialty']: {
                        'prov_graduates': row['prov_graduates'],
                        'prov_specialists': row['prov_specialists'],
                        'total_graduates': row['total_graduates'],
                        'total_specialists': row['total_specialists'],
                        'all': row['total_specialists'] + row['total_graduates']
                    } for _, row in x.iterrows()
                }
            ).reset_index(name='specialists_data'), on='region_city')

            original_cities.drop(columns=['estimate'], inplace=True)
            try:
                original_cities = original_cities.merge(original_cities2.groupby('region_city')[['prov_specialists', 'prov_graduates']].mean().mean(axis=1).to_frame().round(2), on='region_city').rename(columns={0:'estimate'})
            except Exception as ex:
                print(ex)


            # Calculate the average
            city_spec_new = new_city_val[0][0] / new_city_val[0][1]

            # print(plant_assessment_val.keys())
            for k,v in plant_assessment_val.items():
                # print(k,v)
                for kk, vv in v.items():
                    if 'total' in kk:
                        plant_assessment_val[k][kk] = int(round(vv))
                    if 'prov' in kk:
                        plant_assessment_val[k][kk] = round(vv,3)

            # # print(plant_assessment_val)
            # for k,v in specs:
            #     pass
            # est = []
            import numpy as np
            # print(estimate)
            # for p in estimate:
                # print(p)
            updated_params['estimate']=estimate_city_prov

            # print('\n\n\n\n\n',
            #     {"updated_params": updated_params,
            #     "updated_in_out_flow_vals": new_city_val,
            #     'plant': plant_assessment_val,
            #     'plant_total': calculate_average_prov(plant_assessment_val),
            #     'city_spec_new':city_spec_new}
            # )

            # print(cities_diff_ret)
            # print(new_city_val)
            # print(estimate)
            from pprint import pprint
            pprint(plant_assessment_val)
            print(estimate_city_prov)

            return {
                "cities_diff": json.loads(cities_diff_ret.to_json()),
                "links_diff": json.loads(links_diff.to_json()),
                "updated_params": updated_params,
                "updated_in_out_flow_vals": new_city_val,
                'plant': plant_assessment_val,
                'plant_total': estimate,
                'city_spec_new':city_spec_new
            }

        # Return original flows without updates
        else:
            # print(area)
            
            original_cities, original_flows = get_initial_original_cities(wff, city_name)
            

            for col in original_cities.columns:
                try:
                    original_cities[col] = original_cities[col].round(0).astype(int)
                except Exception:   
                    pass
            
            original_cities.drop(columns=['h3_index', 'median_salary', 'num_in_migration',
       'estimate', 'norm_outflow', 'city_attractiveness_coeff',
       'flows_in', 'flows_out'], inplace=True)
            # print(original_cities.columns)

            return {"cities_diff": json.loads(original_cities.to_json()),
                    'links_diff': json.loads(original_flows.to_json()),}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)+'___workflow')
    