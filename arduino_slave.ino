#include <Servo.h> 

// === 1. 설정값 ===
const int ANGLE_CLOSE = 25;    // 닫힘 각도
const int ANGLE_OPEN = 120;    // 열림 각도
const int RECOVERY_DELAY = 2000; // 상황 종료 후 물 빠지는 대기 시간 (2초)

// === 2. 핀 번호 설정 ===
const int PIN_GAS = 2;       // 가스 센서
const int PIN_FLAME = 3;     // [수정] 불꽃 센서 핀 번호 추가 (연결된 핀으로 바꾸세요)
const int PIN_PUMP = 7;      // 워터 펌프 (릴레이)
const int PIN_SERVO = 9;     // 창문 서보모터

Servo myservo;

// 상태 변수
bool is_fire_active = false; // 화재 상태 추적용

void setup() {
  Serial.begin(9600); // 파이썬과 속도 일치 (9600)
  
  pinMode(PIN_GAS, INPUT);
  pinMode(PIN_FLAME, INPUT);
  pinMode(PIN_PUMP, OUTPUT);
  
  myservo.attach(PIN_SERVO);
  
  // === 초기화 (닫힘/꺼짐) ===
  // 릴레이가 Low Trigger(LOW일 때 켜짐) 방식이라고 가정하고 HIGH(꺼짐)로 시작
  digitalWrite(PIN_PUMP, HIGH); 
  myservo.write(ANGLE_CLOSE);
}

void loop() {
  // ------------------------------------------------
  // 1. 센서값 읽기 (감지되면 1, 아니면 0)
  // ------------------------------------------------
  // [중요] 사용하시는 센서가 감지 시 LOW(0V)를 내보내는 타입이라고 가정했습니다.
  // 만약 감지 시 HIGH(5V)가 나오는 센서라면 "== LOW"를 "== HIGH"로 고치세요.
  int gas_val = (digitalRead(PIN_GAS) == LOW) ? 1 : 0;
  int flame_val = (digitalRead(PIN_FLAME) == LOW) ? 1 : 0;

  // ------------------------------------------------
  // 2. 파이썬으로 데이터 전송 (보고)
  // ------------------------------------------------
  // 형식: "가스,불꽃" (예: 1,0) -> 줄바꿈(println) 필수!
  Serial.print(gas_val);
  Serial.print(",");
  Serial.println(flame_val);

  // ------------------------------------------------
  // 3. 파이썬 명령 듣고 행동하기 (실행)
  // ------------------------------------------------
  if (Serial.available() > 0) {
    char command = Serial.read();

    // [명령 '1': 화재 발생!] 
    if (command == '1') { 
      if (!is_fire_active) {
        is_fire_active = true; 
        
        // 화재 발생 시 동작
        myservo.write(ANGLE_OPEN);    // 창문 열기
        digitalWrite(PIN_PUMP, LOW);  // 펌프 켜기 (Low Trigger: LOW가 ON)
      }
    }
    
    // [명령 '0': 상황 종료/안전]
    else if (command == '0') {
      
      // 화재 상태였다가 꺼지는 경우에만 복구 절차 실행
      if (is_fire_active == true) {
        // 1. 펌프 즉시 끄기
        digitalWrite(PIN_PUMP, HIGH); // Relay OFF
        
        // 2. 잔여 물기 제거 대기 (파이썬이 멈추지 않게 딜레이는 신중히 사용)
        // 여기서 delay를 쓰면 2초간 센서값을 못 보냅니다. 
        // 괜찮다면 유지하셔도 됩니다.
        delay(RECOVERY_DELAY); 
        
        // 3. 창문 닫기
        myservo.write(ANGLE_CLOSE); 
        
        is_fire_active = false; // 상태 해제
      }
      else {
        // 평소 상태 유지
        digitalWrite(PIN_PUMP, HIGH);
        myservo.write(ANGLE_CLOSE);
      }
    }
  }
  
  // 통신 속도 조절 (너무 빠르면 파이썬 버퍼가 넘침)
  delay(300); 
}
