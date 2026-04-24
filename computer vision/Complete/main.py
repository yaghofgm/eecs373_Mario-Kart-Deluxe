from collections import namedtuple
from car import Car

if __name__ == "__main__":
    print("Initializing the Car system configurations...")

    BLEConfig = namedtuple('BLEConfig', ['port', 'baudrate', 'name'])
    CameraConfig = namedtuple('CameraConfig', ['device_index', 'save_dir'])

    hm_config = BLEConfig(port='/dev/ttyUSB0', baudrate=9600, name='HM-10')
    cam_config = CameraConfig(device_index=0, save_dir='photos')

    my_car = Car(
        hm_package=hm_config,
        camera_package=cam_config
    )

    print("Car has initialized")

    try:
        my_car.start()
    except KeyboardInterrupt:
        print("\nTest manually interrupted by user.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        my_car.shutdown()
        print("Motors stopped and system shut down. You can plug the monitor back in!")