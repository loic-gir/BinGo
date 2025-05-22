// #include <Servo.h>
// #include "HX711.h"

// // Définition des pins de l’Arduino pour le capteur de poids
// #define DT 2 // DT = Data (signal de données)
// #define SCK 3 // SCK = Serial Clock (signal d’horloge)
// HX711 balance;

// Définition des pins pour 5 capteurs ultrason (trig + echo)
const int trigPins[5] = {9, 11, 13, A0, A2}; // Choisis des pins numériques dispo
const int echoPins[5] = {8, 10, 12, A1, A3}; // Idem pour les echo

// // Création des objets Servo
// Servo servo1; // FS5106B
// Servo servo2; // FT7125M
// Servo servo3; // FT7125M
// Servo servo4; // FT7125M

void setup() {
  // 9600 = vitesse de communication => 9600 bits par seconde
  Serial.begin(9600); // begin pour activer la communication série, permet d’envoyer les Serial.print()

  // Initialisation des 5 capteurs ultrason
  for (int i = 0; i < 5; i++) {
    pinMode(trigPins[i], OUTPUT); // déclencheur, Arduino envoie une impulsion
    pinMode(echoPins[i], INPUT); // récepteur, Arduino reçoit un signal du capteur
  }

  // // Initialisation du capteur de poids
  // balance.begin(DT, SCK); // initialise la communication entre l’Arduino et HX711 
  // balance.set_scale(); // Applique un facteur d’échelle (ou brut si vide)
  // // trouver le bon facteur d’échelle => 
  // // Mets un objet de poids connu (ex : 1 kg) sur la balance
  // // Lis la valeur brute avec : Serial.println(balance.get_units(10));
  // // Ajuste la valeur dans set_scale(...) jusqu’à ce que le résultat corresponde au poids réel
  // balance.tare(); // Réinitialise la balance à zéro

  // // Attachement des servomoteurs aux pins correspondants
  // servo1.attach(4);
  // servo2.attach(5);
  // servo3.attach(6);
  // servo4.attach(7);
}

void loop() {
  // Variable pour savoir si un sac est plein
  bool estPlein[5] = {false, false, false, false, false}; 

  for (int i = 0; i < 5; i++) {
    // Envoie du signal de déclenchement
    digitalWrite(trigPins[i], LOW);   // 1. On s'assure que le trigger est à 0V
    delayMicroseconds(2);         // 2. Petit délai
    digitalWrite(trigPins[i], HIGH);  // 3. On envoie une impulsion (5V)
    delayMicroseconds(10);        // 4. Pendant 10 microsecondes
    digitalWrite(trigPins[i], LOW);   // 5. On coupe l’impulsion

    // Réception du signal
    // mesure combien de temps (en microsecondes) le pin echoPin reste à l’état HIGH (5V)
    long duration = pulseIn(echoPins[i], HIGH);
    // Le son voyage à ~340 m/s, soit 0.034 cm/µs
    float distance = duration * 0.034 / 2;

    Serial.print("Capteur ");
    Serial.print(i + 1);
    Serial.print(" : ");
    Serial.print(distance);
    Serial.println(" cm");

    // Si distance < 25 cm 
    if (distance > 0 && distance < 25) {
      estPlein[i] = true;
    }
    delay(1500);
  }

  // // Lecture du poids (bsn calibrer avant)
  // float poids = balance.get_units(5); // faire 5 mesures et renvoyer la moyenne

  // Serial.print("Poids: ");
  // Serial.println(poids);

  // // Contrôle des servomoteurs en fonction des mesures
  // int valeur = random(1, 6); // 6 est exclu, donc ça donne 1 à 5 inclus

  // if (estPlein[valeur] && poids < 0.5) { // 25 cm, 0.5 kg
  //   // servo.write(angle de 0° à 180°)
  //   servo1.write(90);
  //   servo2.write(90);
  //   servo3.write(90);
  //   servo4.write(90);
  // } else {
  //   servo1.write(0);
  //   servo2.write(0);
  //   servo3.write(0);
  //   servo4.write(0);
  // }

  delay(500);
}

// Ouvre le Moniteur Série (Ctrl + Shift + M)
