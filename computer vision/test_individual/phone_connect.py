import serial
import time
# 88:25:83:F1:23:F0
# Use the settings we just confirmed
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.1)

print("--- Jetson BLE Chat Initialized ---")
print("1. Connect your phone to 'Jetson_BLE'")
print("2. Send a message from your app...")
print("3. Press Ctrl+C to exit")

try:
    while True:
        # Check for data from Phone -> Jetson
        if ser.in_waiting > 0:
            data = ser.read_all().decode(errors='ignore').strip()
            print(f"Phone says: {data}")
            
            # Send an auto-reply back to the Phone
            ser.write(b"Jetson received: " + data.encode() + b"\r\n")

        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nClosing connection.")
finally:
    ser.close()