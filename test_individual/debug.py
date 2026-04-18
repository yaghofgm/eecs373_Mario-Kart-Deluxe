import Jetson.GPIO as GPIO
import time
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup([11, 13, 22, 18], GPIO.OUT)
GPIO.output(11, GPIO.HIGH); GPIO.output(13, GPIO.LOW)
GPIO.output(22, GPIO.HIGH); GPIO.output(18, GPIO.LOW)
print('Direction pins set - swap ENA wire between pins')
time.sleep(240)
GPIO.cleanup()