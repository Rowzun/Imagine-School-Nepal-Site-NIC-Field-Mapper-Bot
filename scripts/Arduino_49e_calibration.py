#!/usr/bin/env python
"""
ss49e_calibrate_auto.py

Automated SS49E calibration using the motorized Z axis and a fixed N48 cube
magnet. Reuses the existing ss49e_mapper_controller.ino firmware -- no
separate calibration sketch needed, since that firmware already speaks the
same H / M x,y,z / R protocol this procedure needs.

Procedure:
  1. Bring the sensor face into contact with the magnet's north face by hand.
  2. Send 'H' to zero that contact point as z = 0.
  3. Step outward from the magnet in 1mm increments, 0..15mm, logging an
     averaged voltage reading at each step.
  4. Compute the magnet's expected on-axis field at each distance from its
     dimensions and remanence.
  5. Linear-fit measured voltage vs. expected field -> sensitivity (mV/G)
     and zero offset (V0).

Install: pip install pyserial numpy
"""

import serial
import time
import csv
import numpy as np


SERIAL_PORT = "COM6"
BAUD_RATE = 9600


# ---- N48 cube magnet properties ----
BR_TESLA = 1.25      # nominal N48 remanence (replace as per spec sheet)
L = W = T = 0.012    # meters (12mm cube)

# ---- Sweep settings ----
STEP_MM = 1
MAX_MM = 50
N_REPEATS = 5         # python-side averages per point, on top of the Arduino's own 100-sample average
OUTPUT_CSV = "ss49e_calibration.csv"

# The near-contact end of this sweep produces a very strong field for a
# 12mm N48 cube (several thousand gauss at z=0), which will very likely
# saturate the SS49E well beyond its linear range. Points predicted above
# this threshold are flagged and also fit separately, so the reported
# sensitivity isn't silently corrupted by saturated readings.
SATURATION_WARN_GAUSS = 700


def expected_field_gauss(z_mm: float) -> float:
    """On-axis field of a cuboid magnet at distance z_mm from its face, in gauss."""
    z = max(z_mm, 1e-6) / 1000.0  # avoid a literal divide-by-zero at contact
    t1 = np.arctan((L * W) / (2 * z * np.sqrt(4 * z**2 + L**2 + W**2)))
    t2 = np.arctan((L * W) / (2 * (z + T) * np.sqrt(4 * (z + T) ** 2 + L**2 + W**2)))
    return (BR_TESLA / np.pi) * (t1 - t2) * 10000  # tesla -> gauss


def take_reading(ser: serial.Serial, n_repeats: int = N_REPEATS) -> float:
    voltages = []
    for _ in range(n_repeats):
        ser.reset_input_buffer()
        ser.write(b"R")
        line = ser.readline().decode(errors="ignore").strip()
        try:
            voltages.append(float(line))
        except ValueError:
            print(f"  (skipped bad reading: {line!r})")
    if not voltages:
        raise RuntimeError("No valid readings received -- check wiring/port.")
    return sum(voltages) / len(voltages)


def home(ser: serial.Serial):
    print("Bring the sensor face into contact with the magnet's north face.")
    input("Press Enter once in contact (this becomes z = 0)...")
    ser.reset_input_buffer()
    ser.write(b"H")
    resp = ser.readline().decode(errors="ignore").strip()
    if resp != "HOMED":
        raise RuntimeError(f"Home failed, got: {resp!r}")
    print(f"  -> {resp}")


def move_to_z(ser: serial.Serial, z_mm: int):
    ser.reset_input_buffer()
    cmd = f"M 0,0,{z_mm}\n".encode()
    ser.write(cmd)
    resp = ser.readline().decode(errors="ignore").strip()
    if resp != "OK":
        raise RuntimeError(f"Move to z={z_mm} failed, got: {resp!r}")


def fit_and_report(B_vals, V_vals, label: str):
    slope, intercept = np.polyfit(B_vals, V_vals, 1)
    sensitivity_mV_per_G = slope * 1000
    residuals = np.array(V_vals) - (slope * np.array(B_vals) + intercept)
    rms_mV = np.sqrt(np.mean(residuals**2)) * 1000

    print(f"\n--- Fit ({label}, n={len(B_vals)}) ---")
    print(f"  sensitivity: {sensitivity_mV_per_G:.5f} mV/Gauss")
    print(f"  zero offset (V0): {intercept:.6f} V")
    print(f"  fit RMS residual: {rms_mV:.3f} mV")
    return sensitivity_mV_per_G, intercept


def main():
    print(f"Connecting to {SERIAL_PORT}...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=5)
    time.sleep(2)  # let the Arduino finish its reset-on-connect

    home(ser)

    rows = []
    for z_mm in range(0, MAX_MM + 1, STEP_MM):
        move_to_z(ser, -z_mm)
        time.sleep(0.3)  # let vibration settle
        v = take_reading(ser)
        b = expected_field_gauss(z_mm)
        flag = "  <- likely saturated" if b > SATURATION_WARN_GAUSS else ""
        print(f"  {z_mm:2d} mm -> expected {b:8.2f} G, measured {v:.6f} V{flag}")
        rows.append((z_mm, b, v))

    ser.close()

    with open(OUTPUT_CSV, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["z_mm", "expected_B_gauss", "measured_V"])
        wr.writerows(rows)
    print(f"\nLogged {len(rows)} points to {OUTPUT_CSV}")

    z_vals, B_vals, V_vals = zip(*rows)
    fit_and_report(B_vals, V_vals, "all points")

    unsat = [(b, v) for b, v in zip(B_vals, V_vals) if b <= SATURATION_WARN_GAUSS]
    if 3 <= len(unsat) < len(B_vals):
        b_u, v_u = zip(*unsat)
        sens, v0 = fit_and_report(b_u, v_u, f"B <= {SATURATION_WARN_GAUSS} G only")
        print(f"\nUse these values in field_mapper_runner.py:")
        print(f"  V0_VOLTS = {v0:.6f}")
        print(f"  SENSITIVITY_MV_PER_G = {sens:.5f}")
    else:
        print("\nAll points are within the unsaturated band or too few to")
        print("split -- inspect the printed table above before trusting this fit.")


if __name__ == "__main__":
    main()