import time
import board
import busio
import adafruit_mlx90640
import serial

# ================= 설정값 =================
FIRE_THRESHOLD = 50.0  # 화재로 판단할 온도 (50도)
SERIAL_PORT = '/dev/ttyACM0' # 아두이노 포트
# =========================================

print("=== 하이드로펌프 자동 배연 시스템 가동 ===")

# 1. 장치 초기화
try:
    # I2C 및 센서 설정
    i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
    frame = [0] * 768
    print("- 열화상 카메라: OK")

    # 아두이노 시리얼 설정
    arduino = serial.Serial(SERIAL_PORT, 9600, timeout=1)
    time.sleep(2) # 안정화 대기
    print("- 아두이노 통신: OK")

except Exception as e:
    print(f"\n[초기화 실패] 장치 연결을 확인하세요: {e}")
    exit()

# 상태 변수 (중복 전송 방지용)
is_fire_mode = False 

print("\n>>> 시스템 감시 중... (화재 기준: {:.1f}°C)".format(FIRE_THRESHOLD))

while True:
    try:
        # 2. 온도 데이터 읽기
        try:
            mlx.getFrame(frame)
        except ValueError:
            continue # 읽기 에러 시 재시도

        # 3. 최고 온도 계산 (화면 전체에서 가장 뜨거운 곳)
        max_temp = max(frame)
        
        # 4. 화재 판단 로직
        if max_temp >= FIRE_THRESHOLD:
            # 화재 감지됨!
            if not is_fire_mode: # 이미 켜져있지 않다면
                print(f"[화재 감지!] 최고온도: {max_temp:.1f}°C -> 배연 장치 가동!!")
                arduino.write(b'1') # 아두이노에 '1' 전송
                is_fire_mode = True
            else:
                print(f"[가동 중] 현재온도: {max_temp:.1f}°C")
                
        else:
            # 정상 상태
            if is_fire_mode: # 화재 모드였다면 끄기
                print(f"[상황 종료] 최고온도: {max_temp:.1f}°C -> 장치 정지")
                arduino.write(b'0') # 아두이노에 '0' 전송
                is_fire_mode = False
            else:
                # 평소에는 너무 자주 출력하지 않게 (옵션)
                # print(f"정상: {max_temp:.1f}°C", end='\r')
                pass

        time.sleep(0.5) # 0.5초 간격으로 검사

    except KeyboardInterrupt:
        print("\n시스템을 종료합니다.")
        arduino.write(b'0') # 종료 전 안전하게 끄기
        break
    except Exception as e:
        print(f"에러 발생: {e}")
        break
