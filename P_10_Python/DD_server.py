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
            save_dir = os.path.join(os.getcwd(), filename)

            received = 0
            with open(save_dir, 'wb') as f:
                while received < length:
                    chunk = client_socket.recv(min(4096, length - received))
                    if not chunk:
                        print("데이터 수신 중단")
                        break
                    f.write(chunk)
                    received += len(chunk)

            print(f"{filename} 수신 완료 ({received}/{length} bytes)")

            time.sleep(0.1)
            if os.path.getsize(save_dir) != length:
                print(f"저장된 파일 크기 불일치")
                continue

            img = cv2.imread(save_dir)
            if img is None:
                print(f"OpenCV : {save_dir} 읽기 불가능")
                continue

            results = model.predict(source=save_dir, save=True, project="Model/predict_folder", name="predict_result")

            detected_image_path = os.path.join("Model", "predict_result", filename)
            if not os.path.exists(detected_image_path) or os.path.getsize(detected_image_path) == 0:
                print(f"감지된 이미지 : {detected_image_path}")


            drowsy_check = False
            all_awake = True

            for result in results:
                for detection in result.boxes.data:
                    class_id = int(detection[5])
                    confidence = float(detection[4])
                    class_name = model.names[class_id]
                    print(f"Class: {class_name}, Confidence: {confidence}")
                    print(f"현재 졸음 스택 : {drowsy_stack}")
                    if class_name=='drowsy' and not drowsy_check:
                        drowsy_stack += 1
                        drowsy_check = True
                        all_awake = False
                    elif class_name == 'awake':
                        continue
                drowsy_check = False

            if all_awake:
                drowsy_stack = 0

            if drowsy_stack > 3:
                message = 'Drowsy'
                message_length = len(message)
                client_socket.send(message_length.to_bytes(4, byteorder='little'))

                client_socket.send(message.encode('utf-8'))
                print(f"클라이언트에 메시지 전송 완료")
            else:
                message = 'Awake'
                message_length = len(message)
                client_socket.send(message_length.to_bytes(4, byteorder='little'))

                client_socket.send(message.encode('utf-8'))
                print(f"클라이언트에 메시지 전송 완료")



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