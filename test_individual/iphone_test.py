import Jetson.GPIO as GPIO
import time
import threading
import serial

# --- 1. GPIO Setup ---
IN_1, IN_2, IN_3, IN_4 = 11, 13, 22, 18
ENA = 32
ENB = 33

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup([IN_1, IN_2, IN_3, IN_4, ENA, ENB], GPIO.OUT, initial=GPIO.LOW)

# --- 2. Your SoftPWM Class ---
class SoftPWM:
    def __init__(self, pin, freq=100):
        self.pin = pin
        self.period = 1.0 / freq
        self.duty = 0
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def _run(self):
        while self.running:
            if self.duty <= 0:
                GPIO.output(self.pin, GPIO.LOW)
                time.sleep(self.period)
            elif self.duty >= 100:
                GPIO.output(self.pin, GPIO.HIGH)
                time.sleep(self.period)
            else:
                GPIO.output(self.pin, GPIO.HIGH)
                time.sleep(self.period * self.duty / 100)
                GPIO.output(self.pin, GPIO.LOW)
                time.sleep(self.period * (1 - self.duty / 100))

    def set_duty(self, duty):
        self.duty = max(0, min(100, duty))

    def stop(self):
        self.running = False
        GPIO.output(self.pin, GPIO.LOW)

pwm_a = SoftPWM(ENA)
pwm_b = SoftPWM(ENB)

# --- 3. Modified Movement Functions (No Time limits) ---
def drive_forward(speed=75):
    print(f"Moving FORWARD at {speed}%")
    GPIO.output(IN_1, GPIO.HIGH); GPIO.output(IN_2, GPIO.LOW)
    GPIO.output(IN_3, GPIO.HIGH); GPIO.output(IN_4, GPIO.LOW)
    pwm_a.set_duty(speed)
    pwm_b.set_duty(speed)

def stop_car():
    print("STOPPING")
    pwm_a.set_duty(0)
    pwm_b.set_duty(0)
    GPIO.output([IN_1, IN_2, IN_3, IN_4], GPIO.LOW)

# --- 4. The Bluetooth Listening Loop ---
try:
    # Open connection to the HM-10
    ble = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.1)
    print("Bluetooth Ready! Waiting for iPhone commands...")
    
    current_speed = 25 # Default speed

    while True:
        if ble.in_waiting > 0:
            # Read incoming text and clean it up
            command = ble.readline().decode('utf-8', errors='ignore').strip().upper()
            
            if command == "GO":
                drive_forward(current_speed)
            elif command == "STOP":
                stop_car()
            elif command.isdigit():
                # If you send a number like "50" or "100"
                current_speed = int(command)
                print(f"Speed set to {current_speed}%")
                # If currently moving, update the speed instantly
                if pwm_a.duty > 0: 
                    drive_forward(current_speed)

except serial.SerialException:
    print("Could not open /dev/ttyUSB0. Is the HM-10 plugged in?")
except KeyboardInterrupt:
    print("\nShutting down by user...")
finally:
    # Always safely shut down the motors and GPIO
    stop_car()
    pwm_a.stop()
    pwm_b.stop()
    GPIO.cleanup()
    print("Cleanup complete.")