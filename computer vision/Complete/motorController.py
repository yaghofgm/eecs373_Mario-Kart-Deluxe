import Jetson.GPIO as GPIO
import time
import threading

class MotorController:
    def __init__(self):
        self.IN_1, self.IN_2 = 11, 13  # left motor direction
        self.IN_3, self.IN_4 = 22, 18  # right motor direction
        self.ENA = 32  # left motor enable
        self.ENB = 33  # right motor enable
        self.speed = 75  # default speed

        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(
            [self.IN_1, self.IN_2, self.IN_3, self.IN_4, self.ENA, self.ENB],
            GPIO.OUT, initial=GPIO.LOW
        )

        self.pwm_a = self._SoftPWM(self.ENA)
        self.pwm_b = self._SoftPWM(self.ENB)

    class _SoftPWM:
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

    def forward(self, speed=None):
        s = speed if speed is not None else self.speed
        GPIO.output(self.IN_1, GPIO.HIGH); GPIO.output(self.IN_2, GPIO.LOW)
        GPIO.output(self.IN_3, GPIO.HIGH); GPIO.output(self.IN_4, GPIO.LOW)
        self.pwm_a.set_duty(s)
        self.pwm_b.set_duty(s)

    def turn_left(self, speed=None):
        s = speed if speed is not None else self.speed
        GPIO.output(self.IN_1, GPIO.LOW);  GPIO.output(self.IN_2, GPIO.LOW)
        GPIO.output(self.IN_3, GPIO.HIGH); GPIO.output(self.IN_4, GPIO.LOW)
        self.pwm_a.set_duty(0)
        self.pwm_b.set_duty(s)

    def turn_right(self, speed=None):
        s = speed if speed is not None else self.speed
        GPIO.output(self.IN_1, GPIO.HIGH); GPIO.output(self.IN_2, GPIO.LOW)
        GPIO.output(self.IN_3, GPIO.LOW);  GPIO.output(self.IN_4, GPIO.LOW)
        self.pwm_a.set_duty(s)
        self.pwm_b.set_duty(0)

    def stop(self):
        self.pwm_a.set_duty(0)
        self.pwm_b.set_duty(0)
        GPIO.output([self.IN_1, self.IN_2, self.IN_3, self.IN_4], GPIO.LOW)

    def cleanup(self):
        self.stop()
        self.pwm_a.stop()
        self.pwm_b.stop()
        GPIO.cleanup()
