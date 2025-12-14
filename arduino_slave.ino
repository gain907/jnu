#include <Servo.h> 

// === 1. 설정값 ===
const int ANGLE_CLOSE = 25;    // 닫힘 각도
const int ANGLE_OPEN = 120;    // 열림 각도
const int RECOVERY_DELAY = 2000; // 2초 대기

// === 2. 핀 번호 ===
const int PIN_GAS = 2;       // 가스 센서
const int PIN_FLAME = 3;     // 불꽃 센서
const int PIN_PUMP = 7;      // 워터 펌프 (릴레이)
const int PIN_SERVO = 9;     // 창문 서보모터

Servo myservo;

// 상태 변수
bool is_fire_active = false; // 현재 불이 켜져있는 상태인지 기억하는 변수

void setup() {
  Serial.begin(9600);
  
  pinMode(PIN_GAS, INPUT);
  pinMode(PIN_FLAME, INPUT);
  pinMode(PIN_PUMP, OUTPUT);
  
  myservo.attach(PIN_SERVO);
  
  // 초기화 (닫힘/꺼짐)
  digitalWrite(PIN_PUMP, HIGH); // 릴레이 OFF (High Trigger 기준)
  myservo.write(ANGLE_CLOSE);
}

void loop() {
  // ------------------------------------------------
  // 1. 센서값 읽어서 라즈베리 파이로 보내기 (보고)
  // ------------------------------------------------
  // (보통 센서는 감지되면 LOW(0)입니다. 만약 반대면 == HIGH로 고치세요)
  int gas_val = (digitalRead(PIN_GAS) == LOW) ? 1 : 0;
  int flame_val = (digitalRead(PIN_FLAME) == LOW) ? 1 : 0;

  // "가스,불꽃" 형태로 전송 (예: 1,0)
  Serial.print(gas_val);
  Serial.print(",");
  Serial.println(flame_val);

  // ------------------------------------------------
  // 2. 라즈베리 파이 명령 듣고 행동하기 (실행)
  // ------------------------------------------------
  if (Serial.available() > 0) {
    char command = Serial.read();

    // [명령: 화재 발생!] 
    if (command == '1') { 
      // 이미 화재 모드라면 중복 실행 방지
      if (!is_fire_active) {
        is_fire_active = true; 
      }
      // 무조건 수행 (안전 제일)
      myservo.write(ANGLE_OPEN);    // 창문 120도 열기
      digitalWrite(PIN_PUMP, LOW);  // 펌프 켜기 (Relay ON)
    }
    
    // [명령: 상황 종료/안전]
    else if (command == '0') {
      
      // 방금까지 불이 났었다면? (복구 시퀀스 실행)
      if (is_fire_active == true) {
        // 1. 펌프 즉시 끄기
        digitalWrite(PIN_PUMP, HIGH);
        
        // 2. 2초 기다리기 (물 빠지는 시간)
        delay(RECOVERY_DELAY); 
        
        // 3. 창문 닫기
        myservo.write(ANGLE_CLOSE); // 25도
        
        is_fire_active = false; // 상태 해제
      }
      else {
        // 원래 안전했으면 그냥 계속 닫아둠
        digitalWrite(PIN_PUMP, HIGH);
        myservo.write(ANGLE_CLOSE);
      }
    }
  }
  
  delay(100); // 통신 안정화 대기
}
