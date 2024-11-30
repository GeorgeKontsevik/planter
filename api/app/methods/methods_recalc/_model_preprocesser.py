"""
Тут готовим модель. Модель готовится один раз (заранее да) и далее читается из файла.
Из того что используется в продакшене только методы 'препроцессинга'
"""

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.preprocessing import MinMaxScaler
from catboost import CatBoostRegressor
import numpy as np

# import pickle

from api.app.utils.data_reader import cities
from api.app.utils.constants import MASK_X, MASK_Y


scaler_x = MinMaxScaler()


def preprocess_x(df, fit=False):
    """
    По факту просто маска и скейлер
    """

    x = df[MASK_X].copy()

    # Step 1: Initialize the MinMaxScaler

    x_scaled = scaler_x.fit_transform(x) if fit else scaler_x.transform(x)

    return x_scaled


# def postprocess_x(df):
#     df


def preprocess_y(df):
    """
    Тк распределение с длинным хвостом то работаем в лог пространстве.
    """
    return np.log(df[MASK_Y])


def postprocess_y(prediction_lst):
    """
    Тк распределение с длинным хвостом то работаем в лог пространстве.
    """
    return np.exp(prediction_lst)


def define_model():
    """
    Катбуст потому что в данном случае матрица взаимодействий между городами слишком sparsed.
    То есть в лоб берем похожие города и смотрим на похожие характеристики. От этого получаем как нужно подкрутить модель чтобы максимизировать в дальнейшем число входящих миграций.

    P.s. да тут получается немного сложно с матрицей потоков, но как будто для этого сервиса оно и не нужно, поэтому было принято решение от потоков в этом конкретном случае отказаться.

    Глобально, это можно сделать если использовать *старую общую модель*, где в тч предсказывается и матричка. Проблема с ней в том, что у нас много единичных миграций.

    Однако, если, как будет сделано в этом сервисе, перейти от упрощенного представления миграций к относительному т.е. сказть что у нас не 1 отклик, а примерно 1 отклик на N человеков то есть на самом деле там скажем 100 откликов. Тогда мб что-то и будет более показательное.
    """
    return CatBoostRegressor(
        iterations=2000,
        learning_rate=0.005,
        random_seed=42,
        loss_function="Quantile",
        early_stopping_rounds=50,
        metric_period=200,
    )


if __name__ == "__main__":
    mask_drop_outliers = (
        (cities["num_in_migration"] > 7)
        & (cities["num_in_migration"] < 300)
        & (cities["population"] < 15e6)
    )
    cities = cities[mask_drop_outliers].copy()

    scaler_x = MinMaxScaler()

    X_scaled = preprocess_x(cities, fit=True)
    y = preprocess_y(cities)

    # Split data into training and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.3, random_state=42
    )

    model = define_model()
    model.fit(X_train, y_train)

    pred_test = model.predict(X_test)
    pred_train = model.predict(X_train)

    print("mape test: ", round(mean_absolute_percentage_error(pred_test, y_test), 3))
    print("mape train: ", round(mean_absolute_percentage_error(pred_train, y_train)), 3)

    # with open(
    #     "./data/model.pkl", "wb"
    # ) as file:  # Открываем файл в бинарном режиме для чтения
    #     pickle.dump(model, file)  # Загружаем модель

    # with open(
    #     "./data/scaler_x.pkl", "wb"
    # ) as file:  # Открываем файл в бинарном режиме для записи
    #     pickle.dump(scaler_x, file)  # Сохраняем модель
