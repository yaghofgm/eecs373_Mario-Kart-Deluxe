import serial
import time

class JetsonComms:
    def __init__(self, port='/dev/ttyTHS1', baud=9600):
        self.ser = serial.Serial(port, baud, timeout=1)
        time.sleep(2)
        print(f"Connected to {port} at {baud} baud")

    def send(self):
        self.ser.write(b"jetson\n\r")
        print("Sent: jetson")

    def receive(self):
        if self.ser.in_waiting > 0:
            data = self.ser.readline().decode('utf-8', errors='replace').strip()
            print(f"Received: {data}")
            return data
        return None

    def close(self):
        self.ser.close()
        print("Connection closed")