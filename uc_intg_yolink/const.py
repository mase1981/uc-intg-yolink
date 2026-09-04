"""Constants for the YoLink integration."""

STATE_ON = "ON"
STATE_UNAVAILABLE = "UNAVAILABLE"

POLL_INTERVAL = 60

TOKEN_URL = "https://api.yosmart.com/open/yolink/token"

# YoLink device_type strings (from yolink-api const).
TYPE_SWITCH = "Switch"
TYPE_OUTLET = "Outlet"
TYPE_MULTI_OUTLET = "MultiOutlet"
TYPE_MANIPULATOR = "Manipulator"
TYPE_TH_SENSOR = "THSensor"
TYPE_DOOR_SENSOR = "DoorSensor"
TYPE_MOTION_SENSOR = "MotionSensor"
TYPE_LEAK_SENSOR = "LeakSensor"
TYPE_VIBRATION_SENSOR = "VibrationSensor"

SWITCH_TYPES = {TYPE_SWITCH, TYPE_OUTLET, TYPE_MULTI_OUTLET, TYPE_MANIPULATOR}
OUTLET_TYPES = {TYPE_OUTLET, TYPE_MULTI_OUTLET}

# Contact/alert sensor kinds -> (open/alert label, closed/clear label).
STATE_KIND_LABELS = {
    "door": ("Open", "Closed"),
    "motion": ("Motion", "Clear"),
    "leak": ("Wet", "Dry"),
    "vibration": ("Vibration", "Clear"),
}

TYPE_STATE_KIND = {
    TYPE_DOOR_SENSOR: "door",
    TYPE_MOTION_SENSOR: "motion",
    TYPE_LEAK_SENSOR: "leak",
    TYPE_VIBRATION_SENSOR: "vibration",
}

# YoLink reports battery as a 0-4 level; map to a percentage.
BATTERY_LEVEL_PERCENT = {0: 0, 1: 25, 2: 50, 3: 75, 4: 100}
