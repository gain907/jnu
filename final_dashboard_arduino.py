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

print("=== AI 통합 대시보드 (센서: 아두이노) ===")

# 1. 장치 연결
try:
    i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ
    frame = [0] * 768
    
    # 아두이노 연결 (중요!)
    arduino = serial.Serial(SERIAL_PORT, 9600, timeout=1)
    arduino.flush() # 통신 버퍼 비우기
    time.sleep(2)
    print(">>> 시스템 준비 완료")

except Exception as e:
    print(f"장치 연결 에러: {e}")
    exit()

# 2. 대시보드 화면 구성
plt.ion()
fig = plt.figure(figsize=(14, 8))
plt.subplots_adjust(bottom=0.25) 

# [왼쪽] 열화상 이미지
ax_img = fig.add_subplot(1, 2, 1)
thermal_data = np.zeros((24, 32))
im = ax_img.imshow(thermal_data, cmap='inferno', vmin=20, vmax=60)
plt.colorbar(im, ax=ax_img, label='Temp (°C)')
ax_img.set_title("Thermal Camera View", fontsize=14)

# [오른쪽] 온도 그래프
ax_graph = fig.add_subplot(1, 2, 2)
temp_history = [0] * 50
line, = ax_graph.plot(temp_history, 'r-', linewidth=2)
ax_graph.set_ylim(20, 100)
ax_graph.set_title("Max Temperature History", fontsize=14)
ax_graph.axhline(y=FIRE_THRESHOLD, color='orange', linestyle='--', label='Fire Limit')
ax_graph.grid(True)

# [하단] 상태 표시창
txt_temp = fig.text(0.15, 0.1, "TEMP: 0.0°C", fontsize=20, fontweight='bold', 
                    bbox=dict(facecolor='lightgreen', alpha=0.5))
txt_gas = fig.text(0.40, 0.1, "GAS: --", fontsize=20, fontweight='bold', 
                   bbox=dict(facecolor='lightgray', alpha=0.5))
txt_flame = fig.text(0.65, 0.1, "FLAME: --", fontsize=20, fontweight='bold', 
                     bbox=dict(facecolor='lightgray', alpha=0.5))
txt_sys = fig.text(0.5, 0.02, "SYSTEM: MONITORING", fontsize=16, ha='center',
                   color='white', bbox=dict(facecolor='gray', boxstyle='round'))

# 변수 초기화
gas_detected = False
flame_detected = False

try:
    while True:
        try:
            # --- (A) 열화상 데이터 처리 ---
            mlx.getFrame(frame)
            data_array = np.array(frame).reshape((24, 32))
            data_array = np.fliplr(data_array)
            max_temp = np.max(data_array)

            # --- (B) 아두이노와 통신 (핵심!) ---
            # 1. 열화상 상태 보내기 ('1' 또는 '0')
            if max_temp >= FIRE_THRESHOLD:
                arduino.write(b'1') # 뜨거우니까 켜라!
            else:
                arduino.write(b'0') # 정상이다.
            
            # 2. 아두이노가 보낸 센서 상태 읽기 (가스, 불꽃 정보 받기)
            if arduino.in_waiting > 0:
                try:
                    # 아두이노는 "1,0" 처럼 보냅니다 (가스,불꽃)
                    line_data = arduino.readline().decode('utf-8').strip()
                    parts = line_data.split(',')
                    if len(parts) == 2:
                        gas_detected = (parts[0] == '1')
                        flame_detected = (parts[1] == '1')
                except:
                    pass # 통신 에러 무시

            # --- (C) 화면(GUI) 업데이트 ---
            im.set_data(data_array)
            temp_history.append(max_temp)
            temp_history.pop(0)
            line.set_ydata(temp_history)

            # [온도 상태창]
            txt_temp.set_text(f"TEMP: {max_temp:.1f}°C")
            if max_temp >= FIRE_THRESHOLD:
                txt_temp.set_bbox(dict(facecolor='red', alpha=1.0))
            else:
                txt_temp.set_bbox(dict(facecolor='lightgreen', alpha=0.5))

            # [가스 상태창] (아두이노 정보를 바탕으로)
            if gas_detected:
                txt_gas.set_text("GAS: DANGER!")
                txt_gas.set_bbox(dict(facecolor='red', alpha=1.0))
            else:
                txt_gas.set_text("GAS: SAFE")
                txt_gas.set_bbox(dict(facecolor='lightgreen', alpha=0.5))

            # [불꽃 상태창]
            if flame_detected:
                txt_flame.set_text("FLAME: DETECTED!")
                txt_flame.set_bbox(dict(facecolor='red', alpha=1.0))
            else:
                txt_flame.set_text("FLAME: SAFE")
                txt_flame.set_bbox(dict(facecolor='lightgreen', alpha=0.5))

            # [시스템 전체 상태]
            if (max_temp >= FIRE_THRESHOLD) or gas_detected or flame_detected:
                txt_sys.set_text("🚨 SYSTEM ACTIVATED: PUMP ON 🚨")
                txt_sys.set_bbox(dict(facecolor='red', boxstyle='round'))
                ax_img.set_title("🔥 FIRE DETECTED! 🔥", color='red', fontweight='bold')
            else:
                txt_sys.set_text("SYSTEM: MONITORING...")
                txt_sys.set_bbox(dict(facecolor='gray', boxstyle='round'))
                ax_img.set_title("Thermal Camera View", color='black')

            plt.pause(0.01)

        except ValueError:
            continue
            
except KeyboardInterrupt:
    print("종료")
    arduino.write(b'0')
    plt.close()
