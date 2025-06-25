#define NB_CAPTEURS 5
#include <Servo.h>

// Déclaration des servomoteurs
Servo servos[4];
const int servoPins[4] = { A0, A1, A2, A3 };
const int initialPositions[4] = {90, 8, 120, 90};

// Configuration des LEDs RGB (cathode commune)
const int ledRouge = 9;   // Pin PWM pour le rouge
const int ledVert = 10;   // Pin PWM pour le vert
const int ledBleu = 11;   // Pin PWM pour le bleu

// États des LEDs
enum EtatLED {
  LED_ATTENTE,    // Blanc - système en attente
  LED_MOUVEMENT,  // Rouge - bras en mouvement
  LED_BAC_PLEIN,  // Bleu - au moins un bac plein
  LED_PROBLEME    // Violet - problème détecté
};

// Configuration des mots-clés
const String mots[5] = { "metal", "carton", "verre", "plastique", "non recyclable" };

// Configuration des capteurs à ultrasons
const int trigPins[NB_CAPTEURS] = { 2, 4, 6, 8, A5 };
const int echoPins[NB_CAPTEURS] = { 3, 5, 7, 12, A4 };

// Variables d'état
bool sequenceComplete = false;
const int DISTANCE_PLEIN = 10;
bool bacPleinDetecte = false;
bool sequenceEnCours = false;

// Fonction utilitaire pour ruban à cathode commune
void setColor(int r, int g, int b) {
  analogWrite(ledRouge, r);
  analogWrite(ledVert, g);
  analogWrite(ledBleu, b);
}

void setLEDColor(EtatLED etat) {
  switch(etat) {
    case LED_ATTENTE:
      setColor(255, 255, 255); // Blanc
      break;
    case LED_MOUVEMENT:
      setColor(255, 0, 0); // Rouge
      break;
    case LED_BAC_PLEIN:
      setColor(0, 0, 255); // Bleu
      break;
    case LED_PROBLEME:
      setColor(255, 0, 255); // Violet
      break;
  }
}

void setup() {
  Serial.begin(9600);

  // Initialisation des LEDs RGB
  pinMode(ledRouge, OUTPUT);
  pinMode(ledVert, OUTPUT);
  pinMode(ledBleu, OUTPUT);

  // LEDs blanches au démarrage (attente)
  setLEDColor(LED_ATTENTE);

  // Initialisation des capteurs
  for (int i = 0; i < NB_CAPTEURS; i++) {
    pinMode(trigPins[i], OUTPUT);
    pinMode(echoPins[i], INPUT);
  }

  // Initialisation des servos
  for (int i = 0; i < 4; i++) {
    servos[i].attach(servoPins[i]);
    servos[i].write(initialPositions[i]);
    delay(500);
  }

  Serial.println("Système prêt. Envoyez un mot clé :");
  for(int i = 0; i < 5; i++) {
    Serial.println("- " + mots[i]);
  }
}

long readDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH, 30000);

  if (duration == 0) {
    Serial.println("Erreur: Timeout capteur ultrason");
    setLEDColor(LED_PROBLEME);
    delay(1000);
    return -1;
  }

  return duration * 0.034 / 2;
}

void moveServo(int servoNum, int targetAngle, int delayTime = 15) {
  setLEDColor(LED_MOUVEMENT); // LEDs rouges pendant le mouvement
  
  int currentPos = servos[servoNum].read();
  
  if(currentPos < targetAngle) {
    for(int angle = currentPos; angle <= targetAngle; angle++) {
      servos[servoNum].write(angle);
      delay(delayTime);
    }
  } else {
    for(int angle = currentPos; angle >= targetAngle; angle--) {
      servos[servoNum].write(angle);
      delay(delayTime);
    }
  }
}

bool checkNiveauxPoubelles() {
  bool tousPleins = true;
  bool auMoinsUnPlein = false;
  Serial.println("\nVérification des niveaux:");

  for (int i = 0; i < NB_CAPTEURS; i++) {
    long distance = readDistance(trigPins[i], echoPins[i]);

    if (distance == -1) {
      Serial.print("Bac ");
      Serial.print(i + 1);
      Serial.println(": ERREUR CAPTEUR");
      tousPleins = false;
      continue;
    }

    Serial.print("Bac ");
    Serial.print(i + 1);
    Serial.print(": ");

    if (distance < DISTANCE_PLEIN) {
      Serial.println("PLEIN");
      auMoinsUnPlein = true;
    } else {
      Serial.print(distance);
      Serial.println(" cm");
      tousPleins = false;
    }
    delay(100);
  }

  bacPleinDetecte = auMoinsUnPlein;

  if (bacPleinDetecte) {
    setLEDColor(LED_BAC_PLEIN);
  }

  return tousPleins;
}

bool executeSequence(String input) {
  input.trim();
  sequenceComplete = false;
  sequenceEnCours = true;
  int commandIndex = -1;

  // Trouver l'index de la commande
  for (int i = 0; i < 5; i++) {
    if (input.equalsIgnoreCase(mots[i])) {
      commandIndex = i;
      break;
    }
  }

  if (commandIndex == -1) {
    sequenceEnCours = false;
    return false;
  }

  Serial.println("\nDébut de la séquence...");

  // Reproduire exactement les séquences du code 1
  if(commandIndex == 0) { // metal
    moveServo(0, 90); delay(500);
    moveServo(1, 0); delay(500);
    moveServo(2, 110); delay(500);
    moveServo(3, 180); delay(500);

    delay(1000);
    moveServo(3, initialPositions[3]); delay(500);
    moveServo(2, initialPositions[2]); delay(500);
    moveServo(1, initialPositions[1]); delay(500);
    moveServo(0, initialPositions[0]); delay(500);
  }
  else if(commandIndex == 1) { // carton
    moveServo(0, 90); delay(500);
    moveServo(1, 8); delay(500);
    moveServo(2, 120); delay(500);
    moveServo(3, 0); delay(500);

    delay(1000);
    moveServo(3, initialPositions[3]); delay(500);
    moveServo(2, initialPositions[2]); delay(500);
    moveServo(1, initialPositions[1]); delay(500);
    moveServo(0, initialPositions[0]); delay(500);
  }
  else if(commandIndex == 2) { // verre
    moveServo(2, 135); delay(500);
    moveServo(1, 50); delay(500);
    moveServo(2, 175); delay(500);
    moveServo(1, 90); delay(500);
    moveServo(0, 170); delay(500);
    moveServo(3, 110); delay(500);

    delay(1000);
    moveServo(3, initialPositions[3]); delay(500);
    moveServo(0, initialPositions[0]); delay(500);
    moveServo(1, 50); delay(500);
    moveServo(2, 135); delay(500);
    moveServo(1, initialPositions[1]); delay(500);
    moveServo(2, initialPositions[2]); delay(500);
  }
  else if(commandIndex == 3) { // plastique
    moveServo(2, 135); delay(500);
    moveServo(1, 50); delay(500);
    moveServo(2, 145); delay(500);
    moveServo(0, 120); delay(500);
    moveServo(3, 180); delay(500);
        
    delay(1000);
    moveServo(3, initialPositions[3]); delay(500);
    moveServo(2, 145); delay(500);  
    moveServo(1, initialPositions[1]); delay(500);
    moveServo(2, initialPositions[2]); delay(500);
    moveServo(0, initialPositions[0]); delay(500);
  }
  else if(commandIndex == 4) { // non recyclable
    moveServo(2, 135); delay(500);
    moveServo(1, 50); delay(500);
    moveServo(2, 175); delay(500);
    moveServo(1, 90); delay(500);
    moveServo(0, 10); delay(500);
    moveServo(3, 0); delay(500);
   
    delay(1000);
    moveServo(3, initialPositions[3]); delay(500);
    moveServo(0, initialPositions[0]); delay(500);
    moveServo(1, 50); delay(500);
    moveServo(2, 135); delay(500);
    moveServo(1, initialPositions[1]); delay(500);
    moveServo(2, initialPositions[2]); delay(500);
  }

  sequenceComplete = true;
  sequenceEnCours = false;
  Serial.println("Séquence terminée");

  // Après la séquence, si aucun bac n'est plein, LEDs blanches
  if (!bacPleinDetecte) {
    setLEDColor(LED_ATTENTE);
  }

  return true;
}

void loop() {
  static unsigned long dernierCheck = 0;

  // Vérification périodique des niveaux (toutes les 30 secondes)
  if (millis() - dernierCheck > 30000) {
    bool etatPrecedent = bacPleinDetecte;
    checkNiveauxPoubelles();

    if (etatPrecedent && !bacPleinDetecte && !sequenceEnCours) {
      setLEDColor(LED_ATTENTE);
    }

    dernierCheck = millis();
  }

  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');

    if (executeSequence(input)) {
      if (checkNiveauxPoubelles()) {
        Serial.println("⚠️ Tous les bacs sont pleins !");
      } else {
        Serial.println("✅ Certains bacs ont encore de la place.");
      }

      if (!bacPleinDetecte) {
        setLEDColor(LED_ATTENTE);
      }
    } else {
      Serial.println("❌ Commande non reconnue.");
      // Clignotement violet pour indiquer une erreur de commande
      for (int i = 0; i < 3; i++) {
        setLEDColor(LED_PROBLEME);
        delay(200);
        setLEDColor(LED_ATTENTE);
        delay(200);
      }
      setLEDColor(LED_ATTENTE);
    }
  }

  // Sécurité : si rien ne se passe, LEDs blanches (attente)
  if (!bacPleinDetecte && !sequenceEnCours) {
    setLEDColor(LED_ATTENTE);
  }
}
