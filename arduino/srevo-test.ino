#include <Servo.h>

Servo monServo;  // Création de l'objet servo
bool doitBouger = false;  // Contrôle le mouvement

void setup() {
  Serial.begin(9600);  // Initialiser la communication série
  monServo.attach(11);  // Brancher le servo sur la broche 11
  monServo.write(0);   // Position initiale à 0°
  Serial.println("Envoyez 'oui' pour faire bouger le servo.");
}

void loop() {
  // Vérifier si l'utilisateur a envoyé "oui"
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();  // Supprimer les espaces et retours à la ligne
    if (input.equalsIgnoreCase("oui")) {
      doitBouger = true;
      Serial.println("Déplacement en cours...");
    }
  }

  // Si "oui" a été envoyé, faire bouger le servo
  if (doitBouger) {
    // Aller de 0° à 180°
    for (int pos = 0; pos <= 180; pos++) {
      monServo.write(pos);
      delay(15);
    }
    delay(1000);  // Pause à 180°

    // Revenir de 180° à 0°
    for (int pos = 180; pos >= 0; pos--) {
      monServo.write(pos);
      delay(15);
    }
    delay(1000);  // Pause à 0°
    
    doitBouger = false;  // Réinitialiser pour le prochain mouvement
    Serial.println("Déplacement terminé. Envoyez 'oui' pour recommencer.");
  }
}