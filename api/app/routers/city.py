# app/routers/city.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict
from functools import partial
import logging

import optuna
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..dependencies import get_current_user  # Implement authentication as needed

from ..methods.methods_recalc._model_preprocesser import preprocess_x
from ..methods.methods_recalc.recalc_optim import objective

router = APIRouter(
    prefix="/cities",
    tags=["cities"],
    dependencies=[Depends(get_current_user)],  # Secure all endpoints
    responses={404: {"description": "Not found"}},
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/optimize", response_model=schemas.OptimizeResponse, status_code=201)
async def optimize_city(
    request: schemas.OptimizeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Update city parameters and run optimization.
    """
    name = request.name
    new_params = request.new_params.dict(exclude_unset=True)

    # Update the city data in the DataFrame
    try:
        # Assuming `wff` is a global or injected dependency. Adjust as necessary.
        wff.update_city_params(name, new_params)
        wff.recalculate_after_update()
        diff = wff.compare_city_states()
        diff_l = wff.compare_link_states()
    except Exception as e:
        logger.error(f"Error updating city parameters: {e}")
        raise HTTPException(status_code=500, detail="Failed to update city parameters")

    # Prepare data for optimization
    try:
        selected_city = cities.loc[cities["region_city"] == name, cols]
        if selected_city.empty:
            raise HTTPException(status_code=404, detail="City not found")

        x = _preprocess_x(selected_city, scaler_x, fit=False)[0]
        x = [round(val, 3) for val in x]
    except Exception as e:
        logger.error(f"Error preprocessing data: {e}")
        raise HTTPException(status_code=500, detail="Failed to preprocess data")

    # Bind parameters to the objective function
    try:
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
            model=model,  # Ensure `model` is defined or passed appropriately
        )
    except Exception as e:
        logger.error(f"Error binding parameters: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to bind parameters for optimization"
        )

    # Define a callback to capture the results
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
                cities.loc[cities["region_city"] == name, "num_in_migration"].item(), 2
            )
            result.best_value = study.best_value
            result.best_params = {k: round(v, 3) for k, v in study.best_params.items()}
            logger.info(f"Optimization completed for {name}")
        except Exception as e:
            logger.error(f"Error during optimization: {e}")
            # Handle optimization errors as needed

    # Run optimization in background to avoid blocking
    background_tasks.add_task(run_study)

    # Optionally, you can implement a mechanism to check optimization status or retrieve results later
    # For simplicity, here we assume immediate response after scheduling
    return schemas.OptimizeResponse(
        initial_migration=result.initial_migration,
        optimized_migration=result.best_value,
        optimal_parameters=result.best_params,
    )
