import sys
from pathlib import Path
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent / 'src'))

from _config_manager import ConfigManager
import _feeder_module as fdr
import _adc_data as ADC

config_manager = ConfigManager()
from time import sleep

logger.remove()
logger.add(sys.stderr, format="{time} {level} {file}:{line} {message}", level="DEBUG")

def main():
    try:
        logger.info(f'\033[1;35mFeeder project. Weight measurment test file.\033[0m')
        test_check = input()
        if test_check == 't':  
            fdr._calibrate_or_start()
            arduino = fdr.initialize_arduino()
            while True:
                print(arduino.read_data())
                sleep(0.1)
                
        arduino = fdr.initialize_arduino()
        while True:
            weight = arduino.get_measure()
            logger.info(f"Weight is: {weight}\n")
            sleep(0.1)
    finally:
        logger.info("Bye!")
        arduino.disconnect()
    

main()