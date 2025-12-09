import time
import board
import busio
import adafruit_mlx90640
import matplotlib.pyplot as plt
import numpy as np

# === 설정값 ===
FIRE_THRESHOLD = 50.0   # 화재 기준 온도
HISTORY_SIZE = 50       # 그래프에 보여줄 최근 데이터 개수
# =============

print("=== 실시간 열화상 대시보드 시작 ===")

# 1. 하드웨어 초기화
try:
    i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)
    mlx = adafruit_mlx90640.MLX90640(i2c)
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_4_HZ # 화면 갱신을 위해 4Hz로 상향
    frame = [0] * 768
except Exception as e:
    print(f"센서 연결 실패: {e}")
    exit()

# 2. 그래프 및 이미지 창 설정 (Matplotlib)
plt.ion() # 인터랙티브 모드 켜기 (실시간 갱신용)
fig = plt.figure(figsize=(12, 6)) # 창 크기 설정

# [왼쪽] 열화상 이미지 (Heatmap)
ax_img = fig.add_subplot(1, 2, 1)
thermal_data = np.zeros((24, 32)) # 24x32 픽셀
# 초기 이미지 그리기 (vmin=20도, vmax=60도 고정 -> 색상 변화 확실히 보임)
im = ax_img.imshow(thermal_data, cmap='inferno', vmin=20, vmax=60, interpolation='bilinear')
plt.colorbar(im, ax=ax_img, label='Temperature (°C)')
ax_img.set_title("Thermal Camera View")

# [오른쪽] 온도 그래프 (Line Chart)
ax_graph = fig.add_subplot(1, 2, 2)
temp_history = [0] * HISTORY_SIZE # 0으로 초기화된 리스트
line, = ax_graph.plot(temp_history, color='red', linewidth=2)
ax_graph.set_ylim(20, 80) # Y축 범위 (20도 ~ 80도)
ax_graph.set_title("Max Temperature Trend")
ax_graph.set_ylabel("Temp (°C)")
ax_graph.set_xlabel("Time")
ax_graph.grid(True)

# 기준선 그리기 (50도 점선)
ax_graph.axhline(y=FIRE_THRESHOLD, color='orange', linestyle='--', label='Fire Limit')
ax_graph.legend()

print(">>> 시각화 창을 띄웁니다...")

# 3. 메인 루프 (무한 반복)
try:
    while True:
        try:
            # (1) 데이터 읽기
            mlx.getFrame(frame)
            
            # (2) 데이터 가공
            # 1차원 리스트(768개)를 24x32 2차원 배열로 변환
            data_array = np.array(frame).reshape((24, 32))
            
            # 좌우 반전 (거울 모드 - 필요 없으면 삭제 가능)
            data_array = np.fliplr(data_array)
            
            # 최고 온도 찾기
            max_temp = np.max(data_array)
            
            # (3) [왼쪽] 열화상 이미지 업데이트
            im.set_data(data_array)
            
            # 화재 감지 시 제목을 빨간색으로 변경
            if max_temp >= FIRE_THRESHOLD:
                ax_img.set_title(f"🔥 FIRE DETECTED! ({max_temp:.1f}°C) 🔥", color='red', fontweight='bold')
            else:
                ax_img.set_title(f"Normal Monitoring ({max_temp:.1f}°C)", color='black')

            # (4) [오른쪽] 그래프 데이터 업데이트
            temp_history.append(max_temp)       # 새 온도 추가
            temp_history.pop(0)                 # 가장 옛날 온도 삭제
            line.set_ydata(temp_history)        # 그래프 선 업데이트
            
            # (5) 화면 그리기 (잠시 멈춰야 그려짐)
            plt.pause(0.01)

        except ValueError:
            continue # 센서 읽기 에러 무시
            
except KeyboardInterrupt:
    print("종료합니다.")
    plt.close()
