import serial
import time

SERIAL_PORT = '/dev/ttyTHS1'
BAUD_RATE = 9600

ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(2)  # let port settle

print("Sending test message...")
ser.write(b"{hello}\n\r")

time.sleep(0.5)

if ser.in_waiting > 0:
    response = ser.readline().decode('utf-8', errors='replace').strip()
    print(f"Received: {response}")
else:
    print("No response received")

ser.close()
