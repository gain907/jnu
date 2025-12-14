import time
import board
import busio
import adafruit_mlx90640
import serial
import matplotlib.pyplot as plt
import numpy as np

# ================= 설정값 =================
FIRE_THRESHOLD = 50.0        # 열화상 화재 기준 온도
SERIAL_PORT = '/dev/ttyACM0' # 아두이노 포트
# =========================================

print("=== 라즈베리 파이 메인 컨트롤러 (Master) ===")

# 1. 장치 연결
try:
    i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ
    frame = [0] * 768
    
    # 아두이노와 시리얼 연결
    arduino = serial.Serial(SERIAL_PORT, 9600, timeout=1)
    arduino.flush()
    time.sleep(2) # 아두이노 리셋 대기

except Exception as e:
    print(f"장치 연결 실패: {e}")
    exit()

# 2. 대시보드 UI 준비
plt.ion()
fig = plt.figure(figsize=(14, 8))
plt.subplots_adjust(bottom=0.25)

ax_img = fig.add_subplot(1, 2, 1)
thermal_data = np.zeros((24, 32))
im = ax_img.imshow(thermal_data, cmap='inferno', vmin=20, vmax=60)
plt.colorbar(im, ax=ax_img)
ax_img.set_title("Thermal View")

# 상태창
txt_sys = fig.text(0.5, 0.05, "SYSTEM READY", fontsize=20, ha='center', 
                   bbox=dict(facecolor='gray', boxstyle='round', alpha=0.5))

# 아두이노에서 받은 센서값 저장 변수
gas_detected = False
flame_detected = False

try:
    while True:
        try:
            # --- [1] 열화상 데이터 읽기 ---
            mlx.getFrame(frame)
            data_array = np.array(frame).reshape((24, 32))
            data_array = np.fliplr(data_array)
            max_temp = np.max(data_array)

            # --- [2] 아두이노에서 가스/불꽃 값 받아오기 ---
            # 아두이노가 "1,0" 처럼 보내줍니다.
            if arduino.in_waiting > 0:
                try:
                    line = arduino.readline().decode('utf-8').strip()
                    parts = line.split(',')
                    if len(parts) == 2:
                        gas_detected = (parts[0] == '1')
                        flame_detected = (parts[1] == '1')
                except:
                    pass # 통신 깨지면 무시

            # --- [3] 최종 화재 판단 (라즈베리 파이의 결정) ---
            # 열화상 OR 가스 OR 불꽃
            is_fire = (max_temp >= FIRE_THRESHOLD) or gas_detected or flame_detected

            # --- [4] 아두이노에게 명령 내리기 ---
            if is_fire:
                arduino.write(b'1') # 야! 불났다! (문 열고 펌프 켜)
                
                # 화면 표시
                txt_sys.set_text("🔥 WARNING: FIRE DETECTED! 🔥")
                txt_sys.set_bbox(dict(facecolor='red', alpha=1.0))
            else:
                arduino.write(b'0') # 안전함 (복구해라)
                
                # 화면 표시
                status_msg = f"SAFE (Temp: {max_temp:.1f}C)"
                txt_sys.set_text(status_msg)
                txt_sys.set_bbox(dict(facecolor='lightgreen', alpha=0.5))

            # --- [5] 화면 갱신 ---
            im.set_data(data_array)
            plt.pause(0.01)

        except ValueError:
            continue
            
except KeyboardInterrupt:
    if arduino.is_open:
        arduino.write(b'0') # 종료 시 끄기 명령
        arduino.close()
    plt.close()
    print("시스템 종료")
