import serial
import time

SERIAL_PORT = '/dev/ttyTHS1'
BAUD_RATE = 9600

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
time.sleep(2)

print("Listening on ttyTHS1...")

try:
    while True:
        data = ser.read(64)  # read raw bytes
        if data:
            print(f"Raw: {data}")
        else:
            print("nothing")
except KeyboardInterrupt:
    print("Stopped")
    ser.close()