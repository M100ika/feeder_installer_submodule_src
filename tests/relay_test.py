import sys
from pathlib import Path

import RPi.GPIO as GPIO

sys.path.append(str(Path(__file__).parent.parent / 'src'))

import _feeder_module as fdr
from time import sleep
from loguru import logger


logger.remove()
logger.add(sys.stderr, format="{time} {level} {message}", level="DEBUG")

def main():
    try:
        while True:
            if fdr._check_relay_state():
                logger.info("Реле True")
            else:
                logger.info("Реле False")
            sleep(0.5)
    except KeyboardInterrupt or Exception as e:
        logger.info(f'Bye')
        GPIO.cleanup()

main()

