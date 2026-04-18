import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

# We will try the most common 'Force Name' command for these clones
print("Attempting to force name to 'Jetson_BLE'...")
# Try NO question mark, NO equals sign
ser.write(b"AT+NAMEJetson_BLE\r\n") 
time.sleep(1)

if ser.in_waiting:
    print(f"Response: {ser.read_all().decode().strip()}")

# Now check if it stuck
ser.write(b"AT+NAME?\r\n")
time.sleep(1)
if ser.in_waiting:
    print(f"Current Name: {ser.read_all().decode().strip()}")

ser.close()