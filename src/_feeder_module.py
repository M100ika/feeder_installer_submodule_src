"""Feeder version 3. Edition by Suieubayev Maxat.
feeder_module.py - это модуль функции кормушки. 
Contact number +7 775 818 48 43. Email maxat.suieubayev@gmail.com"""

#!/usr/bin/sudo python3

from datetime import datetime
from loguru import logger
from _chafon_rfid_lib import RFIDReader
from _sql_database import SqlDatabase
from _config_manager import ConfigManager
import _adc_data as ADC
from collections import Counter

import sys, select, json, time, requests, binascii, socket, os, timeit

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    from __gpio_simulator import MockGPIO as GPIO

from _glb_val import *

config_manager = ConfigManager()


def _get_relay_state() -> bool:
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(RELAY_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    relay_state = GPIO.input(RELAY_PIN)
    
    return relay_state == GPIO.LOW


def _check_relay_state(check_count=10, threshold=7) -> bool:
    try:
        high_count = 0
        for _ in range(check_count):
            if _get_relay_state():
                high_count += 1
                if high_count >= threshold:
                    return True
            time.sleep(0.1)  

        return False
    except Exception as e:
        logger.error(f"_Check_relay_state function error: {e}")


# def initialize_arduino():
#     try:
#         arduino_obj = ADC.ArduinoSerial(ARDUINO_PORT)
#         arduino_obj.connect()
        
#         if not arduino_obj.isOpen():
#             logger.error(f'Failed to open connection on port {ARDUINO_PORT}')
#             return None
        
#         offset = float(config_manager.get_setting("Calibration", "offset"))
#         scale = float(config_manager.get_setting("Calibration", "scale"))
#         arduino_obj.set_offset(offset)
#         arduino_obj.set_scale(scale)
        
#         return arduino_obj
        
#     except Exception as e:
#         logger.error(f'Error connecting or setting calibration: {e}')
#         return None

def initialize_arduino():
    try:
        obj = ADC.ArduinoSerial(ARDUINO_PORT)
        obj.connect()
        offset, scale = float(config_manager.get_setting("Calibration", "offset")), float(config_manager.get_setting("Calibration", "scale"))
        obj.set_offset(offset)
        obj.set_scale(scale)
        return obj
    except Exception as e:
        logger.error(f'Error connecting: {e}')


def __post_request(event_time, feed_time, animal_id, end_weight, feed_weight) -> dict:
    try:
        return {
            "Eventdatetime": event_time,
            "EquipmentType": EQUIPMENT_TYPE,
            "SerialNumber": SERIAL_NUMBER,
            "FeedingTime": feed_time,
            "RFIDNumber": animal_id,
            "WeightLambda": end_weight,
            "FeedWeight": feed_weight
        }
    except ValueError as v:
        logger.error(f'__Post_request function error: {v}')


def __send_post(postData, sql_db):
    try:
        post = requests.post(URL, data = json.dumps(postData), headers = HEADERS, timeout=30)
        logger.info(f'{post.status_code}')
        if post.status_code != 200:
            sql_db.no_internet(postData)
            raise Exception(f'Response status code: {post.status_code}')
    except Exception as err:
        logger.error(f'Error occurred: {err}')
        if SQL_ON:
            database = SqlDatabase()
            database.no_internet(postData)


def _set_power_RFID_ethernet():
    try:
        logger.info(f"Start configure antenna power")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((TCP_IP, TCP_PORT))
        s.send(bytearray(RFID_READER_POWER))
        data = s.recv(BUFFER_SIZE)
        recieved_data = str(binascii.hexlify(data))
        check_code = "b'4354000400210143'"
        if recieved_data == check_code:
            logger.info(f"operation succeeded")
        else: 
            logger.info(f"Denied!")
    except Exception as e:
        logger.error(f"_set_power_RFID_ethernet: An error occurred: {e}")
    finally:
        s.close()     


def __connect_rfid_reader_ethernet():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((TCP_IP, TCP_PORT))
            s.settimeout(RFID_TIMEOUT)

            # Отправляем команду на считывание метки
            command = bytearray([0x53, 0x57, 0x00, 0x06, 0xff, 0x01, 0x00, 0x00, 0x00, 0x50])
            s.send(command)
            time.sleep(0.2)

            ready = select.select([s], [], [], RFID_TIMEOUT)
            if ready[0]:
                data = s.recv(BUFFER_SIZE)
                full_animal_id = binascii.hexlify(data).decode('utf-8')

                logger.info(f'Raw RFID response: {full_animal_id}')
                logger.info(f'Response length: {len(full_animal_id)} characters')

                # Универсальная обработка EPC
                corrected_rfid = extract_epc_from_raw(full_animal_id)
                if corrected_rfid:
                    logger.info(f'Corrected RFID: {corrected_rfid}')
                    return corrected_rfid
                else:
                    logger.warning('Failed to extract RFID.')
                    return None
            else:
                logger.info("No RFID data received within timeout")
                return None

    except Exception as e:
        logger.error(f'Error connect RFID reader: {e}')
        return None


def extract_epc_from_raw(raw_data):
    """
    Универсальная функция для извлечения EPC из ответа RFID-ридера.
    Убирает CRC и адаптируется к разным форматам меток.
    """
    if len(raw_data) < 40:
        logger.warning("RFID response is too short.")
        return None

    # Находим возможные позиции начала EPC (обычно начинается после заголовка)
    start_positions = [40, 44, 48]  # Возможные позиции EPC

    for start in start_positions:
        epc_candidate = raw_data[start:start + 24]  # EPC 12 байт (24 символа)
        
        if len(epc_candidate) == 24:
            # Удаляем последние 4 символа (CRC)
            corrected_epc = epc_candidate[:-4]
            return corrected_epc

    return None


def _calibrate_or_start():
    try:
        logger.info(f'\nTo calibrate the equipment, put a tick in the settings to calibration mode:\nActaul state is {"CALIBRATION_ON" if CALIBRATION_MODE else "CALIBRATION_OFF"}')
        if CALIBRATION_MODE:
            __calibrate(timeout=120)

    except Exception as e:
        logger.error(f'Calibrate or start Error: {e}')


def __input_with_timeout(timeout):

    logger.info(f"You have {int(timeout)} seconds to respond.")
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if ready:
        return sys.stdin.readline().strip()
    else:
        logger.warning("Input timed out.")
        raise TimeoutError("User input timed out.")


def __calibrate(timeout):
    start_time = time.time()

    def time_remaining():
        return max(0, timeout - (time.time() - start_time))

    try:
        logger.info(f'\033[1;33mStarting the calibration process.\033[0m')
        arduino = ADC.ArduinoSerial(config_manager.get_setting("Parameters", "arduino_port"), 9600, timeout=30)
        arduino.connect()

        logger.info(f"Ensure the scale is clear. Press any key once it's empty and you're ready to proceed.")
        time.sleep(1)
        __input_with_timeout(time_remaining())

        offset = arduino.calib_read_mediana()
        logger.info("Offset: {}".format(offset))
        arduino.set_offset(offset)

        logger.info("Place a known weight on the scale and then press any key to continue.")
        __input_with_timeout(time_remaining())

        measured_weight = (arduino.calib_read_mediana() - arduino.get_offset())
        logger.info("Please enter the item's weight in kg.\n>")
        
        item_weight = __input_with_timeout(time_remaining())
        scale = int(measured_weight) / int(item_weight)
        arduino.set_scale(scale)

        logger.info(f"\033[1;33mCalibration complete.\033[0m")
        logger.info(f'Calibration details\n\n —Offset: {offset}, \n\n —Scale factor: {scale}')
        
        config_manager.update_setting("Calibration", "Offset", offset)
        config_manager.update_setting("Calibration", "Scale", scale)

        arduino.disconnect()
        del arduino

    except TimeoutError:
        logger.error("Calibration timed out.")
        arduino.disconnect()
        del arduino
    except Exception as e:
        logger.error(f'Calibration failed: {e}')
        arduino.disconnect()
        del arduino


def _rfid_offset_calib():
    try:
        logger.info(f'\033[1;33mStarting the RFID taring process.\033[0m')
        arduino = ADC.ArduinoSerial(ARDUINO_PORT, 9600, timeout=1)
        arduino.connect()
        offset = arduino.calib_read_mediana()
        arduino.set_offset(offset)
        config_manager.update_setting("Calibration", "Offset", offset)
        logger.info(f'Calibration details\n\n —Offset: {offset}')
        arduino.disconnect()
        del arduino
        logger.info(f'\033[1;33mRFID taring process finished succesfully.\033[0m')
    except:
        logger.error(f'RFID taring process Failed')
        arduino.disconnect()


def _rfid_scale_calib():
    try:
        logger.info(f'\033[1;33mStarting the RFID scale calibration process.\033[0m')
        logger.info(f'\033There should be {CALIBRATION_WEIGHT} kg.\033[')
        arduino = ADC.ArduinoSerial(ARDUINO_PORT, 9600, timeout=1)
        arduino.connect()
        offset = float(config_manager.get_setting("Calibration", "Offset"))
        mediana = arduino.calib_read_mediana()
        logger.info(f'Mediana: {mediana}\noffset: {offset}')
        measured_weight = (mediana - offset)
        logger.info(f'measured_weight: {measured_weight}\nCALIBRATION_WEIGHT: {CALIBRATION_WEIGHT}')
        scale = measured_weight/CALIBRATION_WEIGHT
        logger.info(f'calibration weight is: {CALIBRATION_WEIGHT}')
        arduino.set_scale(scale)
        config_manager.update_setting("Calibration", "Scale", scale)
        logger.info(f'Calibration details\n\n —Scale factor: {scale}')
        arduino.disconnect()
        del arduino
        logger.info(f'\033[1;33mRFID scale calibration process finished succesfully.\033[0m')
    except:
        logger.error(f'calibrate Fail')
        arduino.disconnect()


def __process_calibration(animal_id):
    try:
        if RFID_CABLIBRATION_MODE:
            if animal_id == CALIBRATION_TARING_RFID:
                _rfid_offset_calib()
                return True
            elif animal_id == CALIBRATION_SCALE_RFID:
                _rfid_scale_calib()   
                return True     
        return False
    except Exception as e:
        logger.error(f'Calibration with RFID: {e}')


def __animal_rfid():
    try:
        if RFID_READER_USB:
            rfid_reader = RFIDReader()
            return rfid_reader.connect()
        else:
            return __connect_rfid_reader_ethernet() 
    except Exception as e:
        logger.error(f'RFID reader error: {e}')


def _set_antenna_power(power_level):
    try:
        logger.info(f"Setting antenna power to {power_level}")
        command = SET_POWER_MESSAGES.get(power_level)
        if command is None:
            logger.error(f"Invalid power level: {power_level}")
            return False

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((TCP_IP, TCP_PORT))
            s.send(bytearray(command))
            response = s.recv(BUFFER_SIZE)
            logger.info(f"Power set response: {binascii.hexlify(response).decode('utf-8')}")
        return True

    except Exception as e:
        logger.error(f"Failed to set antenna power: {e}")
        return False
    

def _retry_rfid_with_power_levels():
    power_levels = [10, 15, 20, 26]
    for power in power_levels:
        if _set_antenna_power(power):
            time.sleep(0.5)
            animal_id = __animal_rfid()
            if animal_id is not None:
                logger.info(f"RFID detected at power level {power}: {animal_id}")
                return animal_id
    logger.warning("RFID not detected after changing power levels.")
    return None


def is_valid_rfid(animal_id):
    """
    Проверка, что animal_id выглядит как более-менее адекватный
    """
    return (
        animal_id and                        # не None и не пустая строка
        len(animal_id) >= 8 and              # хотя бы 8 символов
        len(animal_id) <= 64 and             # ограничим максимум
        any(c.isalnum() for c in animal_id)  # хотя бы одна буква или цифра
    )

def _take_weight(weight, count = 50) -> float:
    try:
        weight.clean_arr()  # Очистим массив перед стартом
        for _ in range(count):  # Например, взять 50 значений
            weight.calc_mean()
            time.sleep(0.05)  # Делаем паузу, чтобы усреднить медленнее

        #logger.info(f'ARRAY {weight.get_arr()}')
        return sum(weight.get_arr()) / len(weight.get_arr())
    except Exception as e:
        logger.error(f'Error _take_weight: {e}')


def _process_feeding(weight, sql_db):
    try:
        logger.debug('_process_feeding start')
        if weight is None:
            event_time = str(datetime.now())
            post_data = __post_request(event_time, 0, "Arduino Not Connected", 0, 0)
            __send_post(post_data)
            time.sleep(60)
            os.system("sudo reboot")
            return True
        
        
        start_weight = _take_weight(weight)

        logger.info(f"Start weight (mean): {start_weight}")
        start_time = timeit.default_timer()            
        animal_id = __animal_rfid()
        animal_id_list = []

        if is_valid_rfid(animal_id):
            animal_id_list.append(animal_id)
            logger.info(f"RFID added to list: {animal_id}")
        else:
            logger.warning(f"Ignored suspicious RFID: {animal_id}")

        logger.info(f'Start weight: {start_weight}')      
        logger.info(f'Start time: {start_time}')           
        logger.info(f'Animal ID: {animal_id}')

        __process_calibration(animal_id) 

        beam_sensor_threshold = 3600 # Для обнаружения загрязнения в секундах
        beam_sensor_start_time = None

        logger.debug('start while')
        while True:
            
            
            if _check_relay_state():
                if beam_sensor_start_time is None:
                    beam_sensor_start_time = time.time()

                if time.time() - beam_sensor_start_time > beam_sensor_threshold:
                    logger.error(f'Possible beam sensor contamination detected.')
                    event_time = str(datetime.now())
                    post_data = __post_request(event_time, 0, "Beam Sensor Contamination", 0, 0)
                    __send_post(post_data)
                    logger.info("Raspberry Pi will restart in 30 minutes.")
                    time.sleep(1800)  # Ожидание 30 минут (1800 секунд)
                    os.system("sudo reboot")  # Перезагрузка    
                    return True
                
                current_animal_id = __animal_rfid()  # ВСЕГДА ПРОБОВАТЬ СЧИТАТЬ СНОВА

                # if current_animal_id is None:
                #     logger.info("RFID is None. Retrying power levels.")
                #     current_animal_id = _retry_rfid_with_power_levels()

                if is_valid_rfid(current_animal_id):
                    animal_id_list.append(current_animal_id)
                    logger.info(f"RFID added to list: {current_animal_id}")
                else:
                    logger.warning(f"Ignored suspicious RFID: {current_animal_id}")

                __process_calibration(animal_id)

            else:
                beam_sensor_start_time = None # Сброс таймера
                break

            time.sleep(1)

        logger.debug('while ended')

        end_weight = _take_weight(weight)
        
        logger.info(f"End weight (mean): {end_weight}")
        end_time = timeit.default_timer() 
        feed_time = end_time - start_time           
        feed_time_rounded = round(feed_time, 2)
        final_weight = start_weight - end_weight    
        final_weight_rounded = round(final_weight, 2)

        logger.debug(f'finall weight: {final_weight_rounded}')
        logger.debug(f'feed_time: {feed_time_rounded}')    

        most_common_animal_id = None

        most_common_animal_id = Counter(animal_id_list).most_common(1)[0][0] if animal_id_list else "UNKNOWN"

        if feed_time > 5:
            eventTime = str(datetime.now())
            post_data = __post_request(eventTime, feed_time_rounded, most_common_animal_id, final_weight_rounded, end_weight)
            __send_post(post_data, sql_db)
        
        return False

    except Exception as e:
        logger.error(f'_process_feeding: {e}')
        return True
    
    
def feeder_module_v71():
    try:
        _calibrate_or_start()
        if RFID_READER_USB == False:
            _set_power_RFID_ethernet()

        sql_db = SqlDatabase(db_path='sql_table.db')
        weight = initialize_arduino()

          # Порог для определения загрузки корма
        previous_weight = _take_weight(weight)
        logger.info(f"Initial weight: {previous_weight}")

        last_internet_check = time.time()
          # Проверка интернета каждые 5 минут

        while True:  
            try: 
                current_weight = _take_weight(weight, 20)
                weight_diff = round(current_weight - previous_weight, 2)

                # Если вес увеличился больше чем на threshold, отправляем "ЗАГРУЗКА КОРМА"
                if weight_diff > WEIGHT_CHANGE_THRESHOLD:       
                    event_time = str(datetime.now())
                    current_weight = round(current_weight, 2)
                    weight_diff = round(weight_diff, 2)
                    post_data = __post_request(event_time, 0, "ЗАГРУЗКА КОРМА", current_weight, weight_diff)
                    __send_post(post_data, sql_db)
                    previous_weight = current_weight

                if _check_relay_state():
                    try:
                        if _process_feeding(weight, sql_db):
                            logger.info("Ending process based on _process_feeding result.")
                            break
                    except Exception as e:
                        logger.error(f'Error: _process_feeding {e}')                  

                # Проверка интернета каждые 5 минут
                current_time = time.time()
                if current_time - last_internet_check > INTERNET_CHECK_INTERVAL:
                    sql_db.internet_on()
                    last_internet_check = current_time
                    previous_weight = current_weight

            except KeyboardInterrupt:
                logger.info(f'Stopped by user.')
                break
            except Exception as e:
                logger.error(f'Unexpected error: {e}')
            finally:
                time.sleep(0.1)

    except Exception as e:
        logger.error(f'Critical error in feeder_module_v71: {e}')
    finally:
        if weight is not None:
            weight.disconnect()
        config_manager.update_setting("Calibration", "calibration_mode", 0)   
        GPIO.cleanup()
 


"""Предыдущая версия алгоритма кормушки. Это основной алгоритм, возможно некоторые функции изменены или удалены."""
def feeder_module_v61():
    _calibrate_or_start()  
    logger.debug(f"'\033[1;35mFeeder project version 6.1.\033[0m'")
    while True:
        try:        
            if _get_relay_state():  
                weight = initialize_arduino(ARDUINO_PORT)
                start_weight = _first_weight(weight)       
                start_time = timeit.default_timer()      
                animal_id = __connect_rfid_reader_ethernet()      

                logger.info(f'Start weight: {start_weight}')    
                logger.info(f'Start time: {start_time}')
                logger.info(f'Animal_id: {animal_id}')
                end_time = start_time      
                end_weight = start_weight

                __process_calibration(animal_id)

                while _get_relay_state():
                    end_time = timeit.default_timer()       
                    end_weight = weight._get_measure()
                    logger.info(f'Feed weight: {end_weight}')
                    if animal_id == config_manager.get_config("Parameters", "null_rfid"):
                        animal_id = __connect_rfid_reader_ethernet()
                    time.sleep(1)
                    if _get_relay_state() == False: # На всякий случай
                        break
                    
                logger.info(f'While ended.')

                feed_time = end_time - start_time           
                feed_time_rounded = round(feed_time, 2)
                final_weight = start_weight - end_weight    
                final_weight_rounded = round(final_weight, 2)

                logger.info(f'Finall result')
                logger.info(f'finall weight: {final_weight_rounded}')
                logger.info(f'feed_time: {feed_time_rounded}')

                eventTime = str(str(datetime.now()))

                if feed_time > 10: # Если корова стояла больше 10 секунд то отправляем данные
                    post_data = __post_request(eventTime, feed_time_rounded, animal_id, final_weight_rounded, end_weight)    #400
                    __send_post(post_data)
                weight.disconnect()
        except Exception as e:
            logger.error(f'Error: {e}')
            weight.disconnect()

