// [아두이노] 통합 제어 코드
// 가스, 불꽃, 열화상 신호 중 하나라도 감지되면 작동

#include <Servo.h> 

// === 핀 설정 ===
const int PIN_GAS = 2;       // 가스 센서
const int PIN_FLAME = 3;     // 불꽃 센서
const int PIN_PUMP = 7;      // 워터 펌프 릴레이
const int PIN_FAN = 8;       // 팬 릴레이
const int PIN_SERVO = 9;     // 창문 서보모터

Servo myservo; 

// === 상태 변수 ===
bool fire_thermal = false; // 열화상 감지 여부 (라즈베리파이에서 받음)
bool fire_gas = false;     // 가스 감지 여부
bool fire_flame = false;   // 불꽃 감지 여부

void setup() {
  Serial.begin(9600); // 통신 시작
  
  // 핀 모드 설정
  pinMode(PIN_GAS, INPUT);
  pinMode(PIN_FLAME, INPUT);
  pinMode(PIN_PUMP, OUTPUT);
  pinMode(PIN_FAN, OUTPUT);
  
  myservo.attach(PIN_SERVO);
  myservo.write(0); // 창문 닫기 (초기화)

  // 릴레이 초기화 (High가 꺼짐이라고 가정)
  digitalWrite(PIN_PUMP, HIGH);
  digitalWrite(PIN_FAN, HIGH);
}

void loop() {
  // 1. 라즈베리 파이로부터 열화상 신호 수신
  if (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '1') fire_thermal = true;       // 열화상: 화재!
    else if (c == '0') fire_thermal = false; // 열화상: 정상
  }

  // 2. 아두이노 센서 읽기 (보통 감지되면 LOW=0 출력)
  // 센서마다 다를 수 있으니 반대로 동작하면 == HIGH로 바꾸세요.
  fire_gas = (digitalRead(PIN_GAS) == LOW);
  fire_flame = (digitalRead(PIN_FLAME) == LOW);

  // 3. 화재 판단 (OR 조건)
  bool is_fire = (fire_thermal || fire_gas || fire_flame);

  // 4. 작동 제어
  if (is_fire) {
    // [화재 발생]
    digitalWrite(PIN_PUMP, LOW); // 펌프 ON
    digitalWrite(PIN_FAN, LOW);  // 팬 ON
    myservo.write(90);           // 창문 열기
  } else {
    // [정상 상태]
    digitalWrite(PIN_PUMP, HIGH); // 펌프 OFF
    digitalWrite(PIN_FAN, HIGH);  // 팬 OFF
    myservo.write(0);             // 창문 닫기
  }

  // 5. 라즈베리 파이로 현재 센서 상태 보고 (대시보드 표시용)
  // 형식: "가스상태,불꽃상태" (예: "1,0" -> 가스O, 불꽃X)
  Serial.print(fire_gas);
  Serial.print(",");
  Serial.println(fire_flame);

  delay(100); // 안정적인 통신을 위해 약간 대기
}
