from camera import Camera


cam = Camera()
cam.open()
cam.take_picture()          # auto-named by timestamp
cam.take_picture("test.jpg") # custom filename
cam.close()

# Cleaner usage with "with" block (auto closes camera)
with Camera() as cam:
    cam.take_picture()