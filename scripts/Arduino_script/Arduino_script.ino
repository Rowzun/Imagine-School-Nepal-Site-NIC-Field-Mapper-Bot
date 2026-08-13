// ss49e_mapper_controller.ino
//
// Combined firmware: drives 3 axes (X, Y, Z) via M422 STEP/DIR drivers,
// and reads the SS49E Hall sensor -- all on one Arduino.
//
// M422 is a raw STEP/DIR driver (no G-code parsing) -- this sketch
// generates the step pulses directly.
//
// Serial protocol (from Python):
//   'H'                 -> zero/home: set current position as (0,0,0)
//   'M x,y,z\n'          -> move to ABSOLUTE position (x,y,z) in mm, blocks
//                           until complete, then replies "OK"
//   'R'                 -> take a 100-sample averaged sensor reading,
//                           reply with gauss
//
// ------------------- WIRING -------------------
// M422 (X axis):  STEP -> pin 2   DIR -> pin 3   ENA -> pin 4  (optional)
// M422 (Y axis):  STEP -> pin 5   DIR -> pin 6   ENA -> pin 7  (optional)
// M422 (Z axis):  STEP -> pin 8   DIR -> pin 9   ENA -> pin 10 (optional)
// SS49E:          OUT  -> A0, VCC -> 5V, GND -> GND
// ------------------------------------------------

// ====== FILL THESE IN BEFORE USE ======
// steps_per_mm = (motor full steps per rev * microstepping) / (mm per rev)
// Example: 200 steps/rev motor, 1/8 microstepping, 2mm/rev leadscrew:
//          (200 * 8) / 2 = 800 steps/mm
const float STEPS_PER_MM_X = 1679.2;   
const float STEPS_PER_MM_Y = 1679.2;   
const float STEPS_PER_MM_Z = 1679.2;   
// =======================================

const int STEP_PIN_X = 5, DIR_PIN_X = 4;
const int STEP_PIN_Y = 3, DIR_PIN_Y = 2;
const int STEP_PIN_Z = 7, DIR_PIN_Z = 6;

const int SENSOR_PIN = A0;
const unsigned int STEP_PULSE_US = 400;   // step timing 

// ---- SS49E calibration ----
// Re-fit against NMR ground-truth field data (z_sweep_log.csv vs
// NMR_Gauss_meter_interpolated_0-50mm.xlsx), 18-50mm linear region
// (below 18mm the sensor saturates), R^2 = 0.99993.
// Previous values (V0=2.6865, SENSITIVITY=0.002747) had a ~0.115V V0
// error, worth ~43G of flat offset across the whole range.
const float V0 = 2.571686;          // was 2.6865
const float SENSITIVITY = 0.0026927; // V/Gauss, was 0.002747

// current absolute position, in steps, relative to wherever 'H' was last sent
long posStepsX = 0, posStepsY = 0, posStepsZ = 0;

void setup() {
  Serial.begin(9600);
  pinMode(STEP_PIN_X, OUTPUT); pinMode(DIR_PIN_X, OUTPUT);
  pinMode(STEP_PIN_Y, OUTPUT); pinMode(DIR_PIN_Y, OUTPUT);
  pinMode(STEP_PIN_Z, OUTPUT); pinMode(DIR_PIN_Z, OUTPUT);
}

void stepAxis(int stepPin, int dirPin, long steps) {
  digitalWrite(dirPin, steps >= 0 ? HIGH : LOW);
  long n = abs(steps);
  for (long i = 0; i < n; i++) {
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(STEP_PULSE_US);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(STEP_PULSE_US);
  }
}

float readSensorGauss() {
  long sum = 0;
  const int N = 50;
  for (int i = 0; i < N; i++) {
    sum += analogRead(SENSOR_PIN);
    delay(5);
  }
  float avgRaw = sum / (float)N;
  float Vmeasured = avgRaw * (5.0 / 1023.0);
  float gauss = (Vmeasured - V0) / SENSITIVITY;
  return gauss; 

}

void loop() {
  if (!Serial.available()) return;

  char cmd = Serial.read();

  if (cmd == 'H') {
    // Zero the current physical position -- call this once, with the
    // probe manually positioned at true isocenter, before starting a scan.
    posStepsX = 0; posStepsY = 0; posStepsZ = 0;
    Serial.println("HOMED");
  }

  else if (cmd == 'M') {
    // Read "x,y,z\n" (mm, absolute target from isocenter)
    float targetX = Serial.parseFloat();
    Serial.read();  // consume comma
    float targetY = Serial.parseFloat();
    Serial.read();  // consume comma
    float targetZ = Serial.parseFloat();
    Serial.read();  // consume newline

    long targetStepsX = round(targetX * STEPS_PER_MM_X);
    long targetStepsY = round(targetY * STEPS_PER_MM_Y);
    long targetStepsZ = round(targetZ * STEPS_PER_MM_Z);

    stepAxis(STEP_PIN_X, DIR_PIN_X, targetStepsX - posStepsX);
    stepAxis(STEP_PIN_Y, DIR_PIN_Y, targetStepsY - posStepsY);
    stepAxis(STEP_PIN_Z, DIR_PIN_Z, targetStepsZ - posStepsZ);

    posStepsX = targetStepsX;
    posStepsY = targetStepsY;
    posStepsZ = targetStepsZ;

    Serial.println("OK");
  }

  else if (cmd == 'R') {
    float measured_gauss = readSensorGauss();
    Serial.println(measured_gauss, 6);
  }
}
