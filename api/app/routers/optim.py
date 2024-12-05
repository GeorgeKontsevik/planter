from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict
from functools import partial
import logging
import optuna
from sqlalchemy.orm import Session
import geopandas as gpd
from catboost import CatBoostRegressor
import os
import pickle

from .. import schemas
from ..database import get_db
from ..dependencies import get_current_user  # Implement authentication as needed
from ..methods.methods_recalc._model_preprocesser import preprocess_x
from ..methods.methods_recalc.recalc_optim import objective

router = APIRouter(
    prefix="/cities",
    tags=["City"],
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

directory = "api/app/data"
filepath = os.path.join(directory, 'cities.parquet')
cities = gpd.read_parquet(filepath)

filepath = os.path.join(directory, 'scaler_x.pkl')
with open(filepath, "rb") as f:
    scaler_x = pickle.load(f)

cbm_path = os.path.join(directory, "city_migr_pred_1711_base.cbm")
model = CatBoostRegressor()
model.load_model(cbm_path)



@router.post("/optimize", response_model=schemas.OptimizeResponse, status_code=201)
async def optimize_city(
    request: schemas.OptimizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    cols = [
    "population",
    "harsh_climate",
    # "ueqi_score",
    "ueqi_residential",
    "ueqi_street_networks",
    "ueqi_green_spaces",
    "ueqi_public_and_business_infrastructure",
    "ueqi_social_and_leisure_infrastructure",
    "ueqi_citywide_space",
    "median_salary",
    "factories_total",
    ]

    """
    Update city parameters and run optimization.
    """

    try:
        name = request.name
        new_params = request.new_params.dict(exclude_unset=True)

        # Fetch the city from the dataset
        selected_city = cities.loc[cities["region_city"] == name, cols]
        if selected_city.empty:
            raise HTTPException(status_code=404, detail="City not found")

        # Preprocess city data
        x = preprocess_x(selected_city, scaler_x, fit=False)[0]
        x = [round(val, 3) for val in x]

        # Bind parameters to the objective function
        objective_with_params = partial(
            objective,
            population=x[0],
            harsh_climate=x[1],
            ueqi_residential_current=x[2],
            ueqi_street_networks_current=x[3],
            ueqi_green_spaces_current=x[4],
            ueqi_public_and_business_infrastructure_current=x[5],
            ueqi_social_and_leisure_infrastructure_current=x[6],
            ueqi_citywide_space_current=x[7],
            median_salary_current=x[8],
            factories_total=x[9],
            model=model,
        )

        # Capture the optimization results
        class OptimizeResult:
            initial_migration: float = 0
            best_value: float = 0
            best_params: Dict[str, float] = {}

        result = OptimizeResult()

        def run_study():
            try:
                study = optuna.create_study(direction="maximize")
                study.optimize(
                    objective_with_params, n_trials=50, n_jobs=1, show_progress_bar=True
                )
                result.initial_migration = round(
                    cities.loc[cities["region_city"] == name, "num_in_migration"].item(),
                    2,
                )
                result.best_value = study.best_value
                result.best_params = {
                    k: round(v, 3) for k, v in study.best_params.items()
                }
                logger.info(f"Optimization completed for {name}")
            except Exception as e:
                logger.error(f"Error during optimization: {e}")

        # Run the optimization as a background task
        background_tasks.add_task(run_study)

        return schemas.OptimizeResponse(
            initial_migration=result.initial_migration,
            optimized_migration=result.best_value,
            optimal_parameters=result.best_params,
        )
    except HTTPException as e:
        logger.error(f"HTTPException: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")