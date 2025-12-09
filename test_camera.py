import time
import board
import busio
import adafruit_mlx90640

print("=== 열화상 카메라 연결 테스트 시작 ===")

# 1. I2C 통신 연결 (SCL=5번핀, SDA=3번핀)
i2c = busio.I2C(board.SCL, board.SDA, frequency=800000)

# 2. 센서 객체 생성
try:
    mlx = adafruit_mlx90640.MLX90640(i2c)
    print("성공: MLX90640 센서를 찾았습니다!")
    
    # 3. 재생률 설정 (2Hz = 1초에 2번 측정)
    mlx.refresh_rate = adafruit_mlx90640.RefreshRate.REFRESH_2_HZ
    
    # 데이터를 담을 그릇 (768개 픽셀)
    frame = [0] * 768

    while True:
        try:
            # 온도 데이터 읽기
            mlx.getFrame(frame)
            
            # 중앙 위치 온도 가져오기 (대략 384번째 픽셀)
            center_temp = frame[384]
            max_temp = max(frame)
            
            print(f"중앙 온도: {center_temp:.1f}°C | 최고 온도: {max_temp:.1f}°C")
            time.sleep(1)
            
        except ValueError:
            # 가끔 읽기 에러가 날 수 있음 (무시하고 계속)
            continue

except Exception as e:
    print("\n[에러 발생] 센서 연결을 확인해주세요!")
    print(f"에러 내용: {e}")
