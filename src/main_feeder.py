"""Feeder version 7.1. Edition by Suieubayev Maxat.
main_feeder.py - это файл с основной логикой работы кормушки. 
Contact number +7 775 818 48 43. Email maxat.suieubayev@gmail.com"""

#!/usr/bin/sudo python3

from _headers import install_packages

requirement_list = ['loguru', 'requests', 'numpy', 'RPi.GPIO', 'wabson.chafon-rfid', 'pyserial']
install_packages(requirement_list)

from _feeder_module import feeder_module_v71
from loguru import logger
from _config_manager import ConfigManager
from _glb_val import DEBUG

try:
    import RPi.GPIO
    log_dir = "/home/pi/feeder_v71/feeder_installer_submodule_src/feeder_installer_submodule_src/feeder_log"
except RuntimeError:
    from __gpio_simulator import MockGPIO
    log_dir = '../feeder_log'

config_manager = ConfigManager()
debug_level = "DEBUG" if DEBUG == 1 else "CRITICAL"

"""Инициализация logger для хранения записи о всех действиях программы"""
logger.add(f'{log_dir}\feeder.log', format="{time} {level} {message}", 
level=debug_level, rotation="1 day", retention= '1 month', compression="zip")  

"""Инициализация logger для хранения записи об ошибках программы"""
logger.add(f'{log_dir}error_log\error.log', format="{time} {level} {file}:{line} {message}", 
level="ERROR", rotation="1 day", retention= '1 month', compression="zip") 
       
@logger.catch
def main():
    try:
        feeder_module_v71()
    except Exception as e: 
        logger.error(f'Error: {e}')

        
main()



