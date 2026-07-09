DOMAIN = "samaraenergo"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 3600
MIN_SCAN_INTERVAL = 900
MAX_SCAN_INTERVAL = 86400

BASE_URL = "https://lk.samaraenergo.ru"
SERVICE_PATH = "/sap/opu/odata/sap/Z_ERP_UTILITIES_UMC_SRV_01"
AUTH_CHECK_PATH = "/sap/bc/ui5_ui5/sap/z_umcui5_v03"

ACCOUNT_NUMBER_LENGTH = 12

# RegisterTypeID values used by Samaraenergo meters.
REGISTER_TYPE_DAY = "01"
REGISTER_TYPE_NIGHT = "02"
REGISTER_TYPE_SEMI_PEAK = "03"

SENSOR_AMOUNT_DUE = "amount_due"
SENSOR_DUE_DATE = "due_date"
SENSOR_LAST_PAYMENT = "last_payment"
SENSOR_LAST_PAYMENT_DATE = "last_payment_date"
SENSOR_LAST_READING = "last_reading"
SENSOR_LAST_READING_DATE = "last_reading_date"
SENSOR_LAST_READING_DAY = "last_reading_day"
SENSOR_LAST_READING_NIGHT = "last_reading_night"
SENSOR_LAST_READING_SEMI_PEAK = "last_reading_semi_peak"
SENSOR_AVG_MONTHLY_CONSUMPTION = "avg_monthly_consumption"
SENSOR_AVG_MONTHLY_COST = "avg_monthly_cost"
SENSOR_CONSUMPTION_HISTORY = "consumption_history"
SENSOR_TARIFF_TYPE = "tariff_type"
SENSOR_TARIFF_DAY = "tariff_day"
SENSOR_TARIFF_SEMI_PEAK = "tariff_semi_peak"
SENSOR_TARIFF_NIGHT = "tariff_night"
