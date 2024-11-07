CONST_SEC_IN_H = 3600
H3_RESOLUTION = 6
MAX_ACCS_TIME_HOURS = 2
FIX_COEFF = 2.5  # this was applied to convert distance from hex grid to traditional one
CAR_SPEED_KMH = (
    80  # this was applied to convert distance from hex grid to traditional one
)
YEAR = 2021
HEX_KM_CONVERSION_CONSTANT = 4
HEX_SIZE_KM = HEX_KM_CONVERSION_CONSTANT * FIX_COEFF
CITY_MODEL_PARAMS = [
    "population",
    "harsh_climate",
    "ueqi_residential",
    "ueqi_street_networks",
    "ueqi_green_spaces",
    "ueqi_public_and_business_infrastructure",
    "ueqi_social_and_leisure_infrastructure",
    "ueqi_citywide_space",
    "median_salary",
    "num_in_migration",
]

MASK_X = [
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
    # "vacancies_total",
]

MASK_Y = "num_in_migration"
