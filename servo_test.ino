#include <Servo.h>

Servo myservo;  // 서보모터 객체 생성

// 서보모터 핀 번호 (회로에 맞게 수정하세요, 보통 9번)
const int SERVO_PIN = 9; 

void setup() {
  Serial.begin(9600); // 시리얼 통신 시작
  
  myservo.attach(SERVO_PIN); // 서보모터 연결
  
  // [초기 상태] 로딩 시 90도로 설정
  myservo.write(90); 
  
  Serial.println("=== 서보모터 각도 제어 모드 ===");
  Serial.println("초기화 완료: 90도 (중간)");
  Serial.println("1: 30도 (닫힘 쪽)");
  Serial.println("2: 90도 (중간)");
  Serial.println("3: 140도 (열림 쪽)");
}

void loop() {
  // 시리얼 모니터에서 데이터가 들어오면
  if (Serial.available() > 0) {
    char command = Serial.read(); // 문자 읽기 (1, 2, 3 중 하나)
    
    // 엔터키나 공백 등은 무시하기 위한 처리
    if (command == '\n' || command == '\r') return;

    if (command == '1') {
      myservo.write(30);
      Serial.println("명령: 1 -> 30도로 이동");
    }
    else if (command == '2') {
      myservo.write(90);
      Serial.println("명령: 2 -> 90도로 이동 (복귀)");
    }
    else if (command == '3') {
      myservo.write(140);
      Serial.println("명령: 3 -> 140도로 이동 (활짝)");
    }
  }
}
