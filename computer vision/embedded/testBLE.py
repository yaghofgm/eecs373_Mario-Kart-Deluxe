from BLEManager import BLEDevice
import time

# 1. Define what happens when the phone sends a message
def on_message_received(device_name, data):
    # This prints the phone's message and reprints the input prompt
    print(f"\n[Phone says]: {data}")
    print("[Send to Phone]: ", end="", flush=True)

# 2. Instantiate your BLE module using the port we confirmed
my_ble = BLEDevice(port='/dev/ttyUSB0', baudrate=9600, name="Jetson_BLE")

# 3. Connect and test
if my_ble.connect():
    # Start the background listening thread
    my_ble.start_listening(callback_function=on_message_received)
    
    print("\n--- BLE Class Test Active ---")
    print("1. Open nRF Connect on your phone and connect.")
    print("2. Enable Notifications (the 3 down-arrows) on characteristic FFE1.")
    print("3. Send a message from your phone.")
    print("-----------------------------\n")
    
    try:
        # 4. Main loop for sending messages to the phone
        while True:
            # Wait for you to type something on the Jetson keyboard
            msg_to_send = input("[Send to Phone]: ")
            if msg_to_send:
                my_ble.send(msg_to_send)
                
    except KeyboardInterrupt:
        print("\nTest stopped by user.")
    finally:
        # Safely close the port and kill the thread
        my_ble.disconnect()
else:
    print("Failed to open /dev/ttyUSB0. Run 'sudo fuser -k /dev/ttyUSB0' if it's busy.")