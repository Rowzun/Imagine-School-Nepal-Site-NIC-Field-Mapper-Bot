import serial.tools.list_ports


# Common USB-to-serial / development-board identifiers
DEV_BOARD_KEYWORDS = [
    # Arduino
    "arduino",
    "arduino uno",
    "arduino mega",
    "arduino leonardo",

    # Espressif
    "esp32",
    "esp8266",
    "espressif",

    # STM32
    "stm32",
    "stlink",
    "stmicroelectronics",

    # USB-UART bridges
    "ch340",
    "ch341",
    "ch910",
    "cp210",
    "silicon labs",
    "ftdi",
    "ft232",
    "usb serial",
    "usb-to-serial",

    # Other common boards
    "seeed",
    "nordic",
    "j-link",
]

# Known non-development virtual COM ports
IGNORE_KEYWORDS = [
    "bluetooth",
    "intel amt",
    "amt interface",
    "serial over bluetooth",
]


def detect_dev_board():
    ports = serial.tools.list_ports.comports()

    candidates = []

    for port in ports:
        # Combine all useful descriptors into one searchable string
        info = " ".join([
            str(port.device or ""),
            str(port.description or ""),
            str(port.manufacturer or ""),
            str(port.product or ""),
            str(port.hwid or ""),
        ]).lower()

        # Ignore obvious virtual/non-development ports
        if any(keyword in info for keyword in IGNORE_KEYWORDS):
            continue

        # Score likely development-board ports
        score = 0

        for keyword in DEV_BOARD_KEYWORDS:
            if keyword in info:
                score += 1

        # USB VID/PID usually indicates a physical USB device
        if port.vid is not None and port.pid is not None:
            score += 2

        if score > 0:
            candidates.append((score, port))

    # Assume only one development board is connected
    if not candidates:
        return None

    # Highest score first
    candidates.sort(key=lambda x: x[0], reverse=True)

    return candidates[0][1].device


def main():
    port = detect_dev_board()

    if port is None:
        print("ERROR: No development board COM port detected.")
        return

    print(f"Detected development board: {port}")

    try:
        with open("arduino_port.txt", "w") as f:
            f.write(port)

        print(f"COM port saved to arduino_port.txt")

    except OSError as e:
        print(f"ERROR: Could not save COM port: {e}")


if __name__ == "__main__":
    main()