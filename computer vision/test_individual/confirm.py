import serial
import time

def verify_ble_config():
    port = '/dev/ttyUSB0'
    baud = 9600
    
    print(f"--- Interrogating BLE Module on {port} ---")
    
    try:
        # Open the serial port
        ser = serial.Serial(port, baud, timeout=1)
        
        # Dictionary of commands to send
        commands = {
            "Module Status": "AT",
            "Broadcast Name": "AT+NAME?",
            "MAC Address": "AT+ADDR?",
            "Firmware Version": "AT+VERS?",
            "Module Role (0=Peripheral/Slave, 1=Central/Master)": "AT+ROLE?"
        }
        
        for description, cmd in commands.items():
            print(f"Checking {description}...")
            
            # Send command with \r\n based on our previous success
            ser.write((cmd + '\r\n').encode())
            time.sleep(0.6) # Give the module time to think and reply
            
            # Read the response
            response = ""
            while ser.in_waiting > 0:
                response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
            
            # Print the result
            if response:
                print(f"  -> {response.strip()}")
            else:
                print("  -> [No Response]")
            print("-" * 40)
            
    except serial.SerialException as e:
        print(f"\n[!] Port Error: {e}")
        print("Remember to run 'sudo fuser -k /dev/ttyUSB0' if the port is busy.")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("\nVerification complete. Port safely closed.")

if __name__ == '__main__':
    verify_ble_config()