from motorController import MotorController
import time

motors = MotorController()

speed = 17
motors.turn_left(speed)
time.sleep(4)
motors.stop()
time.sleep(2)