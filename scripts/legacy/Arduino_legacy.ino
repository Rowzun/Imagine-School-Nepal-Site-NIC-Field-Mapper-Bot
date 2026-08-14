/* ───────────────── robot pin map ───────────────── */
const int Step_z = 8, Dir_z = 6;
const int Step_x = 5, Dir_x = 4;
const int Step_y = 3, Dir_y = 2;
#define STEPS_PER_MM  533.33333334            // 1-mm move = 533 pulses
#define PULSE_US      200            // HIGH / LOW time per pulse

/* ───────────────── sensor setup ────────────────── */
const byte  SIG_PIN = A2;            // analogue input
const float VREF    = 4.9010;           // 3.3 V boards; use 5.0 for Uno
const uint16_t FULL_SCALE = 1023;    // 10-bit ADC (0-1023)

void setup() {
  Serial.begin(9600);                // ← keep in sync with Python
  pinMode(Step_z, OUTPUT);  pinMode(Dir_z, OUTPUT);
  pinMode(Step_x, OUTPUT);  pinMode(Dir_x, OUTPUT);
  pinMode(Step_y, OUTPUT);  pinMode(Dir_y, OUTPUT);
  /* Optional extras
     // analogReadResolution(12);     // RP2040 / SAMD
     // analogReference(INTERNAL);    // 1.1 V on AVR
  */
}

/* ───────── main loop: parse one-line commands ───── */
void loop() {
  static char line[16];
  static byte idx = 0;

  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {          // end-of-command
      line[idx] = '\0';  idx = 0;
      handleCmd(line);
    } else if (idx < sizeof(line) - 1) {
      line[idx++] = c;                     // build token
    }
  }
}

/* ───────── command dispatcher ───────────────────── */
void handleCmd(const char *cmd) {
  if      (!strcmp(cmd, "X+")) { digitalWrite(Dir_x, HIGH);  moveSteps(Step_x); }
  else if (!strcmp(cmd, "X-")) { digitalWrite(Dir_x, LOW);   moveSteps(Step_x); }
  else if (!strcmp(cmd, "Y+")) { digitalWrite(Dir_y, HIGH);  moveSteps(Step_y); }
  else if (!strcmp(cmd, "Y-")) { digitalWrite(Dir_y, LOW);   moveSteps(Step_y); }
  else if (!strcmp(cmd, "Z+")) { digitalWrite(Dir_z, HIGH);  moveSteps(Step_z); }
  else if (!strcmp(cmd, "Z-")) { digitalWrite(Dir_z, LOW);   moveSteps(Step_z); }
  else if (!strcmp(cmd, "READ")) {
    uint16_t raw  = analogRead(SIG_PIN);         // 0-1023
    float volts   = raw * VREF / FULL_SCALE;
    Serial.println(volts, 5);                    // e.g. 0.24200
  }
  /* ignore unknown strings */
}

/* ───────── 1-mm step routine ───────────────────── */
void moveSteps(int stepPin)
{
  for (int i = 0; i < STEPS_PER_MM; ++i) {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(PULSE_US);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(PULSE_US);
  }
}
