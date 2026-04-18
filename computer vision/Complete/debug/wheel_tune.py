import time
from motorController import MotorController  # adjust to your filename

# --- TUNE THIS ---
TRIM = 0  # positive = more power to left, negative = more power to right
SPEED = 7
DURATION = 10.0  # seconds
# -----------------

mc = MotorController(tune_parameter=TRIM)

print(f"Running forward | speed={SPEED} | trim={TRIM} | duration={DURATION}s")
# mc.pwm_b.set_duty(90)
time.sleep(3)
mc.forward(speed=SPEED)
time.sleep(DURATION)
mc.stop()
mc.cleanup()
print("Done.")