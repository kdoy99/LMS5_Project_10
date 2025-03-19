from tensorflow.keras.preprocessing import image
import numpy as np
import os
from PIL import Image



os.environ["TF_GPU_ALLOCATOR"] = "cuda_malloc_async"

import tensorflow as tf

gpus = tf.config.experimental.list_physical_devices('GPU')
if gpus:
    try:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)  # 메모리를 필요한 만큼만 할당
        print("✅ GPU 메모리 사용 제한 적용됨")
    except RuntimeError as e:
        print(e)

# 이미지 로드 및 전처리 함수
def load_images_from_folder(folder):
    images = []
    for filename in os.listdir(folder):
        if filename.endswith(('.jpg', '.png', '.jpeg')):  # 이미지 파일만 가져오기
            img_path = os.path.join(folder, filename)
            img = image.load_img(img_path, target_size=(416, 416))  # 크기 조정
            img_array = image.img_to_array(img)  # NumPy 배열로 변환
            images.append(img_array)

    return np.array(images)  # 리스트를 NumPy 배열로 변환

# 모든 이미지 로드
train_images = load_images_from_folder("C:\\Users\\jihye\\Desktop\\Project10_dataset\\train")
train_images = train_images / 255.0  # 정규화

print("총 이미지 개수:", train_images.shape[0])
print("이미지 크기:", train_images.shape[1:])

import pandas as pd
from sklearn.preprocessing import LabelEncoder

# CSV 파일 로드
csv_file = "C:\\Users\\jihye\\Desktop\\Project10_dataset\\train\\_annotations.csv"
df = pd.read_csv(csv_file)

# 이미지 파일 이름을 기준으로 라벨 매칭
image_to_label = {row["filename"]: row["class"] for _, row in df.iterrows()}

# 이미지와 라벨을 매칭하여 리스트 생성
labels = [image_to_label[filename] for filename in os.listdir("C:\\Users\\jihye\\Desktop\\Project10_dataset\\train") if filename in image_to_label]

# NumPy 배열로 변환
labels = np.array(labels)

print("총 클래스 개수:", len(set(labels)))
print("라벨 샘플:", labels[:5])


from sklearn.model_selection import train_test_split

# 데이터를 훈련(train)과 테스트(test)로 나누기 (80% 학습, 20% 테스트)
train_images, test_images, train_labels, test_labels = train_test_split(train_images, labels, test_size=0.2, random_state=42)

# LabelEncoder 인스턴스 생성
label_encoder = LabelEncoder()

# 'awake'와 'drowsy'를 정수로 변환
train_labels = label_encoder.fit_transform(train_labels)
test_labels = label_encoder.transform(test_labels)

# 라벨 확인
print("변경된 라벨:", train_labels[:5])

print("훈련 데이터 개수:", train_images.shape[0])
print("테스트 데이터 개수:", test_images.shape[0])

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten


# 간단한 모델 정의
model = Sequential([
    Flatten(input_shape=(416, 416, 3)),  # 입력 크기: (416, 416, 3)
    Dense(128, activation='relu'),
    Dense(len(set(labels)), activation='softmax')  # 클래스 개수만큼 출력 노드
])

# 모델 컴파일
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])

# 모델 학습
model.fit(train_images, train_labels, epochs=10, batch_size = 8, validation_data=(test_images, test_labels))

model.save('my_model.h5')

