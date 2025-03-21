# 소켓을 사용하기 위해서는 socket을 import해야 한다.
import os
import cv2
from ultralytics import YOLO
import socket
import threading
import time

model = YOLO("Model/best.pt")
drowsy_stack = 0
# binder함수는 서버에서 accept가 되면 생성되는 socket 인스턴스를 통해 client로부터 데이터를 받으면 echo형태로 재송신하는 메소드이다.
def binder(client_socket, addr):
    # 커넥션이 되면 접속 주소가 나온다.
    global drowsy_stack
    print('Connected by', addr)
    try:
        # 접속 상태에서는 클라이언트로부터 받을 데이터를 무한 대기한다.
        # 만약 접속이 끊기게 된다면 except가 발생해서 접속이 끊기게 된다.
        while True:
            # # socket의 recv함수는 연결된 소켓으로부터 데이터를 받을 대기하는 함수입니다. 최초 4바이트를 대기합니다.
            data = client_socket.recv(4)
            if not data:
                break;
            # # 최초 4바이트는 전송할 데이터의 크기이다. 그 크기는 big 엔디언으로 byte에서 int형식으로 변환한다.
            # # C#의 BitConverter는 big엔디언으로 처리된다. >> little엔디언으로 처리됨
            length = int.from_bytes(data, "little")

            filename = 'transferredImage.png'
            save_dir = os.path.join(os.getcwd(), filename) # 파일 저장 경로

            # 클라이언트로부터 이미지 받아옴
            received = 0
            with open(save_dir, 'wb') as f: # w : 쓰기 모드, b : 바이너리 모드
                while received < length: # 전체 데이터의 크기만큼 데이터 받기 반복문
                    # 한번에 최대 4096바이트 수신, 크기가 length 넘지 않도록 계산
                    chunk = client_socket.recv(min(4096, length - received))
                    if not chunk: # 데이터 X
                        print("데이터 수신 중단")
                        break
                    f.write(chunk) # 받은 데이터 파일에 쓰기
                    received += len(chunk) # 수신한 데이터 토대로 크기 업데이트

            print(f"{filename} 수신 완료 ({received}/{length} bytes)")

            time.sleep(0.05) # 데이터 범람 방지 텀 지정
            if os.path.getsize(save_dir) != length: # 파일 크기 예상 크기와 동일한지 확인
                print(f"저장된 파일 크기 불일치")
                continue

            img = cv2.imread(save_dir) # 파일 형식 제대로 되어있는지
            if img is None:
                print(f"OpenCV : {save_dir} 읽기 불가능")
                continue


            # 만들어진 모델 토대로, 예측 수행 후 지정한 경로에 파일 저장
            results = model.predict(source=save_dir, save=True, project="Model/predict_folder", name="predict_result")

            # 클라이언트에서 받은 이미지 경로 지정
            detected_image_path = os.path.join("Model", "predict_result", filename)
            # 이미지 제대로 왔는지 확인
            if not os.path.exists(detected_image_path) or os.path.getsize(detected_image_path) == 0:
                print(f"감지된 이미지 : {detected_image_path}")


            drowsy_check = False # 졸음 스택 변수
            all_awake = True # 모두 awake 상태일 때, 졸음 변수 초기화 용
            detect = False # 아무것도 감지 못했을 때 False

            for result in results: # 예측 결과 리스트 확인용 반복문
                for detection in result.boxes.data: # 감지된 객체 정보 포함한 리스트, 리스트 이므로 또 반복문 사용
                    class_id = int(detection[5]) # awake인지 drowsy인지 들어있는 부분 (0과 1)
                    confidence = float(detection[4]) # 신뢰도
                    class_name = model.names[class_id] # (0과 1 기반으로 awake, drowsy 변환)
                    print(f"Class: {class_name}, Confidence: {confidence}")
                    print(f"현재 졸음 스택 : {drowsy_stack}")
                    if class_name=='drowsy' and not drowsy_check: # drowsy 상태이면서, 졸음 스택이 활성화 안 되어있다면
                        drowsy_stack += 1
                        drowsy_check = True
                        all_awake = False
                        detect = True
                    elif class_name == 'awake': # 깨어있다면 넘어가기
                        detect = True
                        continue

                drowsy_check = False # drowsy 상태 초기화
            # 위 변수들이 필요한 이유 : 여러명을 감지해서 여러번의 drowsy가 들어오고, 스택이 여러번 쌓일 수 있기 때문
            # 여러명을 인식해도 drowsy 상태 1명이라도 있으면 스택 쌓이도록 하는 중

            if all_awake: # 모두 깨어있으면 스택 초기화
                drowsy_stack = 0

            if drowsy_stack > 3: # 3스택일시, 클라이언트에 졸림 상태라고 전송
                message = 'Drowsy'
                message_length = len(message)
                client_socket.send(message_length.to_bytes(4, byteorder='little'))

                client_socket.send(message.encode('utf-8'))
                print(f"클라이언트에 {message} 전송 완료")
            elif not detect:
                message = 'No Detection'
                message_length = len(message)
                client_socket.send(message_length.to_bytes(4, byteorder='little'))

                client_socket.send(message.encode('utf-8'))
                print(f"클라이언트에 {message} 전송 완료")

            else: # 그외 깨어있는 상태라고 전송
                message = 'Awake'
                message_length = len(message)
                client_socket.send(message_length.to_bytes(4, byteorder='little'))

                client_socket.send(message.encode('utf-8'))
                print(f"클라이언트에 {message} 전송 완료")

    except:
        # 접속이 끊기면 except가 발생한다.
        print("except : ", addr)
    finally:
        # 접속이 끊기면 socket 리소스를 닫는다.
        client_socket.close()


# 소켓을 만든다.
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# 소켓 레벨과 데이터 형태를 설정한다.
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# 서버는 복수 ip를 사용하는 pc의 경우는 ip를 지정하고 그렇지 않으면 None이 아닌 ''로 설정한다.
# 포트는 pc내에서 비어있는 포트를 사용한다. cmd에서 netstat -an | find "LISTEN"으로 확인할 수 있다.
server_socket.bind(('', 9999))
# server 설정이 완료되면 listen를 시작한다.
server_socket.listen()

try:
    # 서버는 여러 클라이언트를 상대하기 때문에 무한 루프를 사용한다.
    while True:
        # client로 접속이 발생하면 accept가 발생한다.
        # 그럼 client 소켓과 addr(주소)를 튜플로 받는다.
        client_socket, addr = server_socket.accept()
        th = threading.Thread(target=binder, args=(client_socket, addr))
        # 쓰레드를 이용해서 client 접속 대기를 만들고 다시 accept로 넘어가서 다른 client를 대기한다.
        th.start()
except:
    print("server")
finally:
    # 에러가 발생하면 서버 소켓을 닫는다.
    server_socket.close()