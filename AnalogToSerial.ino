/*
  Analog input, serial output
 
 The circuit:
 * connect a photoresistor between analog pin 0 and +5V
 * connect a 10K resistor between analog pin 0 and ground

 */

// These constants won't change.  They're used to give names
// to the pins used:
const int analogInPin = A0;  // Analog input pin

int sensorValue = 0;        // value read from the pot

void setup() {
  // initialize serial communications at 9600 bps:
  Serial.begin(9600); 
}

void loop() {
  // read the analog in value:
  sensorValue = analogRead(analogInPin);            

  // print the results to the serial monitor:
  Serial.println(sensorValue);      

  // wait 10 seconds before the next loop
  delay(10000);                     
}
