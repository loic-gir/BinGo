#include <Servo.h>

Servo monServo;  // Objet servo
const int positionInitiale = 90;  // Position par défaut (90°)

// Définition des mots clés et des positions associées
const String mots[5] = {"plastique", "carton", "verre", "non recyclable", "metal"};
const int angles[5] = {0, 45, 74, 135, 180};

void setup() {
  Serial.begin(9600);
  monServo.attach(A4);  // Broche 11 pour le signal PWM
  monServo.write(positionInitiale);  // Initialisation à 90°
  Serial.println("Prêt. Envoyez un mot clé :");
  Serial.println("- plastique (0°)");
  Serial.println("- carton (45°)");
  Serial.println("- verre (74°)");
  Serial.println("- non recyclable (135°)");
  Serial.println("- metal (180°)");
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();  // Supprime les espaces et sauts de ligne

    // Vérification du mot clé et déplacement
    for (int i = 0; i < 5; i++) {
      if (input.equalsIgnoreCase(mots[i])) {
        Serial.print("Déplacement à ");
        Serial.print(angles[i]);
        Serial.println("°...");

        // Mouvement progressif vers l'angle cible
        int posActuelle = monServo.read();
        if (posActuelle < angles[i]) {
          for (int angle = posActuelle; angle <= angles[i]; angle++) {
            monServo.write(angle);
            delay(15);  // Ajuster pour vitesse
          }
        } else {
          for (int angle = posActuelle; angle >= angles[i]; angle--) {
            monServo.write(angle);
            delay(15);
          }
        }

        delay(1000);  // Pause à la position cible
        Serial.println("Retour à 90°...");
        
        // Retour progressif à 90°
        if (angles[i] < positionInitiale) {
          for (int angle = angles[i]; angle <= positionInitiale; angle++) {
            monServo.write(angle);
            delay(15);
          }
        } else {
          for (int angle = angles[i]; angle >= positionInitiale; angle--) {
            monServo.write(angle);
            delay(15);
          }
        }
        Serial.println("Prêt pour une nouvelle commande.");
        return;  // Sortie après traitement
      }
    }
    Serial.println("Mot clé non reconnu. Réessayez.");
  }
}