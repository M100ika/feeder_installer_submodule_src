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
    arduino = None
    raw_arr = []

    try:
        logger.info("Starting RAW HX711 collection")
        arduino = fdr.initialize_arduino()

        while True:
            raw = arduino.read_data()   # СЫРОЕ значение
            raw_arr.append(raw)
            logger.info(raw)
            sleep(0.1)

    except KeyboardInterrupt:
        logger.info("Stopping and printing RAW array")

    finally:
        if arduino:
            arduino.disconnect()

        print("\n=== RAW DATA ARRAY ===")
        print(raw_arr)
        print(f"\nTotal samples: {len(raw_arr)}")

if __name__ == "__main__":
    main()