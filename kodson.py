import time
import cv2
import numpy as np
import math

def edge(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blur= cv2.GaussianBlur(gray, (5, 15), 0)
    canny = cv2.Canny(blur, 50, 150)
    return canny

# Doğru eğimini hesaplayan fonksiyon
def find_slope(x1, y1, x2, y2):
    if x2 - x1 != 0:
        return (x2- x1) / (y2 - y1)  # m = (y2-y1) / (x2-x1)
    else:
        return None  # Dik doğru (sonsuz eğim)
def dereceye_cevirme(a):
    if a is not None:
        return math.atan(a)*180/math.pi
# İki doğru arasındaki orta noktayı bulan fonksiyon
def find_midpoint(line1, line2):
    x1, y1, x2, y2 = line1
    x3, y3, x4, y4 = line2
    midpoint_x = (x1 + x2 + x3 + x4) // 4
    midpoint_y = (y1 + y2 + y3 + y4) // 4
    return midpoint_x, midpoint_y

# Kuş bakışı perspektifi ekleyen fonksiyon
def kusbasi(frame):
    frame =cv2.resize(frame,(640,480))
    top_left = (183, 279)
    bottom_left = (38, 443)
    top_right = (476, 279)
    bottom_right = (610, 443)

    pts1 = np.float32([top_left, bottom_left, top_right, bottom_right])
    pts2 = np.float32([[0, 0], [0, 480], [640, 0], [640, 480]])
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    transformed_frame = cv2.warpPerspective(frame, matrix, (640 ,480))
    return transformed_frame

# Video kaynağını aç
cap = cv2.VideoCapture("C:\pydeneme\duzyol4.mp4")
if not cap.isOpened():
    print('ERROR FILE NOT FOUND')
    exit()

while cap.isOpened():
    ret, frame = cap.read()
    if ret:
        # ROI (Region of Interest) seçimi
        roi = frame[800:1500, 700:3200]
        canny1=edge(roi)

        # Hough Çizgi Algılama
        cizgi = cv2.HoughLinesP(canny1, 1, np.pi / 180, 50, minLineLength=50, maxLineGap=50)
        sonuc = np.copy(roi)

        # Sol ve sağ şeritleri ayrı listelere koymak
        left_lines = []
        right_lines = []

        if cizgi is not None:
            for line in cizgi:
                x1, y1, x2, y2 = line[0]
                slope = find_slope(x1, y1, x2, y2)
                aci=dereceye_cevirme(slope)

                if slope is not None:
                    if slope < 0:  # Sol şerit (negatif eğim)
                        left_lines.append((x1, y1, x2, y2))
                    elif slope > 0:  # Sağ şerit (pozitif eğim)
                        right_lines.append((x1, y1, x2, y2))

                # Çizgileri görüntüde çiz
                cv2.line(sonuc, (x1, y1), (x2, y2), (255, 0, 0), thickness=5)

        # Orta nokta hesaplama ve şerit bilgileri
        steering_angle = 0
        lane_position = "Unknown"

        if left_lines and right_lines:
            # Ortalama bir sol ve sağ şerit seçelim
            left_avg = np.mean(left_lines, axis=0, dtype=int)
            right_avg = np.mean(right_lines, axis=0, dtype=int)

            # Orta noktayı bul
            midpoint_x, midpoint_y = find_midpoint(left_avg, right_avg)

            # Orta noktayı görüntüye ekle
            cv2.circle(sonuc, (midpoint_x, midpoint_y), 10, (0, 255, 0), -1)

            # Direksiyon açısını hesapla
            frame_center = (roi.shape[1]) // 2
            lane_center = (left_avg[2] + right_avg[2]) // 2
            steering_angle = (lane_center - frame_center) * 0.1

            if lane_center < frame_center - 50:
                lane_position = "Left Lane"
            elif lane_center > frame_center + 50:
                lane_position = "Right Lane"
            else:
                lane_position = "Center Lane"

            # Eğim bilgilerini yazdır
            print(f"Sol eğim: {find_slope(*left_avg):.2f}, Sağ eğim: {find_slope(*right_avg):.2f}")
            print(f"Orta Nokta: ({midpoint_x}, {midpoint_y})")

        # Şerit bilgilerini görüntüye ekle
        cv2.putText(sonuc, f"Angle: {int(steering_angle)} degrees", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(sonuc, f"Lane: {lane_position}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Kuş bakışı perspektifi
        kus = kusbasi(frame)

        # Kuş bakışını gri tonlamaya çevir ve işleyin
        kus_canny=edge(kus)
        kus_cizgi = cv2.HoughLinesP(kus_canny, 1, np.pi / 180, 50, minLineLength=50, maxLineGap=50)

        if kus_cizgi is not None:
            for line in kus_cizgi:
                x1, y1, x2, y2 = line[0]
                slope = find_slope(x1, y1, x2, y2)
                aci=dereceye_cevirme(slope)
                print("kusbakis:"+str(aci))
                cv2.line(kus, (x1, y1), (x2, y2), (0, 0, 255), thickness=5)

        # Görüntüleri göster
        cv2.imshow('Kus Bakisi', kus)
        cv2.imshow('Lane Detection', sonuc)

        if cv2.waitKey(10) & 0xFF == ord('q'):
            break
    else:
        break

cap.release()
cv2.destroyAllWindows()