import serial
import time

print("=== 아두이노 시리얼 통신 테스트 시작 ===")

# 1. 아두이노 연결 설정
# '/dev/ttyACM0'는 보통 라즈베리 파이 USB 포트 이름입니다.
# 안 되면 '/dev/ttyUSB0' 으로 바꿔보세요.
try:
    arduino = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
    time.sleep(2) # 아두이노가 연결되면 재부팅되므로 2초 기다림
    print("성공: 아두이노와 연결되었습니다.")

    while True:
        # 2. 켜기 신호 보내기
        print("명령 전송: 1 (작동)")
        arduino.write(b'1') # 바이트 형태로 전송
        time.sleep(3)

        # 3. 끄기 신호 보내기
        print("명령 전송: 0 (정지)")
        arduino.write(b'0')
        time.sleep(3)

except Exception as e:
    print("\n[에러] 아두이노를 찾을 수 없습니다.")
    print("USB 케이블이 잘 꽂혔는지, 포트 이름이 맞는지 확인하세요.")
    print(f"에러 내용: {e}")
