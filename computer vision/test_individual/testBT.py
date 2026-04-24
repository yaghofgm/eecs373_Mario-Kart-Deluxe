import serial
import time

ser = serial.Serial('/dev/ttyUSB1', 9600, timeout=2)
time.sleep(1)

print("Listening for data from STM32...")
while True:
    if ser.in_waiting > 0:
        data = ser.readline()
        print("Received:", data.decode('utf-8', errors='ignore'))