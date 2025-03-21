﻿using System;
using System.Text;
using System.Windows;
using System.Drawing;
using System.IO;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using AForge.Video;
using AForge.Video.DirectShow;
using System.Data;
using System.Windows.Threading;
using System.Net.Sockets;
using System.Net;
using System.Media;

namespace Project_10
{
    public partial class MainWindow : Window
    {
        // 사용 가능한 비디오 장치 목록
        private FilterInfoCollection videoDevices;
        // 선택된 비디오 장치에서 영상을 캡처하는 객체
        private VideoCaptureDevice videoSource;
        // 타이머 변수
        private DispatcherTimer timer = new DispatcherTimer();

        TcpClient client;
        NetworkStream stream;

        public MainWindow()
        {
            InitializeComponent();
            this.Closed += Window_Closed;  // 창 닫을 때 웹캠도 꺼지게
        }

        private void Window_Closed(object sender, EventArgs e)
        {
            if (videoSource != null && videoSource.IsRunning)
            {
                videoSource.SignalToStop();  // 웹캠 연결 종료
                videoSource.NewFrame -= new NewFrameEventHandler(video_NewFrame);  // 프레임 이벤트 핸들러 제거
                videoSource = null;
            }
        }

        private void startButton_Click(object sender, RoutedEventArgs e)
        {
            // 시스템에서 사용 가능한 비디오 입력 장치 목록 가져오기
            videoDevices = new FilterInfoCollection(FilterCategory.VideoInputDevice);

            // 비디오 장치가 없을 경우 메시지 출력 후 종료
            if (videoDevices.Count == 0)
            {
                MessageBox.Show("비디오 장치를 찾을 수 없습니다.");
                return;
            }

            // 첫 번째 비디오 장치를 선택하여 영상 소스로 설정
            videoSource = new VideoCaptureDevice(videoDevices[1].MonikerString);
            // 새로운 프레임이 들어올 때마다 처리하는 이벤트 핸들러 등록
            videoSource.NewFrame += new NewFrameEventHandler(video_NewFrame);
            // 비디오 캡처 시작
            videoSource.Start();
        }

        private void closeButton_Click(object sender, RoutedEventArgs e)
        {
            // 비디오 소스가 실행 중이라면 종료
            if (videoSource != null && videoSource.IsRunning)
            {
                videoSource.SignalToStop(); // 비디오 스트림 정지
                videoSource.NewFrame -= new NewFrameEventHandler(video_NewFrame); // 이벤트 핸들러 제거
                videoSource = null; // 객체 해제
            }
            
            // 소켓 닫음
            stream.Close();
            client.Close();

            // 타이머 종료
            timer.Stop();
        }

        private void video_NewFrame(object sender, NewFrameEventArgs eventArgs)
        {
            Dispatcher.Invoke(() =>
            {
                BitmapImage bi;
                using (var bitmap = (Bitmap)eventArgs.Frame.Clone()) // 프레임을 복사하여 사용
                {
                    bi = BitmapToBitmapImage(bitmap); // Bitmap을 BitmapImage로 변환
                }

                bi.Freeze(); // UI 스레드에서 사용하기 위해 Freezing 적용
                webcamImage.Source = bi; // UI에 영상 표시
            });
        }

        // 비트맵 이미지로 변환
        private BitmapImage BitmapToBitmapImage(Bitmap bitmap)
        {
            using (var memory = new System.IO.MemoryStream()) // 메모리 스트림 사용
            {
                bitmap.Save(memory, System.Drawing.Imaging.ImageFormat.Bmp); // Bitmap을 메모리 스트림에 저장
                memory.Position = 0; // 스트림 위치 초기화
                var bitmapImage = new BitmapImage();
                bitmapImage.BeginInit();
                bitmapImage.StreamSource = memory; // 스트림 데이터를 이미지 소스로 설정
                bitmapImage.CacheOption = BitmapCacheOption.OnLoad; // 이미지 캐싱 옵션 설정
                bitmapImage.EndInit();
                return bitmapImage;
            }
        }

        private void connectButton_Click(object sender, RoutedEventArgs e) // 서버 연결, 타이머 작동
        {
            // 소켓을 생성한다.
            client = new TcpClient(new IPEndPoint(0, 0));
            // Connect 함수로 로컬(127.0.0.1)의 포트 번호 9999로 대기 중인 socket에 접속한다.
            client.Connect(new IPEndPoint(IPAddress.Parse("127.0.0.1"), 9999));
            // stream 생성
            stream = client.GetStream();

            timer.Interval = TimeSpan.FromMilliseconds(500); // 0.5초
            timer.Tick += new EventHandler(timer_Tick); // 타이머 1회당 함수 발동
            timer.Start(); // 타이머 시작
        }

        private void timer_Tick(object sender, EventArgs e)
        {
            // 타이머 1번 발생 = timer_Tick
            try
            {
                captureImage();
                string filepath = Path.Combine(App.path, "capturedImage.png");

                // 1️. 파일 크기 계싼
                byte[] fileBytes = File.ReadAllBytes(filepath);
                byte[] fileSizeBytes = BitConverter.GetBytes(fileBytes.Length);

                // 2️. 파일 데이터 비동기 전송 (정확한 크기만큼)
                stream.Write(fileSizeBytes, 0, 4);
                stream.Write(fileBytes, 0, fileBytes.Length);

                // 3️. 감지된 메시지 크기 수신
                byte[] sizeBuffer = new byte[4];
                int bytesRead = 0;
                while (bytesRead < 4)
                {
                    int read = stream.Read(sizeBuffer, bytesRead, 4 - bytesRead);
                    if (read == 0) throw new Exception("서버 연결이 끊어졌습니다.");
                    bytesRead += read;
                }
                int messageLength = BitConverter.ToInt32(sizeBuffer, 0);
                Console.WriteLine($"받은 메시지 크기: {messageLength} bytes");

                // 4️. 메시지 수신
                byte[] messageBuffer = new byte[messageLength];
                int totalReceived = 0;
                while (totalReceived < messageLength)
                {
                    int read = stream.Read(messageBuffer, totalReceived, messageLength - totalReceived);
                    if (read == 0)
                        throw new Exception("서버와 연결이 끊어졌습니다.");
                    totalReceived += read;
                }

                // 5. 메시지 출력
                string message = Encoding.UTF8.GetString(messageBuffer);
                Console.WriteLine($"서버로부터 받은 메시지: {message}");

                string currentTime = DateTime.Now.ToString("yy-MM-dd HH:mm:ss");

                // 메시지 UI에 표시
                Dispatcher.Invoke(() =>
                {
                    userInfo.Text = "현재 사용자 상태 : " + message;

                    var lines = logBox.Text.Split(new[] { "\r\n", "\n" }, StringSplitOptions.None).ToList();
                    if (lines.Count >= 100)
                    {
                        lines.RemoveAt(0); // 첫 번째 줄 삭제
                    }

                    // 날짜와 시간, 메시지를 추가
                    lines.Add($"[{currentTime}] 사용자 상태 : {message}");

                    logBox.Text = string.Join("\r\n", lines); // 나머지 줄들을 다시 합침

                    if (message == "Drowsy") // 졸음 판정이면 알림소리 울림
                    {
                        SystemSounds.Beep.Play();
                    }
                    logBox.ScrollToEnd();
                });
            }
            catch (Exception ex)
            {
                Console.WriteLine($"클라이언트 오류: {ex.Message}");
            }
        }

        private void captureImage() // 이미지 캡쳐
        {
            if (webcamImage.Source != null)
            {
                BitmapEncoder encoder = new PngBitmapEncoder();

                encoder.Frames.Add(BitmapFrame.Create((BitmapSource)webcamImage.Source)); // 웹캠 프레임 기반으로 이미지 비트맵 생성

                string combinePath = Path.Combine(App.path, "capturedImage.png");

                using (FileStream fs = new FileStream(combinePath, FileMode.Create))
                {
                    encoder.Save(fs); // 만들어둔 경로, 파일 이름에 이미지 저장
                }
            }
        }
    }
}