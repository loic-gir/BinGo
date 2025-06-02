#include <Servo.h>

// Configuration servo unique
Servo servoMain;        // Servo principal seulement
const int SERVO_MAIN_PIN = 9;  // Votre servo sur pin 9

// Configuration capteurs ultrasons (inchangé)
const int TRIG_PIN_1 = 2;
const int ECHO_PIN_1 = 3;
const int TRIG_PIN_2 = 4;
const int ECHO_PIN_2 = 5;
const int TRIG_PIN_3 = 6;
const int ECHO_PIN_3 = 7;

// Positions pour chaque type de déchet
const int POS_PAPER = 30;
const int POS_PLASTIC = 70;
const int POS_METAL = 110;
const int POS_GLASS = 150;
const int POS_TRASH = 180;
const int POS_NEUTRAL = 90;

// Variables
String inputString = "";
bool stringComplete = false;
unsigned long lastSensorCheck = 0;
const unsigned long SENSOR_CHECK_INTERVAL = 5000;

void setup() {
  Serial.begin(9600);
  
  // Initialiser UN SEUL servo
  servoMain.attach(SERVO_MAIN_PIN);
  
  // Capteurs ultrasons
  pinMode(TRIG_PIN_1, OUTPUT);
  pinMode(ECHO_PIN_1, INPUT);
  pinMode(TRIG_PIN_2, OUTPUT);
  pinMode(ECHO_PIN_2, INPUT);
  pinMode(TRIG_PIN_3, OUTPUT);
  pinMode(ECHO_PIN_3, INPUT);
  
  // Position initiale
  servoMain.write(POS_NEUTRAL);
  
  delay(1000);
  Serial.println("READY");
  Serial.println("Système avec 1 servo + capteurs initialisé");
  
  checkAllCompartments();
}

void loop() {
  if (stringComplete) {
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }
  
  if (millis() - lastSensorCheck > SENSOR_CHECK_INTERVAL) {
    checkAllCompartments();
    lastSensorCheck = millis();
  }
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      stringComplete = true;
    } else {
      inputString += inChar;
    }
  }
}

void processCommand(String command) {
  int commaIndex = command.indexOf(',');
  
  if (commaIndex > 0) {
    String objectType = command.substring(0, commaIndex);
    
    if (objectType == "TEST") {
      Serial.println("READY");
      return;
    }
    
    // Vérifier disponibilité du compartiment
    bool canSort = true;
    String targetCompartment = "";
    
    if (objectType == "PAPER") {
      canSort = checkCompartmentAvailable(1, "Papier");
      if (canSort) moveToPosition(POS_PAPER, "Papier");
    }
    else if (objectType == "PLASTIC") {
      canSort = checkCompartmentAvailable(2, "Plastique");
      if (canSort) moveToPosition(POS_PLASTIC, "Plastique");
    }
    else if (objectType == "METAL") {
      canSort = checkCompartmentAvailable(3, "Métal");
      if (canSort) moveToPosition(POS_METAL, "Métal");
    }
    else if (objectType == "GLASS") {
      canSort = checkCompartmentAvailable(1, "Verre");
      if (canSort) moveToPosition(POS_GLASS, "Verre");
    }
    else if (objectType == "TRASH") {
      canSort = checkCompartmentAvailable(3, "Déchet");
      if (canSort) moveToPosition(POS_TRASH, "Déchet");
    }
    
    Serial.println(canSort ? "DONE" : "FULL");
  }
}

void moveToPosition(int position, String category) {
  Serial.print("Orientation vers: ");
  Serial.println(category);
  
  // Mouvement fluide du servo vers la position cible
  int currentPos = servoMain.read();
  moveServoSmoothly(currentPos, position);
  
  delay(2000);  // Temps pour que l'objet tombe/glisse
  
  // Retour position neutre
  moveServoSmoothly(position, POS_NEUTRAL);
  
  Serial.print("Tri terminé: ");
  Serial.println(category);
}

void moveServoSmoothly(int fromPos, int toPos) {
  int step = (toPos > fromPos) ? 1 : -1;
  
  for (int pos = fromPos; pos != toPos; pos += step) {
    servoMain.write(pos);
    delay(15);  // Mouvement fluide
  }
  servoMain.write(toPos);  // Position finale exacte
}

// Fonctions des capteurs ultrasons (identiques à avant)
bool checkCompartmentAvailable(int compartmentNum, String compartmentName) {
  float distance = readUltrasonicDistance(compartmentNum);
  
  if (distance <= 5.0) {  // Seuil plein
    Serial.print("ALERTE: Compartiment ");
    Serial.print(compartmentName);
    Serial.println(" PLEIN!");
    return false;
  }
  
  return true;
}

float readUltrasonicDistance(int sensorNumber) {
  int trigPin, echoPin;
  
  switch(sensorNumber) {
    case 1: trigPin = TRIG_PIN_1; echoPin = ECHO_PIN_1; break;
    case 2: trigPin = TRIG_PIN_2; echoPin = ECHO_PIN_2; break;
    case 3: trigPin = TRIG_PIN_3; echoPin = ECHO_PIN_3; break;
    default: return -1;
  }
  
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  long duration = pulseIn(echoPin, HIGH, 30000);
  if (duration == 0) return -1;
  
  return duration * 0.034 / 2;
}

void checkAllCompartments() {
  Serial.println("=== ÉTAT DES COMPARTIMENTS ===");
  
  String compartmentNames[] = {"", "Papier/Verre", "Plastique", "Métal/Déchet"};
  
  for (int i = 1; i <= 3; i++) {
    float distance = readUltrasonicDistance(i);
    Serial.print("Compartiment ");
    Serial.print(compartmentNames[i]);
    Serial.print(": ");
    
    if (distance > 0) {
      Serial.print(distance, 1);
      Serial.print("cm ");
      if (distance <= 5.0) {
        Serial.println("[PLEIN!]");
      } else if (distance <= 8.0) {
        Serial.println("[ATTENTION]");
      } else {
        Serial.println("[OK]");
      }
    } else {
      Serial.println("ERREUR CAPTEUR");
    }
  }
  Serial.println("===============================");
}
