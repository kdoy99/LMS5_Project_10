from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
import os
from PIL import Image

# 모델 불러오기
model = load_model('predict_folder/my_model.h5')

# 라벨 인코딩 (예: "awake" -> 0, "drowsy" -> 1)
class_labels = {'awake': 0, 'drowsy': 1}

# 이미지 전처리 함수
def prepare_image(img_path):
    # 이미지 로드
    img = image.load_img(img_path, target_size=(416, 416))  # 모델 입력 크기에 맞게 사이즈 조정
    img_array = image.img_to_array(img)  # NumPy 배열로 변환
    img_array = np.expand_dims(img_array, axis=0)  # 배치 차원 추가
    img_array = img_array / 255.0  # 정규화
    return img_array

# 예측 함수
def predict_image_class(img_path):
    # 이미지 전처리
    img = prepare_image(img_path)

    # 예측
    prediction = model.predict(img)
    predicted_class = np.argmax(prediction, axis=1)  # 예측된 클래스 인덱스

    # 클래스 인덱스를 라벨로 변환
    for label, index in class_labels.items():
        if predicted_class == index:
            return label

# 예시 이미지 경로
img_path = "C:\\Users\\jihye\\Desktop\\LMS5_Project_10\\Project_10\\Project_10\\Project_10\\Image\\capturedImage.png"

# 예측 결과 출력
prediction = predict_image_class(img_path)
print(f"이 이미지는 '{prediction}' 상태입니다.")
