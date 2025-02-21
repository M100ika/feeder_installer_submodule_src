from _config_manager import ConfigManager


config_manager = ConfigManager()

DEBUG = int(config_manager.get_setting("Parameters", "debug"))

SQL_ON = int(config_manager.get_setting("Parameters", "database"))

EQUIPMENT_TYPE = config_manager.get_setting("Parameters", "type")
SERIAL_NUMBER = config_manager.get_setting("Parameters", "serial_number")

URL = config_manager.get_setting("Parameters", "url")
HEADERS = {'Content-type': 'application/json'}

TCP_IP = '192.168.1.250'  
TCP_PORT = 60000          
BUFFER_SIZE = 512

ARDUINO_PORT = config_manager.get_setting("Parameters", "arduino_port") 
if ARDUINO_PORT == "Отсутствует":
    ARDUINO_PORT == None

CALIBRATION_MODE = int(config_manager.get_setting("Calibration", "calibration_mode"))
RFID_CABLIBRATION_MODE = int(config_manager.get_setting("Calibration", "rfid_calibration_mode"))
CALIBRATION_TARING_RFID = config_manager.get_setting("Calibration", "taring_rfid")
CALIBRATION_SCALE_RFID = config_manager.get_setting("Calibration", "scaling_rfid")
CALIBRATION_WEIGHT = int(config_manager.get_setting("Calibration", "weight"))
RELAY_PIN = int(config_manager.get_setting("Relay", "sensor_pin"))
RFID_TIMEOUT = int(config_manager.get_setting("RFID_Reader", "reader_timeout"))

RFID_READER_USB = int(config_manager.get_setting("RFID_Reader", "reader_usb"))

def closest_number(n):
    numbers = [1, 3, 5, 7, 10, 15, 20, 26]
    if n < min(numbers):
        return min(numbers)
    return min(numbers, key=lambda x: abs(x - n))
initial_power = int(config_manager.get_setting("RFID_Reader", "reader_power"))
power_key = closest_number(initial_power)

SET_POWER_MESSAGES = {1:[0x53, 0x57, 0x00, 0x25, 0xFF, 0x21, 0xC3, 0x55, 0x02, 0x01, 0x00, 0x00, 0x01, 0x01, 0x04, 0x4E, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x1E, 0x0A, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x6A],
3:[0x53, 0x57, 0x00, 0x25, 0xFF, 0x21, 0xC3, 0x55, 0x02, 0x01, 0x00, 0x00, 0x03, 0x01, 0x04, 0x4E, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x1E, 0x0A, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x68],
5:[0x53, 0x57, 0x00, 0x25, 0xFF, 0x21, 0xC3, 0x55, 0x02, 0x01, 0x00, 0x00, 0x05, 0x01, 0x04, 0x4E, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x1E, 0x0A, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x66],
7:[0x53, 0x57, 0x00, 0x25, 0xFF, 0x21, 0xC3, 0x55, 0x02, 0x01, 0x00, 0x00, 0x07, 0x01, 0x04, 0x4E, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x1E, 0x0A, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x64],
10:[0x53, 0x57, 0x00, 0x25, 0xFF, 0x21, 0xC3, 0x55, 0x02, 0x01, 0x00, 0x00, 0x0A, 0x01, 0x04, 0x4E, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x1E, 0x0A, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x61],
15:[0x53, 0x57, 0x00, 0x25, 0xFF, 0x21, 0xC3, 0x55, 0x02, 0x01, 0x00, 0x00, 0x0F, 0x01, 0x04, 0x4E, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x1E, 0x0A, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x5C],
20:[0x53, 0x57, 0x00, 0x25, 0xFF, 0x21, 0xC3, 0x55, 0x02, 0x01, 0x00, 0x00, 0x14, 0x01, 0x04, 0x4E, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x1E, 0x0A, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x57],
26:[0x53, 0x57, 0x00, 0x25, 0xFF, 0x21, 0xC3, 0x55, 0x02, 0x01, 0x00, 0x00, 0x1A, 0x01, 0x04, 0x4E, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x1E, 0x0A, 0x0F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x51]}

RFID_READER_POWER = SET_POWER_MESSAGES.get(power_key)

