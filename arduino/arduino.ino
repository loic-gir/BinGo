#include <Servo.h>

Servo servos[4];
const int servoPins[4] = {A0, A1, A2, A3};
const int initPos[4] = {90, 8, 120, 90}; 

const String mots[5] = {"metal", "carton", "verre", "plastique", "non recyclable"};
const int posServo[2][4] = {
  {90 , 0, 110,180 },    // metal
  {90, 8, 120, 0},   // carton
};

const int trigPins[5] = {2, 4, 6, 8, A5};
const int echoPins[5] = {3, 5, 7, 12, A4};
const int DISTANCE_PLEIN = 10;

bool sequenceComplete = false;

void setup() {
  Serial.begin(9600);
  
  for (int i = 0; i < 5; i++) {
    pinMode(trigPins[i], OUTPUT);
    pinMode(echoPins[i], INPUT);
  }

  for(int i = 0; i < 4; i++) {
    servos[i].attach(servoPins[i]);
    servos[i].write(initPos[i]);
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
  
  long duration = pulseIn(echoPin, HIGH);
  return duration * 0.034 / 2;
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
  
  for (int i = 0; i < 5; i++) {
    long distance = readDistance(trigPins[i], echoPins[i]);
    Serial.print("Bac ");
    Serial.print(i + 1);
    Serial.print(": ");
    
    if (distance < DISTANCE_PLEIN) {
      Serial.println("PLEIN");
    } else {
      Serial.print(distance);
      Serial.println(" cm");
      tousPleins = false;
    }
    delay(100);
  }
  
  return tousPleins;
}

bool executeSequence(String input) {
  input.trim();
  sequenceComplete = false;
  int commandIndex = -1;

  for (int i = 0; i < 5; i++) {
    if (input.equalsIgnoreCase(mots[i])) {
      commandIndex = i;
      break;
    }
  }

  if (commandIndex == -1) return false;

  Serial.println("\nDébut de la séquence...");

  if(commandIndex==0){
    moveServo(0,posServo[commandIndex][0]);delay(500);
    moveServo(1,posServo[commandIndex][1]);delay(500);
    moveServo(2,posServo[commandIndex][2]);delay(500);
    moveServo(3,posServo[commandIndex][3]);delay(500);

    delay(1000);
    moveServo(3,initPos[3]); delay(500);
    moveServo(2, initPos[2]); delay(500);
    moveServo(1, initPos[1]); delay(500);
    moveServo(0, initPos[0]); delay(500);
  }
  if(commandIndex==1){
    moveServo(0,posServo[commandIndex][0]);delay(500);
    moveServo(1,posServo[commandIndex][1]);delay(500);
    moveServo(2,posServo[commandIndex][2]);delay(500);
    moveServo(3,posServo[commandIndex][3]);delay(500);

    delay(1000);
    moveServo(3,initPos[3]); delay(500);
    moveServo(2, initPos[2]); delay(500);
    moveServo(1, initPos[1]); delay(500);
    moveServo(0, initPos[0]); delay(500);
  }
  if(commandIndex==2){
    moveServo(2, 135); delay(500);
    moveServo(1,50);delay(500);
    moveServo(2,175);delay(500);
    moveServo(1,90);delay(500);
    moveServo(0,170);delay(500);
    moveServo(3,110);delay(500);

    delay(1000);
    moveServo(3,initPos[3]); delay(500);
    moveServo(0, initPos[0]); delay(500);
    moveServo(1,50);delay(500);
    moveServo(2,135); delay(500);
    moveServo(1,initPos[1]);delay(500);
    moveServo(2, initPos[2]); delay(500);
  }
  if (commandIndex == 3) {
    // Cas spécial : plastique => ordre 0 → 2 → 1 → 3
    moveServo(2, 135); delay(500);
    moveServo(1,50);delay(500);
    moveServo(2,145);delay(500);
    moveServo(0,120);delay(500);
    moveServo(3,180);delay(500);
        
    delay(1000);
    moveServo(3, initPos[3]); delay(500);
    moveServo(2, 145); delay(500);  
    moveServo(1, initPos[1]); delay(500);
    moveServo(2, initPos[2]); delay(500);
    moveServo(0, initPos[0]); delay(500);
    
  }if(commandIndex==4){
    moveServo(2, 135); delay(500);
    moveServo(1,50);delay(500);
    moveServo(2,175);delay(500);
    moveServo(1,90);delay(500);
    moveServo(0,10);delay(500);
    moveServo(3,0);delay(500);
   
    delay(1000);
    moveServo(3,initPos[3]); delay(500);
    moveServo(0, initPos[0]); delay(500);
    moveServo(1,50);delay(500);
    moveServo(2,135); delay(500);
    moveServo(1,initPos[1]);delay(500);
    moveServo(2, initPos[2]); delay(500);
  }
   

  sequenceComplete = true;
  Serial.println("Séquence terminée");
  return true;
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    
    if (executeSequence(input)) {
      if (checkNiveauxPoubelles()) {
        Serial.println("⚠️ Tous les bacs sont pleins !");
      } else {
        Serial.println("✅ Certains bacs ont encore de la place.");
      }
    } else {
      Serial.println("❌ Commande non reconnue.");
    }
  }
}
