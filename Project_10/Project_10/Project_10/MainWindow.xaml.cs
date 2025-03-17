using System;
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
using System.Windows.Shapes;
using AForge.Video;
using AForge.Video.DirectShow;
using System.Data;

namespace Project_10
{
    public partial class MainWindow : Window
    {
        // 사용 가능한 비디오 장치 목록
        private FilterInfoCollection videoDevices;
        // 선택된 비디오 장치에서 영상을 캡처하는 객체
        private VideoCaptureDevice videoSource;

        public MainWindow()
        {
            InitializeComponent();
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
            videoSource = new VideoCaptureDevice(videoDevices[0].MonikerString);
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
        }

        private void video_NewFrame(object sender, NewFrameEventArgs eventArgs)
        {
            BitmapImage bi;
            using (var bitmap = (Bitmap)eventArgs.Frame.Clone()) // 프레임을 복사하여 사용
            {
                bi = BitmapToBitmapImage(bitmap); // Bitmap을 BitmapImage로 변환
            }

            bi.Freeze(); // UI 스레드에서 사용하기 위해 Freezing 적용

            // 비동기 처리
            Dispatcher.BeginInvoke(new Action(() =>
            {
                webcamImage.Source = bi; // UI에 영상 표시
            }));
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
    }
}