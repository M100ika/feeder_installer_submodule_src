import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(23, GPIO.IN)

try:
    while True:
        state = GPIO.input(23)
        print("Состояние GPIO23:", "HIGH" if state == GPIO.HIGH else "LOW")
        time.sleep(0.5)
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()