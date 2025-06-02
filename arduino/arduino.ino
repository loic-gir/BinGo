// #include <Servo.h>
// #include "HX711.h"
#define NB_bac 5

// Configuration des distances
#define HAUTEUR_BAC_CM 100  // hauteur totale d’un bac => 0% plein
#define DISTANCE_MIN_CM 10  // distance minimale => 100% plein

// // Définition des pins de l’Arduino pour le capteur de poids
// #define DT 2 // DT = Data (signal de données)
// #define SCK 3 // SCK = Serial Clock (signal d’horloge)
// HX711 balance;

// Définition des pins pour 5 capteurs ultrason (trig + echo)
const int trigPins[NB_bac] = {2,3,4,5,6}; // Choisis des pins numériques dispo
const int echoPins[NB_bac] = {7,8,9,10,11}; // Idem pour les echo

// Variable pour savoir si un sac est plein
bool estPlein[NB_bac] = {false, false, false, false, false}; 

float pourcentages[NB_bac];  // Pour stocker les % de remplissage

// // Création des objets Servo
Servo servo1; // FS5106B
// Servo servo2; // FT7125M
// Servo servo3; // FT7125M
// Servo servo4; // FT7125M

const int angleS1[NB_bac] = {0, 45, 74, 135, 180}; 
// const int angleS2[NB_bac] = {90, 90, 0, 180, 90}; 
// const int angleS3[NB_bac] = {90, 0, 90, 90, 180}; 
// const int angleS4[NB_bac] = {90, 180, 0, 90, 90}; 

void bougerServo(Servo& monServo, int angleCible) {
  int posActuelle = monServo.read();
  if (posActuelle < angleCible) {
    for (int angle = posActuelle; angle <= angleCible; angle++) {
      monServo.write(angle);
      delay(15);
    }
  } else {
    for (int angle = posActuelle; angle >= angleCible; angle--) {
      monServo.write(angle);
      delay(15);
    }
  }
  delay(300); // Pause à destination
}

float calculerPourcentage(float distance) {
  if (distance <= DISTANCE_MIN_CM) return 100.0;
  if (distance >= HAUTEUR_BAC_CM) return 0.0;
  return ((HAUTEUR_BAC_CM - distance) / (HAUTEUR_BAC_CM - DISTANCE_MIN_CM)) * 100.0;
}

float calculDistance(int numBac) { // de 0 a 4
  // Envoie du signal de déclenchement
  digitalWrite(trigPins[numBac], LOW);   // 1. On s'assure que le trigger est à 0V
  delayMicroseconds(2);                  // 2. Petit délai
  digitalWrite(trigPins[numBac], HIGH);  // 3. On envoie une impulsion (5V)
  delayMicroseconds(10);                  // 4. Pendant 10 microsecondes
  digitalWrite(trigPins[numBac], LOW);   // 5. On coupe l’impulsion

  // Réception du signal
  // mesure combien de temps (en microsecondes) le pin echoPin reste à l’état HIGH (5V)
  long duration = pulseIn(echoPins[numBac], HIGH);
  // Le son voyage à ~340 m/s, soit 0.034 cm/µs
  float distance = duration * 0.034 / 2;

  // a supprimer apres test
  Serial.print("Capteur ");
  Serial.print(numBac + 1); // de 1 a 5
  Serial.print(" : ");
  Serial.print(distance);
  Serial.println(" cm");

  // Si distance < 10 cm 
  if (distance < 10) {
    estPlein[numBac] = true;
  }
  else estPlein[numBac] = false;

  return distance;
}

void affichageCSV(){
  // Affichage sous forme CSV
  Serial.print("forSite"); // Ajout du mot fixe
  for (int i = 0; i < NB_bac; i++) {
    Serial.print(pourcentages[i], 0); // 0 chiffre après virgule
    if (i < NB_bac - 1) Serial.print(",");
  }
  Serial.println();
}

void setup() {
  // 9600 = vitesse de communication => 9600 bits par seconde
  Serial.begin(9600); // begin pour activer la communication série, permet d’envoyer les Serial.print()

  // Initialisation des 5 capteurs ultrason
  for (int i = 0; i < NB_bac; i++) {
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

  // Attachement des servomoteurs aux pins correspondants
  servo1.attach(A1);
  // servo2.attach(A2);
  // servo3.attach(A3);
  // servo4.attach(A4);

  // Tous à 90° au départ
  bougerServo(servo1,90);
  // bougerServo(servo2,90);
  // bougerServo(servo3,90);
  // bougerServo(servo4,90);

  for (int i = 0; i < NB_bac; i++) {
    float distance = calculDistance(i);
    pourcentages[i] = calculerPourcentage(distance);
    delay(50);
  }
  affichageCSV();

}

void loop() {
  // // Lecture du poids (bsn calibrer avant)
  // float poids = balance.get_units(5); // faire 5 mesures et renvoyer la moyenne

  // Serial.print("Poids: ");
  // Serial.println(poids);

  // Contrôle des servomoteurs en fonction des mesures (type dechet)
  int valeur = random(0, NB_bac); // 5 est exclu, donc ça donne 0 à 4 inclus

  // if (!estPlein[valeur] && poids < 0.5) { // 0.5 kg
  if (!estPlein[valeur]) { // test sans poids
    Serial.print("Déplacement vers bac ");
    Serial.println(valeur);

    // Mouvement séquentiel des bras
    bougerServo(servo1, angleS1[valeur]);
    // bougerServo(servo2, angleS2[valeur]);
    // bougerServo(servo3, angleS3[valeur]);
    // bougerServo(servo4, angleS4[valeur]);

    float nvDistance = calculDistance(valeur);
    pourcentages[valeur] = calculerPourcentage(nvDistance);
    affichageCSV(); // pour affichage site
    
  } else {
    Serial.println("Ce bac est plein, on ne déplace pas.");
  }

  delay(500);
}

// Ouvre le Moniteur Série (Ctrl + Shift + M)
