#!/usr/bin/env python
"""
z_sweep_log.py

Moves the Z axis outward in 1mm steps using ss49e_mapper_controller.ino's
H / M x,y,z / R serial protocol, reading the sensor after each move.

Note: 'R' on this firmware returns gauss directly (converted on-board
using the .ino's own V0/SENSITIVITY), not raw voltage -- so the value
logged here is exactly what the Arduino reports, unmodified.

Install: pip install pyserial
"""

import serial
import time
import csv

SERIAL_PORT = "COM6"
BAUD_RATE = 9600

START_MM = 0
STEP_MM = 1
MAX_MM = 50

OUTPUT_CSV = "z_sweep_log.csv"


def home(ser: serial.Serial):
    print("Position the probe at your reference point (this becomes z = 0).")
    input("Press Enter once ready...")
    ser.reset_input_buffer()
    ser.write(b"H")
    resp = ser.readline().decode(errors="ignore").strip()
    if resp != "HOMED":
        raise RuntimeError(f"Home failed, got: {resp!r}")
    print(f"  -> {resp}")


def move_to_z(ser: serial.Serial, z_mm: float):
    ser.reset_input_buffer()
    cmd = f"M 0,0,{z_mm}\n".encode()
    ser.write(cmd)
    resp = ser.readline().decode(errors="ignore").strip()
    if resp != "OK":
        raise RuntimeError(f"Move to z={z_mm} failed, got: {resp!r}")


def read_gauss(ser: serial.Serial) -> float:
    ser.reset_input_buffer()
    ser.write(b"R")
    line = ser.readline().decode(errors="ignore").strip()
    try:
        return float(line)
    except ValueError:
        raise RuntimeError(f"Bad sensor reply: {line!r}")


def main():
    print(f"Connecting to {SERIAL_PORT}...")
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=5)
    time.sleep(2)  # let the Arduino finish its reset-on-connect

    home(ser)

    rows = []
    for z_mm in range(START_MM, MAX_MM + 1, STEP_MM):
        move_to_z(ser, -z_mm)
        time.sleep(0.3)  # let vibration settle
        g = read_gauss(ser)
        print(f"  {z_mm:2d} mm -> {g:8.2f} G")
        rows.append((z_mm, g))

    ser.close()

    with open(OUTPUT_CSV, "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["z_mm", "gauss"])
        wr.writerows(rows)
    print(f"\nLogged {len(rows)} points to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()