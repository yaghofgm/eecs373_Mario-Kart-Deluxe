import serial
import time

try:
    ser = serial.Serial('/dev/ttyUSB0', 38400, timeout=1)
    
    print("--- Configuring Master HC-05 ---")
    
    # 0. Ask the Jetson's module for its OWN MAC address
    ser.write(b"AT+ADDR?\r\n")
    time.sleep(0.5)
    print(f"Jetson Master Address: {ser.read_all().decode('utf-8', errors='ignore').strip()}")
    print("-" * 30)

    # 1. Set to Master Mode
    ser.write(b"AT+ROLE=1\r\n")
    time.sleep(0.5)
    print(f"Role Set (1=Master): {ser.read_all().decode('utf-8', errors='ignore').strip()}")
    
    # 2. Set Connection Mode to "Specific Address" (CMODE=0)
    ser.write(b"AT+CMODE=0\r\n")
    time.sleep(0.5)
    print(f"CMODE Set (0=Specific): {ser.read_all().decode('utf-8', errors='ignore').strip()}")
    
    # 3. Bind to your exact STM32 Slave (Using COMMAS!)
    ser.write(b"AT+BIND=98D3,71,F5CAD7\r\n")
    time.sleep(0.5)
    print(f"Bind Set: {ser.read_all().decode('utf-8', errors='ignore').strip()}")
    
    ser.close()
    print("\nSuccess! Unplug the module and plug it back in NORMALLY (no button).")

except Exception as e:
    print(f"Error: {e}")