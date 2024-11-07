from enum import Enum


class IndustryEnums(str, Enum):
    MINING_OIL_GAS = "oil_and_gas_ext"
    MINING_COAL_ORES = "coal_and_metal_ext"
    MECH_ENGINEERING = "machinery"
    SHIPBUILDING = "shipbuilding"
    aircraft_and_space = "Авиастроение и космическая отрасль"
    NON_FERROUS_METALLURGY = "nonferrous_metallurgy"
    FERROUS_METALLURGY = "ferrous_metallurgy"
    CHEMICAL = "chemicals"
    PHARMA = "pharmacy"
    ELECTRONICS = "electronics"
