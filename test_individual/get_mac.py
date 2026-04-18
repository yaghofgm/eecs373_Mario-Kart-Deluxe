import serial
import time

try:
    ser = serial.Serial('/dev/ttyUSB0', 38400, timeout=1)
    
    print("Asking for Address (Format 1)...")
    ser.write(b"AT+ADDR?\r\n")
    time.sleep(0.8)  # Giving it a little more time
    resp1 = ser.read_all().decode().strip()
    
    if resp1:
        print(f"Response: {resp1}")
    else:
        print("Blank. Trying Format 2 (LADDR)...")
        ser.write(b"AT+LADDR?\r\n")
        time.sleep(0.8)
        resp2 = ser.read_all().decode().strip()
        print(f"Response: {resp2}")

    ser.close()
except Exception as e:
    print(f"Error: {e}")