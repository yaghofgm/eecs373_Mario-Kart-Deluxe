import serial

# Ensure baud matches what we found (9600)
ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=1)

print("--- Listening for messages from Phone ---")
try:
    while True:
        if ser.in_waiting > 0:
            # Read the incoming bytes and decode to text
            msg = ser.read_all().decode('utf-8', errors='ignore')
            print(f"Phone sent: {msg.strip()}")
except KeyboardInterrupt:
    ser.close()