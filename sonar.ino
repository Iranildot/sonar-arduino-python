#include <Servo.h>
#include <NewPing.h>

#define TRIGGER_PIN 2
#define ECHO_PIN 3
#define SERVO_PIN 9

String sonar_state = "OFF";
String sonar_mode = "BOUNCE";
int sonar_angle = 0;
int sonar_step = 1;
unsigned long sonar_range = 250;
bool data_were_sent = false;
unsigned long object_distance = 0;

Servo servo;  // Cria um objeto Servo
NewPing sonar(TRIGGER_PIN, ECHO_PIN, sonar_range);

void send_data_to_serial(void);
void move_servo(void);
void servo_settings(void);

void setup() {
  Serial.begin(9600);
  servo.attach(SERVO_PIN);  // Conecta o servo ao pino digital 9
}

void loop() {

  if (!data_were_sent and sonar_state.equals("ON")){
    object_distance = sonar.ping_cm(sonar_range);
    send_data_to_serial();
    move_servo();
  }

  if (Serial.available()){
    String serial_response = Serial.readStringUntil(':');

    if (serial_response.equals("ON")){

      sonar_state = "ON";
      sonar_mode = Serial.readStringUntil(':');
      sonar_step = sonar_step < 0 ? - Serial.readStringUntil(':').toInt() : Serial.readStringUntil(':').toInt();
      sonar_range = Serial.readStringUntil(':').toInt();
      servo_settings();

    } else if (serial_response.equals("OFF")){

      sonar_state = "OFF";
      data_were_sent = false;

    } else if (serial_response.equals("NEXT")){

      data_were_sent = false;

    } else if (serial_response.equals("UPDATE")){

      sonar_mode = Serial.readStringUntil(':');
      sonar_step = sonar_step < 0 ? - Serial.readStringUntil(':').toInt() : Serial.readStringUntil(':').toInt();
      sonar_range = Serial.readStringUntil(':').toInt();
      servo_settings();
    }
  }

  delay(10);
}

void send_data_to_serial(void){
  
  Serial.print(object_distance / 100.0);
  Serial.print(":");
  Serial.println(sonar_angle);

  data_were_sent = true;

}

void move_servo(void){

  sonar_angle += sonar_step;

  if (sonar_mode.equals("BOUNCE")){
    if (sonar_angle >= 180) {
      sonar_angle = 180;
      sonar_step = - sonar_step;
    } 
    if (sonar_angle <= 0) {
      sonar_angle = 0;
      sonar_step = - sonar_step;
    }
  } else if (sonar_mode.equals("0")){
    if (sonar_angle >= 180){
      sonar_angle = 0;
    }
  } else{
    if (sonar_angle <= 0){
      sonar_angle = 180;
    }
  }

  servo.write(sonar_angle);
}

void servo_settings(void){
  if (sonar_mode.equals("0")){
    if (sonar_step < 0){
      sonar_step = - sonar_step;
    }
  } else if (sonar_mode.equals("180")){
    if (sonar_step > 0){
      sonar_step = - sonar_step;
    }
  }
}