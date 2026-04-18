import serial
import threading
import time

class BLEDevice:
    def __init__(self, port, baudrate=9600, name="Jetson_BLE"):
        self.port = port
        self.baudrate = baudrate
        self.name = name
        self.ser = None
        self._is_listening = False
        self._listen_thread = None
        
        # This is a placeholder for the function you want to run when a message arrives
        self.on_message_received = None 

    def connect(self):
        """Attempts to open the serial port."""
        try:
            # timeout=0.1 ensures non-blocking reads
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
            print(f"[+] {self.name} connected on {self.port}")
            return True
        except serial.SerialException as e:
            print(f"[-] Failed to connect {self.name} on {self.port}: {e}")
            return False

    def start_listening(self, callback_function):
        """Starts a background thread to listen for incoming data."""
        if not self.ser or not self.ser.is_open:
            print(f"[-] {self.name} is not connected. Cannot start listening.")
            return

        self.on_message_received = callback_function
        self._is_listening = True
        
        # daemon=True means this thread will automatically die when your main script exits
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()
        print(f"[+] {self.name} is now listening in the background.")

    def _listen_loop(self):
        """The internal loop that checks for data."""
        while self._is_listening:
            try:
                if self.ser.in_waiting > 0:
                    data = self.ser.read_all().decode('utf-8', errors='ignore').strip()
                    if data and self.on_message_received:
                        # Pass the name and the data to the callback
                        self.on_message_received(self.name, data)
            except Exception as e:
                print(f"[-] Error reading from {self.name}: {e}")
                self._is_listening = False
            
            time.sleep(0.05) # Prevent maxing out the CPU

    def send(self, message):
        """Sends a string message to the BLE device."""
        if self.ser and self.ser.is_open:
            try:
                full_message = f"{message}\r\n"
                self.ser.write(full_message.encode('utf-8'))
                return True
            except Exception as e:
                print(f"[-] Failed to send to {self.name}: {e}")
                return False
        else:
            print(f"[-] Cannot send. {self.name} is disconnected.")
            return False

    def disconnect(self):
        """Safely shuts down the thread and closes the port."""
        self._is_listening = False
        if self._listen_thread:
            self._listen_thread.join(timeout=1.0)
        
        if self.ser and self.ser.is_open:
            self.ser.close()
            print(f"[+] {self.name} disconnected.")