import csv, serial, time, sys
from pathlib import Path

# ─── USER SETTINGS ──────────────────────────────────────────
INPUT_CSV   = "path.csv"      # must contain: x y z  (space-separated)
OUTPUT_CSV  = "data.csv"      # will be created / overwritten
CMD_DELAY   = 0.25            # s between single-mm pulses
DWELL_S     = 0.10            # settle before READ
BAUD        = 9600            # must match Serial.begin() in Arduino
# ────────────────────────────────────────────────────────────

PORT_FILE = Path("arduino_port.txt")
if not PORT_FILE.exists():
    sys.exit("arduino_port.txt missing – run main.py first.")
PORT_NAME = PORT_FILE.read_text().strip()

ser = serial.Serial(PORT_NAME, BAUD, timeout=1)
time.sleep(2)                               # allow Arduino reset
print(f"[INFO] Connected to {PORT_NAME}")

# ─ helper functions ────────────────────────────────────────
def step_axis(axis: str, delta_mm: int):
    if delta_mm == 0:
        return
    cmd = (axis + ('+\n' if delta_mm > 0 else '-\n')).encode()
    for _ in range(abs(delta_mm)):
        ser.write(cmd)
        time.sleep(CMD_DELAY)

def goto(target, current):
    dx, dy, dz = (t - c for t, c in zip(target, current))
    step_axis('X', dx)
    step_axis('Y', dy)
    step_axis('Z', dz)
    return target

def read_voltage() -> float:
    ser.write(b"READ\n")
    line = ser.readline().decode().strip()
    try:
        return float(line)
    except ValueError:
        print(f"[WARN] malformed ADC reply: {line!r}")
        return float("nan")

# ─ load coordinates ───────────────────────────────────────
path = []
with open(INPUT_CSV, newline='') as f:
    reader = csv.reader(f, delimiter=' ')
    header = next(reader, None)            # optional header
    for row in reader:
        if not row or all(cell.strip() == '' for cell in row):
            continue
        if len(row) < 3:
            print(f"[WARN] skipping short row: {row}")
            continue
        try:
            x, y, z = map(int, row[:3])
            path.append((x, y, z))
        except ValueError:
            print(f"[WARN] non-numeric row skipped: {row}")

if not path:
    sys.exit("Path is empty!")

print(f"[INFO] {len(path)} points loaded from {INPUT_CSV}")

# ─ run the scan & log voltages ────────────────────────────
with open(OUTPUT_CSV, 'w', newline='') as fout:
    writer = csv.writer(fout, delimiter=' ')
    writer.writerow(["x", "y", "z", "reading"])

    current = (0, 0, 0)                    # start at origin
    for idx, target in enumerate(path, start=1):
        current = goto(target, current)
        time.sleep(DWELL_S)

        volts = read_voltage()
        writer.writerow([*target, f"{volts:.5f}"])
        fout.flush()

        if idx % 100 == 0 or idx == len(path):
            print(f"[INFO] {idx}/{len(path)} points  V={volts:.5f}")

ser.close()
print(f"[INFO] Finished at last point; data saved to {OUTPUT_CSV}")
