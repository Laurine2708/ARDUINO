// ##### DECLARATIONS #####
#include "Arduino.h"
#include "DFRobotDFPlayerMini.h"
#include <SoftwareSerial.h>

SoftwareSerial mySoftwareSerial(/*rx =*/11, /*tx =*/12);
DFRobotDFPlayerMini myDFPlayer;

void CallAnswer(int buzzeractive, int ledactive, int numson){

      //ALLUME LA CROIX
      digitalWrite(ledactive, LOW);
      myDFPlayer.volume(30);  //Set volume value. From 0 to 30
      myDFPlayer.play(numson);  

      while (!digitalRead(6)==LOW && !digitalRead(7)==LOW) {
          //ATTEND  LA REPONSE TRUE/FALSE
      }

      //TRAITE LA REPONSE
      if(digitalRead(6)==LOW) Serial.println("false");
      if(digitalRead(7)==LOW) Serial.println("true");
      
      //ETEINT LE BUZZER ET LIBERE LE JEU
      digitalWrite(ledactive, HIGH); 
}

void setup() {

  delay(3000);

  Serial.begin(9600);
  mySoftwareSerial.begin(9600);
  myDFPlayer.begin(mySoftwareSerial);
  

  //Ouvre la communication des boutons poussoirs et leds
  //Buzzers
  pinMode(2, INPUT_PULLUP);  
  pinMode(3, INPUT_PULLUP); 
  pinMode(4, INPUT_PULLUP);
  pinMode(5, INPUT_PULLUP);   

  //Leds Buzzers
  pinMode(A2, OUTPUT);    
  pinMode(A3, OUTPUT);     
  pinMode(A4, OUTPUT);  
  pinMode(A5, OUTPUT); 

  //Boutons pupitre
  pinMode(6, INPUT_PULLUP);  //ROUGE
  pinMode(7, INPUT_PULLUP);  //VERT

  //Eteint les buzzers au démarrage
  digitalWrite(A2, HIGH);
  digitalWrite(A3, HIGH);
  digitalWrite(A4, HIGH);
  digitalWrite(A5, HIGH);



}

void loop() {
  //(LOGIQUE INVERSE)
  // HIGH = BOUTON POUSSOIR NON PRESSE
  // LOW = BP ACTIF

  //CAPTURE DE L'EVENEMENT
  if(digitalRead(2)==LOW || digitalRead(3)==LOW || digitalRead(4)==LOW || digitalRead(5)==LOW){
      //CALL EVENT REPONSE
      if (digitalRead(2) == LOW) {
    Serial.println("BUZZ:Joueur 1");
    CallAnswer(2, A2, 2);
  }

  if (digitalRead(3) == LOW) {
    Serial.println("BUZZ:Joueur 2");
    CallAnswer(3, A3, 3);
  }

  if (digitalRead(4) == LOW) {
    Serial.println("BUZZ:Joueur 3");
    CallAnswer(4, A4, 4);
  }

  if (digitalRead(5) == LOW) {
    Serial.println("BUZZ:Joueur 4");
    CallAnswer(5, A5, 5);
  }

  }



}

