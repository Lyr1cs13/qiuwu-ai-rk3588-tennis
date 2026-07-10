import cv2, time, os

CAP_W, CAP_H = 2112, 1568
time.sleep(0.2)

# 1. 强改回 11 号彩色通道
cap = cv2.VideoCapture(11)

# 2. 删掉了原本对 FOURCC 设置的语句（保持默认，由 OpenCV 后台自动解析彩色 NV12）
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAP_W)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAP_H)

rw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
rh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f'摄像头: {rw}x{rh}')

# 3. 创建自适应大小窗口，消除黑边
cv2.namedWindow('Preview', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Preview', 960, 600)

t0 = time.perf_counter(); fc = 0

while True:
    ret, frame = cap.read()
    if not ret: time.sleep(0.005); continue
    fc += 1
    
    if fc % 30 == 0:
        el = time.perf_counter() - t0
        print(f'{fc} 帧, {fc/el:.1f} fps')
        
    # 如果读取到的是 2 维的原始 Bayer 灰度图，则进行色彩还原（11 号节点通常自动跳过此步）
    if len(frame.shape) == 2:
        frame = cv2.cvtColor(frame, cv2.COLOR_BayerBG2BGR)
        
    disp = cv2.resize(frame, (960, 600))
    cv2.imshow('Preview', disp)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release(); cv2.destroyAllWindows()