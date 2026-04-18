import serial
import time

print("--- HC-05 AT Mode Test ---")
print("Make sure the LED is blinking SLOWLY (1 blink per 2 seconds)!\n")

try:
    # HC-05 AT mode is hardcoded to 38400 baud
    ser = serial.Serial('/dev/ttyUSB0', 38400, timeout=1)

    # HC-05 specific commands
    commands = {
        "Module Status": "AT",
        "Firmware Version": "AT+VERSION?",
        "Current Data Baud Rate": "AT+UART?", 
        "Module Role (0=Slave, 1=Master)": "AT+ROLE?",
        "Module Name": "AT+NAME?" 
    }

    for desc, cmd in commands.items():
        print(f"Checking {desc}...")
        ser.write((cmd + '\r\n').encode())
        time.sleep(0.5)
        
        if ser.in_waiting:
            response = ser.read_all().decode(errors='ignore').strip()
            print(f"  -> {response}")
        else:
            print("  -> [No Response]")
        print("-" * 40)

    ser.close()

except serial.SerialException as e:
    print(f"Port Error: {e}")