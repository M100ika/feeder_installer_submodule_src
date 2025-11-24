import RPi.GPIO as GPIO
from time import sleep

RELAY_PIN = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    while True:
        val = GPIO.input(RELAY_PIN)
        print("RAW:", val)  # 0 или 1
        sleep(0.2)
finally:
    GPIO.cleanup()
