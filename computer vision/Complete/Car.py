import logging
import time
import cv2
from BLEManager import BLEDevice
from camera import Camera
from motorController import MotorController
from direction_classifier import LaneClassifier
from pn532.pn532.api import PN532
from esp import JetsonComms

# Configure logging to write to a file for headless operation
logging.basicConfig(
    filename='car_system.log',
    filemode='a', # 'a' appends to the log, use 'w' if you want a fresh log every boot
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


GREEN_TAGS = {
    (0x04, 0x2A, 0xA7, 0x31, 0xD5, 0x2A, 0x81),
    (0x04, 0xC2, 0x9F, 0x31, 0xD5, 0x2A, 0x81),
    (0x04, 0xEB, 0xA3, 0x31, 0xD5, 0x2A, 0x81),
    (0x04, 0xB2, 0xAA, 0x31, 0xD5, 0x2A, 0x81),
    (0x04, 0xF6, 0xB3, 0x31, 0xD5, 0x2A, 0x81),
    (0x04, 0x73, 0xAE, 0x31, 0xD5, 0x2A, 0x81)
}

YELLOW_TAGS = {
    (0x04, 0x9D, 0xF4, 0x3D, 0xD4, 0x2A, 0x81),
    (0x04, 0x98, 0xED, 0x3D, 0xD4, 0x2A, 0x81),
    (0x04, 0x83, 0x3E, 0x3E, 0xD4, 0x2A, 0x81),
    (0x04, 0x28, 0x39, 0x3E, 0xD4, 0x2A, 0x81),
    (0x04, 0x3D, 0x2E, 0x3E, 0xD4, 0x2A, 0x81),
    (0x04, 0xA6, 0x28, 0x3E, 0xD4, 0x2A, 0x81)
}

class Car:
    def __init__(
        self,
        hm_package,
        camera_package
    ):
        # Init BLE device and connect them
        self.hm10 = BLEDevice(
            port=hm_package.port,
            baudrate=hm_package.baudrate,
            name=hm_package.name
        )

        self.hm10.connect()

        # init the ESP32
        self.esp = JetsonComms()

        # Init motor
        self.motorController = MotorController()

        # Init camera
        self.camera = Camera(
            device_index=camera_package.device_index,
            save_dir=camera_package.save_dir
        )
        
        # Init direction classifier with tuned parameters
        self.direction_controller = LaneClassifier(
            hsv_min=(0, 0, 180), 
            hsv_max=(140, 8, 255), 
            center_pct=50, 
            green_hw_pct=40, 
            yellow_thick_pct=23, 
            ignore_top_pct=25, 
            noise_threshold=50
        )       

        # Start listening
        self.hm10.start_listening(self.handle_hm_msg)

        # init NFC reader
        self.NFC_reader = PN532()
        self.NFC_reader.setup()

        self.speed = 17
        self.passed_pre_finished = False
        self.status = "STOP"
        self.is_running = True # Flag to control the headless loop
        self.motorController.stop()
        
        logging.info("Car initialized and ready.")

    def log_status(self):
        """Replaces print_status to write to the log file instead."""
        logging.info(f"Status changed -> State: {self.status} | Speed: {self.speed}%")

    def handle_hm_msg(self, name, data):
        """Callback for HM10 BLE device."""
        command = data.strip().upper()
        logging.info(f"Received HM10 Command: {command}")

        if command == "STOP":
            self.status = "STOP"
            self.motorController.stop()
        elif command == "GO":
            self.status = "GO"
            # Initial kickstart handled in the main loop
        elif command == "SHUTDOWN":
            logging.info("Shutdown command received via HM10.")
            self.is_running = False
        elif command.isdigit():
            self.speed = int(command)
            if self.status == "GO":
                self.motorController.forward(self.speed)
            
        self.log_status()
    

    def start(self):
        """Headless main loop for camera and computer vision processing."""
        self.camera.open()
        logging.info("Car system loop started.")


        print("⚠️ You have 15 seconds to unplug the monitor and keyboard! ⚠️")
            # 15-second countdown
        for i in range(15, 0, -1):
            print(f"Motors starting in {i}...")
            time.sleep(1)
    
        try:
            while self.is_running:
                # cap.read() blocks until a frame is ready, pacing the loop
                ret, frame = self.camera.cap.read()

                if not ret:
                    logging.warning("Failed to grab frame.")
                    continue

                    
                if self.NFC_reader:
                    try:
                        nfc_data = self.NFC_reader.read()
                        if nfc_data is not None:
                            uid = nfc_data[5:]
                            uid_key = tuple(uid)

                            if uid_key in GREEN_TAGS:
                                self.passed_pre_finished = True
                            elif uid_key in YELLOW_TAGS and self.passed_pre_finished == True:
                                self.esp.send()
                                self.passed_pre_finished = 0
                    except Exception as e:
                        logging.error(f"NFC Read Error: {e}")
                
                # Process the frame through the classifier (visuals disabled for performance)
                action, _ = self.direction_controller.get_action(frame, return_visuals=False)
                # Autonomous steering logic
                if self.status == "GO":
                    if action == "STRAIGHT":
                        self.motorController.forward(self.speed)
                    elif action == "TURN_LEFT":
                        self.motorController.turn_left(self.speed)
                    elif action == "TURN_RIGHT":
                        self.motorController.turn_right(self.speed)
                    elif action in ["CRITICAL", "LOST"]:
                        # Fail-safe: stop the motors if vision is compromised
                        self.motorController.stop()
                        
        except Exception as e:
            logging.error(f"Fatal error in main loop: {e}")
        finally:
            self.shutdown()

    def shutdown(self):
        """Cleanly close all connections and hardware interfaces."""
        logging.info("Shutting down the car system...")
        self.motorController.stop()
        self.camera.close()
        self.hm10.disconnect()
        logging.info("Shutdown complete.")
