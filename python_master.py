import time
import board
import busio
import adafruit_mlx90640
import serial
import matplotlib.pyplot as plt
import numpy as np

# ================= 설정값 =================
FIRE_THRESHOLD = 50.0        
SERIAL_PORT = '/dev/ttyACM0' 
BAUD_RATE = 9600             
# =========================================

print("=== 통합 화재 감지 시스템 (Big UI) ===")

# 1. 장치 초기화
try:
    i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ
    frame = [0] * 768
    
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    
    print(">>> 아두이노 연결 대기 (2초)...")
    time.sleep(2)
    arduino.reset_input_buffer()
    print(">>> 시스템 준비 완료!")

except Exception as e:
    print(f"장치 연결 실패: {e}")
    exit()

# 2. UI 화면 구성 (그래프 작게, 글자 크게)
plt.ion()
# 창 크기 설정
fig = plt.figure(figsize=(12, 9)) 

# [핵심] 하단 여백(bottom)을 0.4(40%)로 설정해서 글자 공간을 확보
# 그래프는 자동으로 위쪽 60% 공간으로 밀려나서 작아짐
plt.subplots_adjust(bottom=0.45, wspace=0.3) 

# 왼쪽: 열화상 이미지
ax_img = fig.add_subplot(1, 2, 1)
thermal_data = np.zeros((24, 32))
im = ax_img.imshow(thermal_data, cmap='inferno', vmin=20, vmax=60)
plt.colorbar(im, ax=ax_img)
ax_img.set_title("Thermal View", fontsize=14)

# 오른쪽: 온도 그래프
ax_graph = fig.add_subplot(1, 2, 2)
temp_history = [20] * 50
line, = ax_graph.plot(temp_history, 'r-', linewidth=2)
ax_graph.set_ylim(20, 100)
ax_graph.set_title("Max Temp History", fontsize=14)
ax_graph.grid(True)

# --- [UI 글자 확대] ---
# y 위치를 0.25 (중간 아래)로 배치하여 그래프 바로 밑에 위치시킴

# 1. 가스 (폰트 20으로 확대)
txt_gas = fig.text(0.20, 0.25, "GAS: OK", ha='center', fontsize=20, fontweight='bold',
                   bbox=dict(facecolor='lightgreen', edgecolor='black', boxstyle='round,pad=0.7'))

# 2. 불꽃 (폰트 20으로 확대)
txt_flame = fig.text(0.50, 0.25, "FLAME: OK", ha='center', fontsize=20, fontweight='bold',
                     bbox=dict(facecolor='lightgreen', edgecolor='black', boxstyle='round,pad=0.7'))

# 3. 온도 (폰트 20으로 확대)
txt_temp = fig.text(0.80, 0.25, "TEMP: 00.0C", ha='center', fontsize=20, fontweight='bold',
                    bbox=dict(facecolor='lightgreen', edgecolor='black', boxstyle='round,pad=0.7'))

# 4. 메인 경고창 (맨 아래, 폰트 35로 아주 크게!)
txt_main = fig.text(0.5, 0.08, "SYSTEM SAFE", ha='center', fontsize=35, fontweight='bold',
                    bbox=dict(facecolor='lightgreen', edgecolor='black', boxstyle='round,pad=1.0'))


gas_detected = False
flame_detected = False
max_temp = 0
last_sent_time = 0 

try:
    while True:
        # --- [1] 열화상 읽기 ---
        try:
            mlx.getFrame(frame)
            data_array = np.array(frame).reshape((24, 32))
            data_array = np.fliplr(data_array)
            max_temp = np.max(data_array)
        except:
            pass 

        # --- [2] 아두이노 데이터 수신 (최신값 유지) ---
        if arduino.in_waiting > 0:
            last_line = ""
            while arduino.in_waiting > 0:
                try:
                    read_val = arduino.readline().decode('utf-8', errors='ignore').strip()
                    if read_val: last_line = read_val
                except: pass
            
            if ',' in last_line:
                parts = last_line.split(',')
                if len(parts) == 2:
                    gas_detected = (parts[0] == '1')
                    flame_detected = (parts[1] == '1')

        # --- [3] UI 상태 업데이트 ---
        
        # 1. 가스
        if gas_detected:
            txt_gas.set_text("GAS: DETECTED")
            txt_gas.set_bbox(dict(facecolor='red', alpha=1.0))
        else:
            txt_gas.set_text("GAS: OK")
            txt_gas.set_bbox(dict(facecolor='lightgreen', alpha=0.7))

        # 2. 불꽃
        if flame_detected:
            txt_flame.set_text("FLAME: DETECTED")
            txt_flame.set_bbox(dict(facecolor='red', alpha=1.0))
        else:
            txt_flame.set_text("FLAME: OK")
            txt_flame.set_bbox(dict(facecolor='lightgreen', alpha=0.7))

        # 3. 온도
        txt_temp.set_text(f"TEMP: {max_temp:.1f}C")
        if max_temp >= FIRE_THRESHOLD:
            txt_temp.set_bbox(dict(facecolor='red', alpha=1.0))
        else:
            txt_temp.set_bbox(dict(facecolor='lightgreen', alpha=0.7))

        # --- [4] 메인 경고창 & 명령 전송 ---
        is_fire = (max_temp >= FIRE_THRESHOLD) or gas_detected or flame_detected
        
        current_time = time.time()
        if current_time - last_sent_time > 0.1:
            if is_fire:
                arduino.write(b'1')
                # 위험 시 문구 변경 및 배경 빨강
                txt_main.set_text("!!! WARNING: FIRE !!!")
                txt_main.set_bbox(dict(facecolor='red', edgecolor='black', boxstyle='round,pad=1.0'))
                txt_main.set_color("white") # 글자는 흰색으로
            else:
                arduino.write(b'0')
                # 안전 시 문구 변경 및 배경 초록
                txt_main.set_text("SYSTEM SAFE")
                txt_main.set_bbox(dict(facecolor='lightgreen', edgecolor='black', boxstyle='round,pad=1.0'))
                txt_main.set_color("black") # 글자는 검은색으로
            
            last_sent_time = current_time

        # --- [5] 그래프 갱신 ---
        im.set_data(data_array)
        im.set_clim(vmin=np.min(data_array), vmax=max(60, max_temp))
        
        temp_history.append(max_temp)
        temp_history.pop(0)
        line.set_ydata(temp_history)
        
        plt.pause(0.001)

except KeyboardInterrupt:
    arduino.close()
    plt.close()
    print("종료")
