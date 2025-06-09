#include <Servo.h>

Servo servoBase;
Servo servoPoignet;

//Bac 1  : Position horizontale : 135 ; Inclinaison plateau :  135
//Bac 2 : Position horizontale : 45 ; Inclinaison plateau :  135
//Bac 3 : Position horizontale : 30 ; Inclinaison plateau : 45 
//Bac 4 : Position horizontale :  90 ; Inclinaison plateau :  45
//Bac 5 : Position horizontale : 150 ; Inclinaison plateau :  45

const int angleBase[5]     = {135, 45, 30, 90, 150};  // Position horizontale du bras
const int angleIncline[5]  = {135, 135, 45, 45, 45};  // Inclinaison du plateau


void setup() {
  servoBase.attach(9);      
  servoPoignet.attach(10);

  servoBase.write(0);
  servoPoignet.write(angleDefaut);
  
  Serial.begin(9600);
}

void loop() {
  if (Serial.available() > 0) {
    int bac = Serial.parseInt();
    if (bac >= 0 && bac < 5) {
        servoBase.write(angleBase[bac]);
        delay(1000);
        servoPoignet.write(angleIncline[bac]);  // Avant ou arrière selon bac
        delay(1000);
      
      servoPoignet.write(angleDefaut);
      delay(500);

    } 
  }
}
