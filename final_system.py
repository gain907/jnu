import time
import board
import busio
import adafruit_mlx90640
import serial
import matplotlib.pyplot as plt
import numpy as np
import RPi.GPIO as GPIO

# ================= 설정값 =================
FIRE_THRESHOLD = 50.0       # 열화상 화재 기준 온도
SERIAL_PORT = '/dev/ttyACM0' # 아두이노 포트 (안되면 /dev/ttyUSB0)

# GPIO 핀 번호 설정 (BCM 모드 기준)
PIN_GAS = 17    # 가스 센서 (MQ-2) DO 핀
PIN_FLAME = 27  # 불꽃 센서 DO 핀
# =========================================

print("=== [최종] AI 자동 배연 시스템 가동 ===")

# 1. GPIO(센서) 초기화
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_GAS, GPIO.IN)
GPIO.setup(PIN_FLAME, GPIO.IN)

# 2. 통신 및 카메라 초기화
try:
    # I2C 열화상 카메라
    i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ
    frame = [0] * 768
    
    # 아두이노 시리얼 통신
    arduino = serial.Serial(SERIAL_PORT, 9600, timeout=1)
    time.sleep(2) # 연결 대기
    print(">>> 장치 연결 성공: 카메라, 아두이노, 센서")

except Exception as e:
    print(f"장치 연결 실패: {e}")
    GPIO.cleanup()
    exit()

# 3. 대시보드(화면) 설정
plt.ion()
fig = plt.figure(figsize=(14, 7))

# [왼쪽] 열화상 뷰
ax_img = fig.add_subplot(1, 2, 1)
thermal_data = np.zeros((24, 32))
im = ax_img.imshow(thermal_data, cmap='inferno', vmin=20, vmax=60)
plt.colorbar(im, ax=ax_img, label='Temp (°C)')
ax_img.set_title("Thermal Camera")

# [오른쪽] 온도 그래프
ax_graph = fig.add_subplot(1, 2, 2)
temp_history = [0] * 50
line, = ax_graph.plot(temp_history, 'r-', linewidth=2)
ax_graph.set_ylim(20, 100)
ax_graph.set_title("Max Temp Trend")
ax_graph.axhline(y=FIRE_THRESHOLD, color='orange', linestyle='--', label='Limit')
ax_graph.grid(True)
ax_graph.legend()

# 상태 변수
is_fire_mode = False

# 4. 메인 루프 실행
try:
    while True:
        try:
            # --- (A) 센서 데이터 읽기 ---
            # 1. 열화상 온도
            mlx.getFrame(frame)
            data_array = np.array(frame).reshape((24, 32))
            data_array = np.fliplr(data_array)
            max_temp = np.max(data_array)

            # 2. 가스 & 불꽃 센서 (0이 감지됨인 경우가 많음 - 센서마다 다름)
            # 보통 모듈은 감지 시 LOW(0), 평소 HIGH(1)를 출력합니다.
            # 만약 반대라면 `== 1`로 수정하세요.
            gas_detected = (GPIO.input(PIN_GAS) == 0) 
            flame_detected = (GPIO.input(PIN_FLAME) == 0)

            # --- (B) 화재 판단 로직 (OR 조건) ---
            # 셋 중 하나라도 감지되면 화재로 판단
            fire_condition = (max_temp >= FIRE_THRESHOLD) or gas_detected or flame_detected
            
            # --- (C) 시각화 업데이트 ---
            im.set_data(data_array)
            temp_history.append(max_temp)
            temp_history.pop(0)
            line.set_ydata(temp_history)

            # 상태 메시지 만들기
            status_msg = f"Temp: {max_temp:.1f}°C"
            if gas_detected: status_msg += " | GAS Detected!"
            if flame_detected: status_msg += " | FLAME Detected!"

            # --- (D) 아두이노 제어 (펌프 작동) ---
            if fire_condition:
                ax_img.set_title(f"🔥 FIRE DETECTED! 🔥\n{status_msg}", color='red', fontweight='bold')
                
                if not is_fire_mode:
                    print(f"[비상] 화재 감지! ({status_msg}) -> 펌프 가동")
                    arduino.write(b'1') # 아두이노 7번 핀 ON 신호 전송
                    is_fire_mode = True
            else:
                ax_img.set_title(f"Normal Monitoring\n{status_msg}", color='black')
                
                if is_fire_mode:
                    print(f"[정상] 상황 종료. ({status_msg}) -> 펌프 정지")
                    arduino.write(b'0') # 아두이노 7번 핀 OFF 신호 전송
                    is_fire_mode = False

            plt.pause(0.01)

        except ValueError:
            continue # 센서 읽기 오류 시 건너뜀
            
except KeyboardInterrupt:
    print("시스템을 종료합니다.")
    arduino.write(b'0') # 종료 전 펌프 끄기
    GPIO.cleanup()      # GPIO 설정 초기화
    plt.close()
