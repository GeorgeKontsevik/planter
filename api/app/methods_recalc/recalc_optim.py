import optuna
import numpy as np
import pandas as pd
from factory_loc_service.api.app.data_reader import model, cities, scaler_x
from factory_loc_service.api.app.constants import CITY_MODEL_PARAMS
from factory_loc_service.api.app.methods_recalc._model_preprocesser import preprocess_x
from functools import partial

# Assume you have a trained CatBoost model
# model = CatBoostRegressor()


def objective(
    trial,
    # target_migration,
    # target_migration,
    population,
    harsh_climate,
    ueqi_residential_current,
    ueqi_street_networks_current,
    ueqi_green_spaces_current,
    ueqi_public_and_business_infrastructure_current,
    ueqi_social_and_leisure_infrastructure_current,
    ueqi_citywide_space_current,
    median_salary_current,
):
    # Sample parameters using Optuna's suggested distributions
    # population = trial.suggest_float("population", min_pop, max_pop)
    ueqi_residential = trial.suggest_float(
        "ueqi_residential", ueqi_residential_current, 1
    )
    ueqi_street_networks = trial.suggest_float(
        "ueqi_street_networks", ueqi_street_networks_current, 1
    )
    ueqi_green_spaces = trial.suggest_float(
        "ueqi_green_spaces", ueqi_green_spaces_current, 1
    )
    ueqi_public_and_business_infrastructure = trial.suggest_float(
        "ueqi_public_and_business_infrastructure",
        ueqi_public_and_business_infrastructure_current,
        1,
    )
    ueqi_social_and_leisure_infrastructure = trial.suggest_float(
        "ueqi_social_and_leisure_infrastructure",
        ueqi_social_and_leisure_infrastructure_current,
        1,
    )
    ueqi_citywide_space = trial.suggest_float(
        "ueqi_citywide_space", ueqi_citywide_space_current, 1
    )

    median_salary = trial.suggest_float("median_salary", median_salary_current, 1)
    # Add more parameters if needed

    # Combine the parameters into a feature vector
    city_parameters = [
        population,
        harsh_climate,
        ueqi_residential,
        ueqi_street_networks,
        ueqi_green_spaces,
        ueqi_public_and_business_infrastructure,
        ueqi_social_and_leisure_infrastructure,
        ueqi_citywide_space,
        median_salary,
    ]

    # Predict migration using the model
    pred_migration = model.predict([city_parameters])

    # Return the absolute error (to minimize)
    return pred_migration
    # return abs(target_migration - np.exp(predicted_migration))


def do_optim_recalc(selected_city_params):
    x = preprocess_x(selected_city_params, fit=False)[0]

    # Use functools.partial to bind extra arguments to the objective function
    objective_with_params = partial(
        objective,
        # target_migration=200,  # Example target migration number
        population=x[0],  # Example fixed population
        harsh_climate=x[1],  # Example fixed climate value
        ueqi_residential_current=x[2],  # Example current value
        ueqi_street_networks_current=x[3],
        ueqi_green_spaces_current=x[4],
        ueqi_public_and_business_infrastructure_current=x[5],
        ueqi_social_and_leisure_infrastructure_current=x[6],
        ueqi_citywide_space_current=x[7],
        median_salary_current=x[8],  # Example current salary
    )

    # Set up the Optuna study
    study = optuna.create_study(direction="maximize")

    # Optimize, passing the pre-bound function
    study.optimize(objective_with_params, n_trials=50, n_jobs=5, show_progress_bar=True)

    predicted_city_params = pd.DataFrame(study.best_params, index=["--new--"])
    predicted_city_params["population"] = x[0]
    predicted_city_params["harsh_climate"] = x[1]
    predicted_city_params = predicted_city_params.loc[
        :,
        predicted_city_params.columns[-2:].to_list()
        + predicted_city_params.columns[:-2].to_list(),
    ]
    predicted_city_params.iloc[0, :] = scaler_x.inverse_transform(predicted_city_params)
    predicted_city_params = predicted_city_params.round(0).astype(int)

    predicted_migration = np.exp(
        model.predict(preprocess_x(predicted_city_params, fit=False))
    )
    predicted_city_params["num_in_migration"] = predicted_migration
    return predicted_city_params


if __name__ == "__main__":
    inp = cities.iloc[0, :].to_frame().T[CITY_MODEL_PARAMS]
    output = do_optim_recalc(inp)
    print(output)
