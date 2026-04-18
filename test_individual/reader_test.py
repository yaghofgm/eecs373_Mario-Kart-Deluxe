import smbus2
import time

bus = smbus2.SMBus(1)
PN532_ADDR = 0x24  # smbus2 uses 7-bit address

# Frame constants
PREAMBLE     = 0x00
START1       = 0x00
START2       = 0xFF
POSTAMBLE    = 0x00
HOST_TO_PN   = 0xD4
PN_TO_HOST   = 0xD5

def wait_ready(timeout=2.0):
    """Poll until PN532 returns 0x01 ready byte"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = bus.read_byte(PN532_ADDR)
            if resp == 0x01:
                return True
        except:
            pass
        time.sleep(0.01)
    return False

def write_command(cmd_bytes):
    """Build and send a full PN532 frame"""
    length = len(cmd_bytes) + 1  # +1 for TFI
    lcs = (~length + 1) & 0xFF
    checksum = HOST_TO_PN
    for b in cmd_bytes:
        checksum = (checksum + b) & 0xFF
    dcs = (~checksum + 1) & 0xFF

    frame = (
        [PREAMBLE, START1, START2] +
        [length, lcs] +
        [HOST_TO_PN] +
        list(cmd_bytes) +
        [dcs, POSTAMBLE]
    )
    bus.write_i2c_block_data(PN532_ADDR, 0x00, frame)

def read_ack():
    """Read and validate ACK frame: 00 00 FF 00 FF 00"""
    if not wait_ready():
        return False
    data = bus.read_i2c_block_data(PN532_ADDR, 0x00, 7)
    # data[0] = RDY byte, data[1:7] = ACK frame
    return (data[0] == 0x01 and
            data[1:7] == [0x00, 0x00, 0xFF, 0x00, 0xFF, 0x00])

def read_response(length=32):
    """Read response frame, returns payload bytes (TFI stripped)"""
    if not wait_ready():
        return None
    data = bus.read_i2c_block_data(PN532_ADDR, 0x00, length)
    # data[0] = RDY, data[1:] = frame
    frame = data[1:]
    if frame[0] != 0x00 or frame[1] != 0x00 or frame[2] != 0xFF:
        print("Bad preamble")
        return None
    length = frame[3]
    lcs    = frame[4]
    if (length + lcs) & 0xFF != 0x00:
        print("Bad LCS")
        return None
    if frame[5] != PN_TO_HOST:
        print("Bad TFI")
        return None
    data_len = length - 1  # strip TFI
    return frame[6:6 + data_len]

def sam_config():
    write_command([0x14, 0x01, 0x14, 0x01])
    if not read_ack():
        print("SAM ACK failed")
        return False
    resp = read_response()
    return resp is not None

def get_firmware_version():
    write_command([0x02])
    if not read_ack():
        print("Firmware ACK failed")
        return False
    resp = read_response()
    if resp:
        print(f"Firmware version: {resp[1]}.{resp[2]}")
        return True
    return False

def read_passive_target():
    write_command([0x4A, 0x01, 0x00])
    if not read_ack():
        return None
    resp = read_response(40)
    if resp is None:
        return None
    # resp[0]=0x4B, resp[1]=nTargets, resp[2]=Tg
    # resp[3,4]=SENS_RES, resp[5]=SEL_RES
    # resp[6]=UID length, resp[7:]=UID
    if resp[0] != 0x4B or resp[1] == 0:
        return None
    uid_len = resp[6]
    return list(resp[7:7 + uid_len])

# --- Main ---
print("Waking PN532...")
time.sleep(0.5)
print("bbbbbb")
# if not get_firmware_version():
#     print("Failed to get firmware version — check wiring/DIP switches")
#     exit()
print("zzzzz")
if not sam_config():
    print("SAM config failed")
    exit()
print("dfasdfasdfasd")
print("Waiting for tag...")
while True:
    uid = read_passive_target()
    if uid:
        print(f"Tag UID: {[hex(b) for b in uid]}")
    time.sleep(0.5)