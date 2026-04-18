import serial
ser = serial.Serial('/dev/ttyTHS1', 115200, timeout=1)
print('UART opened successfully')
ser.close()