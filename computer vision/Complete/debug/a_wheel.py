import time
from motorController import MotorController

mc = MotorController()

# Test motor A only
print("Motor A running...")
mc.pwm_a.set_duty(50)

mc.pwm_a.set_duty(50)
time.sleep(6)
mc.cleanup()