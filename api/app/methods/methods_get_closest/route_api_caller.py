"""
Просто стучусь во внешнюю апи для того чтобы получить маршруты по дороге от точки до точки.
Также внутри внешнего апи обрабатываается история когда точка не на графе (берет ближ.).
Да, это происходит прям на проде.
Чтобы не зависеть от внешнего апи, нужно развернуть сервис (есть прям образ) где-то локально.
"""

import requests
from shapely.geometry import LineString
import polyline
from typing import Dict, List, Tuple

from api.app.methods.methods_get_closest.utils import flip_geometry
from api.app.utils.constants import CONST_SEC_IN_H


def _make_pyrosm_api_call(
    start_coords: Tuple[float, float], end_coords: Tuple[float, float]
) -> Dict:
    # Construct the URL for the OSRM route API
    url = f"http://router.project-osrm.org/route/v1/driving/{start_coords[0]},{start_coords[1]};{end_coords[0]},{end_coords[1]}?overview=full"

    # Send the GET request to the OSRM API
    response = requests.get(url, timeout=5)

    assert response.ok, "Bad PYROSM api request, probably coords could be the cause"

    assert len(response.json().items()) != 0, "No data was found on OSM :("

    return response.json()


def _preprocess_geom(geom: str) -> LineString:
    decoded_points = polyline.decode(geom)
    line = LineString(decoded_points)
    line = flip_geometry(line)
    return line


def _get_route_line_geom(route_data: dict) -> str:
    return route_data["routes"][0]["geometry"]


def _get_route_distance(route_data: dict) -> float:
    return route_data["routes"][0]["distance"]


def _get_route_duration(route_data: dict) -> float:
    return round(route_data["routes"][0]["duration"] / CONST_SEC_IN_H, 2)


def get_route(
    start_coords: Tuple[float, float], end_coords: Tuple[float, float]
) -> Dict[str, float | LineString | None]:
    """
    Чтобы подружить эту всю историю с Transport frames (TF), нужно просто заменить этот метод.
    Что конкретно нужно заменить, так это то, как получается маршрут.
    Тут он просто стучится в сторонний АПИ и получает ответ.
    Чтобы это было через осм граф (коим и оперирует TF), нужно где-то засторить дорожный граф на всю рашку.
    Есть идея сторить его где-то не весь, а в делении по АДМ например. И через условно sjoin получать нужный кусок где находится точка (тут нужно все же учесть уровень на котором в TF хранится граф).
    Если условно по изменению графа в TF его сохранять с новым айдишником, запускать джобу по подгрузке его куда-то сюда,
    то при запросе сюда можно также передавать айди нужного графа. Тогда можно условно сравнить до-после.

    Пути (всм на машине) через osmnx можно получить, там не сложно.
    Либо такую штуку как это локально поднять по туториалу от девелоперов osrm.
    """

    # Check if the response is successful
    route_data = _make_pyrosm_api_call(start_coords, end_coords)
    assert route_data["code"] == "Ok", route_data["message"]

    geom = _get_route_line_geom(route_data)

    return {
        "distance": _get_route_distance(route_data),
        "duration": _get_route_duration(route_data),
        "geometry": _preprocess_geom(geom),  # List of (lat, lng) tuples
    }
