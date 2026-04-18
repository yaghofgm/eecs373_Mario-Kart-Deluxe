import serial
import time

# Expanded list of bauds found in various clones
bauds = [9600, 115200, 38400, 57600, 19200, 4800, 2400]
port = '/dev/ttyUSB0'

for b in bauds:
    print(f"Testing {b} baud...", end="\r")
    try:
        ser = serial.Serial(port, b, timeout=0.5)
        # Some modules are very picky about timing and line endings
        for msg in [b'AT', b'AT\r\n', b'AT\r', b'AT\n']:
            ser.write(msg)
            time.sleep(0.1)
            if ser.in_waiting:
                res = ser.read_all().decode('utf-8', errors='ignore')
                print(f"\n[!] FOUND MODULE AT {b} BAUD: {res.strip()}")
                ser.close()
                exit()
        ser.close()
    except:
        pass
print("\nNo response at any baud rate. Try swapping TX/RX one more time just in case.")