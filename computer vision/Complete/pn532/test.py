from pn532.api import PN532

nfc = PN532()
nfc.setup()

print("Waiting for card...")
while True:
    data = nfc.read()
    uid = data[5:]  # UID is typically 4 bytes for Mifare Classic
    print("UID:", [hex(b) for b in uid])
    print(len(uid))