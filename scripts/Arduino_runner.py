#!/usr/bin/env python
# Field-mapper runner - single Arduino handles motion (M422 steppers)
# AND the SS49E Hall sensor reading, over one serial link.
#
# NOTE: The Arduino sketch now converts raw sensor voltage to gauss
# ON-BOARD (see readSensorGauss() in the .ino) and returns the gauss
# value directly in response to 'R'. This script no longer performs
# its own voltage->gauss conversion -- doing so would double-convert
# an already-converted value.
#
# If you want to change the calibration (V0 / sensitivity), edit the
# constants in the .ino file, NOT here -- the values below are no
# longer used for conversion and are kept only as a reference/record
# of what was previously used on the Python side.

import csv, serial, time, math, sys
from pathlib import Path

# ─── USER SETTINGS ────────────────────────────────────────────────────────
INPUT_CSV    = "path.csv"
OUTPUT_CSV   = "data.csv"
DWELL_S      = 1            # settle time after each move, before reading
ARDUINO_BAUD = 9600
MOVE_TIMEOUT = 30          # seconds to wait for "OK" on a move
READ_TIMEOUT = 5           # seconds to wait for a sensor reply
RETRIES      = 1           # extra attempts on a failed move/read before giving up
REREAD_MAX   = 5           # extra full reread attempts at a point if the reading is NaN,
                            # before giving up on that point and moving on anyway

# ---- Calibration reference only (conversion now happens on the Arduino) ----
# Arduino sketch currently uses: V0 = 2.6865 V, SENSITIVITY = 0.002747 V/G
# Double check this matches the fit window you actually want live before a run.
V0_VOLTS_REFERENCE_ONLY             = 2.576520
SENSITIVITY_MV_PER_G_REFERENCE_ONLY = 2.73702
# ────────────────────────────────────────────────────────────────────────

ARDUINO_PORT = Path("arduino_port.txt").read_text().strip() \
    if Path("arduino_port.txt").exists() else sys.exit("arduino_port.txt missing")

try:
    ser = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=2)
    time.sleep(2)  # let the Arduino finish its reset-on-connect
    print(f"[INFO] link on {ARDUINO_PORT}")
except serial.SerialException as e:
    sys.exit(f"Serial error: {e}")

# ─── low-level command helpers ────────────────────────────────────────────
def _send_and_wait(cmd: bytes, timeout: float) -> str:
    """Send a raw command and block for one non-empty reply line."""
    ser.reset_input_buffer()
    ser.write(cmd)
    deadline = time.time() + timeout
    while time.time() < deadline:
        line = ser.readline().decode(errors="ignore").strip()
        if line:
            return line
    return ""

def home():
    input("[INFO] position probe at isocenter, then press Enter to home...")
    reply = _send_and_wait(b"H", timeout=10)
    if reply != "HOMED":
        sys.exit(f"[ERROR] home failed, got: {reply!r}")
    print("[INFO] homed")

def move_to(x, y, z):
    cmd = f"M {x},{y},{z}\n".encode()
    for attempt in range(RETRIES + 1):
        reply = _send_and_wait(cmd, timeout=MOVE_TIMEOUT)
        if reply == "OK":
            return
        print(f"[WARN] move to ({x},{y},{z}) got {reply!r}")
    sys.exit(f"[ERROR] move to ({x},{y},{z}) failed after {RETRIES + 1} attempt(s)")

def read_sensor_gauss() -> float:
    """Request one averaged (100-sample) reading. Arduino returns the
    value already converted to gauss -- NOT a voltage."""
    for attempt in range(RETRIES + 1):
        reply = _send_and_wait(b"R", timeout=READ_TIMEOUT)
        try:
            return float(reply)
        except ValueError:
            print(f"[WARN] bad sensor reply {reply!r}")
    print("[ERROR] sensor read failed, returning NaN")
    return float("nan")

def read_sensor_gauss_with_reread(x, y, z) -> float:
    """Wraps read_sensor_gauss(): if the reading comes back NaN, reread
    (re-request from the Arduino) up to REREAD_MAX times before giving up
    and letting the point be logged as NaN."""
    b = read_sensor_gauss()
    reread_count = 0
    while math.isnan(b) and reread_count < REREAD_MAX:
        reread_count += 1
        print(f"[WARN] invalid reading at ({x},{y},{z}), "
              f"rereading ({reread_count}/{REREAD_MAX})...")
        b = read_sensor_gauss()
    if math.isnan(b):
        print(f"[ERROR] still no valid reading at ({x},{y},{z}) after "
              f"{REREAD_MAX} reread attempt(s), logging NaN and moving on")
    return b

# ─── load path.csv ─────────────────────────────────────────────────────────
path = []
with open(INPUT_CSV, newline='') as f:
    for r in csv.reader(f, delimiter=' '):
        if not r or any(not c.strip() for c in r):
            continue
        if any(not c.lstrip('-').isdigit() for c in r[:3]):
            continue
        path.append(tuple(map(int, r[:3])))

if not path:
    sys.exit("Path is empty!")
print(f"[INFO] {len(path)} points loaded from {INPUT_CSV}")

# ─── scan loop ──────────────────────────────────────────────────────────────
home()

with open(OUTPUT_CSV, 'w', newline='') as fout:
    wr = csv.writer(fout, delimiter=',')
    wr.writerow(["x", "y", "z", "B_gauss"])
    for i, (x, y, z) in enumerate(path, 1):
        move_to(x, y, z)
        time.sleep(DWELL_S)
        b = read_sensor_gauss_with_reread(x, y, z)
        wr.writerow([x, y, z, f"{b:.4f}"])
        fout.flush()
        print(f"[INFO] {i}/{len(path)} pos=({x},{y},{z}) B={b:.2f} G")

ser.close()
print(f"[INFO] finished -- data in {OUTPUT_CSV}")