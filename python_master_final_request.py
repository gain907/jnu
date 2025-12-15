# -*- coding: utf-8 -*-
import time
import board
import busio
import adafruit_mlx90640
import serial
import matplotlib.pyplot as plt
import numpy as np
import requests  # <--- [필수] 텔레그램용 라이브러리 추가됨

# ================= 설정값 =================
FIRE_THRESHOLD = 50.0        
SERIAL_PORT = '/dev/ttyACM0'
TELEGRAM_TOKEN = "8342638303:AAHPZpn33Xr8oxCvqypyCKJwySy5VrwW9xE"
TELEGRAM_CHAT_ID = "7134855426"
BAUD_RATE = 9600              

# [디자인 컬러 팔레트]
COLOR_BG = '#212121'       # 배경색
COLOR_SAFE = '#00E676'     # 안전 색상
COLOR_DANGER = '#FF1744'   # 위험 색상
COLOR_TEXT = '#FFFFFF'     # 글자색
# =========================================

print("=== 통합 화재 감지 시스템 (Dark UI + Telegram) ===")

# --- [추가 1] 텔레그램 메시지 전송 함수 ---
def send_telegram_message(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': msg}
        requests.post(url, data=data, timeout=1) # 1초 안에 안 가면 포기 (렉 방지)
        print(f"[전송 완료] {msg}")
    except Exception as e:
        print(f"[전송 실패] {e}")

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

# 2. UI 디자인 설정
plt.style.use('dark_background')
plt.ion()

fig = plt.figure(figsize=(12, 9), facecolor=COLOR_BG)
fig.canvas.manager.set_window_title('Fire Safety Monitor')
plt.subplots_adjust(bottom=0.45, wspace=0.2, left=0.05, right=0.95, top=0.90)

# --- [왼쪽] 열화상 이미지 ---
ax_img = fig.add_subplot(1, 2, 1)
thermal_data = np.zeros((24, 32))
ax_img.axis('off') 
ax_img.set_title("THERMAL CAMERA", color=COLOR_TEXT, fontsize=14, fontweight='bold')
im = ax_img.imshow(thermal_data, cmap='inferno', vmin=20, vmax=60)
cbar = plt.colorbar(im, ax=ax_img, fraction=0.046, pad=0.04)
cbar.ax.yaxis.set_tick_params(color=COLOR_TEXT)
plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color=COLOR_TEXT)

# --- [오른쪽] 온도 그래프 ---
ax_graph = fig.add_subplot(1, 2, 2)
ax_graph.set_facecolor(COLOR_BG)
temp_history = [20] * 50
x_data = list(range(50))
line, = ax_graph.plot(temp_history, color=COLOR_SAFE, linewidth=2)
fill = ax_graph.fill_between(x_data, temp_history, 0, color=COLOR_SAFE, alpha=0.3)

ax_graph.set_ylim(20, 100)
ax_graph.set_title("TEMP HISTORY", color=COLOR_TEXT, fontsize=14, fontweight='bold')
ax_graph.grid(True, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
ax_graph.spines['top'].set_visible(False)
ax_graph.spines['right'].set_visible(False)

# --- [하단] 상태 패널 ---
box_style_ok = dict(facecolor=COLOR_BG, edgecolor=COLOR_SAFE, boxstyle='round,pad=0.8', linewidth=2)
box_style_ng = dict(facecolor=COLOR_DANGER, edgecolor=COLOR_DANGER, boxstyle='round,pad=0.8', linewidth=2)

txt_gas = fig.text(0.20, 0.28, "GAS\nOK", ha='center', fontsize=18, fontweight='bold', color=COLOR_SAFE, bbox=box_style_ok)
txt_flame = fig.text(0.50, 0.28, "FLAME\nOK", ha='center', fontsize=18, fontweight='bold', color=COLOR_SAFE, bbox=box_style_ok)
txt_temp = fig.text(0.80, 0.28, "TEMP\n00.0°C", ha='center', fontsize=18, fontweight='bold', color=COLOR_SAFE, bbox=box_style_ok)
txt_main = fig.text(0.5, 0.08, "SYSTEM SAFE", ha='center', fontsize=40, fontweight='bold', color=COLOR_BG,
                    bbox=dict(facecolor=COLOR_SAFE, edgecolor='none', boxstyle='round,pad=0.6'))

# 변수 초기화
gas_detected = False
flame_detected = False
max_temp = 0
last_sent_time = 0 
msg_sent_flag = False  # <--- [추가 2] 메시지 중복 전송 방지 플래그

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

        # --- [2] 아두이노 데이터 수신 ---
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
            txt_gas.set_text("GAS\nDETECTED")
            txt_gas.set_color(COLOR_TEXT)
            txt_gas.set_bbox(box_style_ng)
        else:
            txt_gas.set_text("GAS\nOK")
            txt_gas.set_color(COLOR_SAFE)
            txt_gas.set_bbox(box_style_ok)

        # 2. 불꽃
        if flame_detected:
            txt_flame.set_text("FLAME\nDETECTED")
            txt_flame.set_color(COLOR_TEXT)
            txt_flame.set_bbox(box_style_ng)
        else:
            txt_flame.set_text("FLAME\nOK")
            txt_flame.set_color(COLOR_SAFE)
            txt_flame.set_bbox(box_style_ok)

        # 3. 온도
        txt_temp.set_text(f"TEMP\n{max_temp:.1f}°C")
        if max_temp >= FIRE_THRESHOLD:
            txt_temp.set_color(COLOR_TEXT)
            txt_temp.set_bbox(box_style_ng)
        else:
            txt_temp.set_color(COLOR_SAFE)
            txt_temp.set_bbox(box_style_ok)

        # --- [4] 화재 판단 및 메시지 전송 로직 ---
        is_fire = (max_temp >= FIRE_THRESHOLD) or gas_detected or flame_detected
        
        current_time = time.time()
        
        # 아두이노 명령 전송 (너무 자주 보내지 않게 0.1초 간격)
        if current_time - last_sent_time > 0.1:
            if is_fire:
                arduino.write(b'1')
                txt_main.set_text("WARNING: FIRE")
                txt_main.set_color(COLOR_TEXT)
                txt_main.set_bbox(dict(facecolor=COLOR_DANGER, edgecolor='none', boxstyle='round,pad=0.6'))
                
                # 그래프 색상 변경
                line.set_color(COLOR_DANGER)
                try: fill.remove() 
                except: pass
                fill = ax_graph.fill_between(x_data, temp_history, 0, color=COLOR_DANGER, alpha=0.3)
                
                # === [추가 3] 텔레그램 메시지 보내기 (최초 1회만) ===
                if msg_sent_flag == False:
                    # 원인 분석 메시지 작성
                    cause = []
                    if max_temp >= FIRE_THRESHOLD: cause.append(f"온도과열({max_temp:.1f}도)")
                    if gas_detected: cause.append("가스감지")
                    if flame_detected: cause.append("불꽃감지")
                    cause_str = ", ".join(cause)
                    
                    msg = f"🚨[비상] 화재 감지됨!🚨\n원인: {cause_str}\n시스템이 창문을 열고 펌프를 가동합니다."
                    send_telegram_message(msg)
                    msg_sent_flag = True # 보냈다고 표시 (중복 전송 방지)
                # ===============================================

            else:
                arduino.write(b'0')
                txt_main.set_text("SYSTEM SAFE")
                txt_main.set_color(COLOR_BG)
                txt_main.set_bbox(dict(facecolor=COLOR_SAFE, edgecolor='none', boxstyle='round,pad=0.6'))
                
                # 그래프 색상 복구
                line.set_color(COLOR_SAFE)
                try: fill.remove()
                except: pass
                fill = ax_graph.fill_between(x_data, temp_history, 0, color=COLOR_SAFE, alpha=0.3)

                # === [추가 4] 상황 종료 메시지 (복구 시 1회만) ===
                if msg_sent_flag == True:
                    send_telegram_message(f"✅[안전] 화재 상황 종료.\n현재온도: {max_temp:.1f}도\n시스템을 복구합니다.")
                    msg_sent_flag = False # 다시 보낼 준비
                # ===============================================
            
            last_sent_time = current_time

        # --- [5] 그래프 갱신 ---
        im.set_data(data_array)
        im.set_clim(vmin=np.min(data_array), vmax=max(60, max_temp))
        
        temp_history.append(max_temp)
        temp_history.pop(0)
        line.set_ydata(temp_history)
        
        plt.pause(0.001)

except KeyboardInterrupt:
    if arduino.is_open: arduino.close()
    plt.close()
    print("종료")
