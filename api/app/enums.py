from enum import Enum

class WorkforceTypeEnum(str, Enum):
    SPECIALISTS = 'specialists'
    GRADUATES = 'graduates'
    ALL = f"all"

class IndustryEnum(str, Enum):
    MINING_OIL_GAS = "oil_and_gas_ext"
    MINING_COAL_ORES = "coal_and_metal_ext"
    MECH_ENGINEERING = "machinery"
    SHIPBUILDING = "shipbuilding"
    aircraft_and_space = "aircraft_engineering"
    NON_FERROUS_METALLURGY = "nonferrous_metallurgy"
    FERROUS_METALLURGY = "ferrous_metallurgy"
    CHEMICAL = "chemicals"
    PHARMA = "pharmacy"
    ELECTRONICS = "electronics"

class SpecialtyEnum(str, Enum):
    OPERATOR = 'Оператор, аппаратчик'
    INSTALLER = 'Монтажник'
    MACHINE_OPERATOR = 'Машинист'
    REPAIR_MASTER = 'Мастер по ремонту оборудования'
    HANDYMAN = 'Разнорабочий'
    LOCKSMITH = 'Слесарь'
    SURVEYOR = 'Геодезист'
    GEOLOGIST = 'Геолог'
    TECHNOLOGIST = 'Технолог'
    ECO_ENGINEER = 'Инженер-эколог'
    DESIGN_ENGINEER = 'Инженер-конструктор'
    WELDER = 'Сварщик'
    ADJUSTER = 'Наладчик'
    MACHINIST = 'Токарь, фрезеровщик, шлифовщик'
    Q_CONTROL_INSPECTOR = 'Контролер ОТК'
    PROJECT_ENGINEER = 'Инженер-проектировщик'
    CERTIFICATION_SPECIALIST = 'Специалист по сертификации'
    QUALITY_ENGINEER = 'Инженер по качеству'
    MECHANIC = 'Механик'
    MAINTENANCE_ENGINEER = 'Инженер по эксплуатации'
    LAB_ASSISTANT = 'Лаборант'
    RESEARCHER = 'Исследователь'
    ELECTRICIAN = 'Электромонтажник'