#define NB_CAPTEURS 4
#include <Servo.h>

Servo monServo;  // Création de l'objet servo

// Définir les pins TRIG et ECHO
int trigPins[NB_CAPTEURS] = {2, 3, 4, 5};
int echoPins[NB_CAPTEURS] = {6, 7, 8, 9};

long readDistance(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  
  long duration = pulseIn(echoPin, HIGH);
  long distance = duration * 0.034 / 2; // Convertir en cm
  return distance;
}

void setup() {
  delay(2000);
  Serial.begin(9600);
  for (int i = 0; i < NB_CAPTEURS; i++) {
    pinMode(trigPins[i], OUTPUT);
    pinMode(echoPins[i], INPUT);
  }
  monServo.attach(11);
}

void loop() {
  // 1. Faire l'aller-retour du servo
  for (int pos = 0; pos <= 180; pos++) {
    monServo.write(pos);
    delay(15);
  }

  delay(1000); // Pause à 180°

  for (int pos = 180; pos >= 0; pos--) {
    monServo.write(pos);
    delay(15);
  }

  delay(1000); // Pause à 0°

  // 2. Lire et afficher les distances des capteurs
  for (int i = 0; i < NB_CAPTEURS; i++) {
    long distance = readDistance(trigPins[i], echoPins[i]);
    Serial.print("Capteur ");
    Serial.print(i + 1);
    Serial.print(" : ");
    if (distance < 10) {
      Serial.println("Le bac est plein !");
    } else {
      Serial.print(distance);
      Serial.println(" cm");
    }
  }

  // 3. Attendre pour que le cycle se répète toutes les minutes
  delay(30000); // 30 secondes pour compléter les ~60 sec cycle total
}
