#define NB_CAPTEURS 5
#include <Servo.h>

// Déclaration des servomoteurs
Servo servos[4];
const int servoPins[4] = { A0, A1, A2, A3 };
const int initialPositions[4] = { 90, 45, 90, 0 };

// Configuration des mots-clés
const String mots[5] = { "plastique", "carton", "verre", "non recyclable", "metal" };
const int anglesServo1[5] = { 0, 45, 74, 135, 180 };

// Configuration des capteurs à ultrasons
const int trigPins[NB_CAPTEURS] = { 2, 3, 4, 5, 6 };
const int echoPins[NB_CAPTEURS] = { 7, 8, 9, 10, 11 };

// Variables d'état
bool sequenceComplete = false;
const int DISTANCE_PLEIN = 10;  // Seuil en cm pour considérer le bac plein
const int HAUTEUR_BAC_CM = 100;

float pourcentages[NB_bac];  // Pour stocker les % de remplissage

float calculerPourcentage(float distance) {
  if (distance <= DISTANCE_PLEIN) return 100.0;
  if (distance >= HAUTEUR_BAC_CM) return 0.0;
  return ((HAUTEUR_BAC_CM - distance) / (HAUTEUR_BAC_CM - DISTANCE_PLEIN)) * 100.0;
}

void setup() {
  Serial.begin(9600);

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
  Serial.println("- plastique");
  Serial.println("- carton");
  Serial.println("- verre");
  Serial.println("- non recyclable");
  Serial.println("- metal");
}

long readDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  long duration = pulseIn(echoPin, HIGH);
  return duration * 0.034 / 2;  // Conversion en cm
}

void moveServo(int servoNum, int targetAngle, int delayTime = 15) {
  int currentPos = servos[servoNum].read();

  if (currentPos < targetAngle) {
    for (int angle = currentPos; angle <= targetAngle; angle++) {
      servos[servoNum].write(angle);
      delay(delayTime);
    }
  } else {
    for (int angle = currentPos; angle >= targetAngle; angle--) {
      servos[servoNum].write(angle);
      delay(delayTime);
    }
  }
}

bool checkNiveauxPoubelles() {
  bool tousPleins = true;
  Serial.println("\nVérification des niveaux:");

  for (int i = 0; i < NB_CAPTEURS; i++) {
    long distance = readDistance(trigPins[i], echoPins[i]);
    Serial.print("Bac ");
    Serial.print(i + 1);
    Serial.print(": ");

    pourcentages[i] = calculerPourcentage(distance);

    if (distance < DISTANCE_PLEIN) {
      Serial.println("PLEIN");
    } else {
      Serial.print(distance);
      Serial.println(" cm");
      tousPleins = false;
    }
    delay(100);  // Pause entre les mesures
  }

  Serial.print("forSite");  // Ajout du mot fixe pour eviter les infos inutils
  for (int i = 0; i < NB_CAPTEURS; i++) {
    Serial.print(pourcentages[i], 0);  // 0 chiffre après virgule
    if (i < NB_bac - 1) Serial.print(",");
  }
  Serial.println();

  return tousPleins;
}

bool executeSequence(String input) {
  input.trim();
  sequenceComplete = false;

  for (int i = 0; i < 5; i++) {
    if (input.equalsIgnoreCase(mots[i])) {
      Serial.println("\nDébut de la séquence...");

      // Mouvement des servos
      moveServo(0, anglesServo1[i]);
      delay(1000);
      moveServo(1, 90);
      delay(1000);
      moveServo(2, (i % 2 == 0) ? 25 : 45);
      delay(1000);
      moveServo(3, 180);
      delay(1000);

      // Retour aux positions initiales
      moveServo(3, initialPositions[3]);
      delay(500);
      moveServo(2, initialPositions[2]);
      delay(500);
      moveServo(1, initialPositions[1]);
      delay(500);
      moveServo(0, initialPositions[0]);

      sequenceComplete = true;
      Serial.println("Séquence terminée");
      return true;
    }
  }
  return false;
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');

    if (executeSequence(input)) {
      // Après la séquence, vérifier les niveaux
      if (checkNiveauxPoubelles()) {
        Serial.println("Attention: Tous les bacs sont pleins!");
      } else {
        Serial.println("Certains bacs ont encore de la place");
      }
    } else {
      Serial.println("Commande non reconnue");
    }
  }
}
