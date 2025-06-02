#include <Servo.h>

// Configuration des servos
Servo servoMain;        // Servo principal pour diriger les objets
Servo servoTrappe;      // Servo pour ouvrir/fermer les trappes

// Pins des servos
const int SERVO_MAIN_PIN = 9;
const int SERVO_TRAPPE_PIN = 10;

// Positions des servos pour chaque type de déchet
const int POS_PAPER = 20;     // Position pour papier/carton
const int POS_PLASTIC = 60;   // Position pour plastique  
const int POS_METAL = 100;    // Position pour métal
const int POS_GLASS = 140;    // Position pour verre
const int POS_TRASH = 180;    // Position pour non-recyclable
const int POS_NEUTRAL = 90;   // Position neutre

// Positions trappe
const int TRAPPE_FERMEE = 0;
const int TRAPPE_OUVERTE = 90;

// Variables
String inputString = "";
bool stringComplete = false;
unsigned long lastMovement = 0;
const unsigned long MOVEMENT_DELAY = 2000; // 2 secondes

void setup() {
  Serial.begin(9600);
  
  // Attacher les servos
  servoMain.attach(SERVO_MAIN_PIN);
  servoTrappe.attach(SERVO_TRAPPE_PIN);
  
  // Position initiale
  servoMain.write(POS_NEUTRAL);
  servoTrappe.write(TRAPPE_FERMEE);
  
  delay(1000);
  
  Serial.println("READY");
  Serial.println("Arduino Tri Automatique initialisé");
}

void loop() {
  // Vérifier les commandes série
  if (stringComplete) {
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }
  
  // Retour automatique en position neutre après délai
  if (millis() - lastMovement > MOVEMENT_DELAY && 
      servoMain.read() != POS_NEUTRAL) {
    returnToNeutral();
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
  // Parse la commande reçue (format: "TYPE,CONFIDENCE")
  int commaIndex = command.indexOf(',');
  
  if (commaIndex > 0) {
    String objectType = command.substring(0, commaIndex);
    float confidence = command.substring(commaIndex + 1).toFloat();
    
    Serial.print("Reçu: ");
    Serial.print(objectType);
    Serial.print(" avec confiance: ");
    Serial.println(confidence);
    
    // Traiter selon le type d'objet
    if (objectType == "TEST") {
      Serial.println("READY");
    }
    else if (objectType == "PAPER") {
      moveToPosition(POS_PAPER, "Papier/Carton");
    }
    else if (objectType == "PLASTIC") {
      moveToPosition(POS_PLASTIC, "Plastique");
    }
    else if (objectType == "METAL") {
      moveToPosition(POS_METAL, "Métal");
    }
    else if (objectType == "GLASS") {
      moveToPosition(POS_GLASS, "Verre");
    }
    else if (objectType == "TRASH") {
      moveToPosition(POS_TRASH, "Non-recyclable");
    }
    else {
      Serial.println("ERREUR: Type non reconnu");
      return;
    }
    
    Serial.println("DONE");
  } else {
    Serial.println("ERREUR: Format de commande invalide");
  }
}

void moveToPosition(int position, String category) {
  Serial.print("Tri vers: ");
  Serial.println(category);
  
  // Ouvrir la trappe
  servoTrappe.write(TRAPPE_OUVERTE);
  delay(500);
  
  // Mouvement du servo principal vers la position cible
  int currentPos = servoMain.read();
  int step = (position > currentPos) ? 1 : -1;
  
  for (int pos = currentPos; pos != position; pos += step) {
    servoMain.write(pos);
    delay(15); // Mouvement fluide
  }
  
  delay(1000); // Attendre que l'objet tombe
  
  // Fermer la trappe
  servoTrappe.write(TRAPPE_FERMEE);
  delay(500);
  
  lastMovement = millis();
}

void returnToNeutral() {
  Serial.println("Retour position neutre");
  
  int currentPos = servoMain.read();
  int step = (POS_NEUTRAL > currentPos) ? 1 : -1;
  
  for (int pos = currentPos; pos != POS_NEUTRAL; pos += step) {
    servoMain.write(pos);
    delay(15);
  }
}
