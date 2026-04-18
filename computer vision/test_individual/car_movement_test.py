import Jetson.GPIO as GPIO
import time
import threading

IN_1, IN_2, IN_3, IN_4 = 11, 13, 22, 18
ENA = 32
ENB = 33

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup([IN_1, IN_2, IN_3, IN_4, ENA, ENB], GPIO.OUT, initial=GPIO.LOW)

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

def forward(t=2, speed=75):
    GPIO.output(IN_1, GPIO.HIGH); GPIO.output(IN_2, GPIO.LOW)
    GPIO.output(IN_3, GPIO.HIGH); GPIO.output(IN_4, GPIO.LOW)
    pwm_a.set_duty(speed)
    pwm_b.set_duty(speed)
    time.sleep(t)

def stop():
    pwm_a.set_duty(0)
    pwm_b.set_duty(0)
    GPIO.output([IN_1, IN_2, IN_3, IN_4], GPIO.LOW)

try:
    print("0% speed")
    forward(t=3, speed=0)
    stop()

    print("25% speed")
    forward(t=3, speed=25)
    stop()
    time.sleep(1)
    print("75% speed")
    forward(t=3, speed=75)
    stop()
    time.sleep(1)
    print("100% speed")
    forward(t=3, speed=100)
    stop()
finally:
    pwm_a.stop()
    pwm_b.stop()
    GPIO.cleanup()