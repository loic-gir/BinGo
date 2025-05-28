#define NB_CAPTEURS 4

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
  Serial.begin(9600);
  for (int i = 0; i < NB_CAPTEURS; i++) {
    pinMode(trigPins[i], OUTPUT);
    pinMode(echoPins[i], INPUT);
  }
}

void loop() {
  for (int i = 0; i < NB_CAPTEURS; i++) {
    long distance = readDistance(trigPins[i], echoPins[i]);
    Serial.print("Capteur ");
    Serial.print(i+1);
    Serial.print(" : ");
    if (distance < 10) {
      Serial.println("Le bac est plein !");
    } else {
      Serial.print(distance);
      Serial.println(" cm");
    }
  }
  delay(30000); // Attendre 1 minute
}
