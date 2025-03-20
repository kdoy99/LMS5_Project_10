using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Net;
using System.Net.Sockets;
using Microsoft.VisualBasic;

namespace SocketTest
{
    class Program
    {
        const byte NOT_FRAGMENTED = 0;
        const byte FRAGMENTED = 1;
        const int CHUNK_SIZE = 60113;
        
        static void Main(string[] args)
        {
            string filepath = "../../../image/capturedImage.png";
            long filesize = new FileInfo(filepath).Length;
            byte[] filename = Encoding.Default.GetBytes(filepath);
            // bytes 배열에 파일 사이즈와 파일 경로(이름) 넣어줌
            int size = sizeof(long) + filename.Length;
            byte[] bytes = new byte[size];
            byte[] temp = BitConverter.GetBytes(filesize);
            Array.Copy(temp, 0, bytes, 0, temp.Length);
            Array.Copy(filename, 0, bytes, temp.Length, filename.Length);

            // 소켓을 생성한다.
            TcpClient client = new TcpClient(new IPEndPoint(0, 0));
            // Connect 함수로 로컬(127.0.0.1)의 포트 번호 9999로 대기 중인 socket에 접속한다.
            client.Connect(new IPEndPoint(IPAddress.Parse("127.0.0.1"), 9999));

            NetworkStream stream = client.GetStream();

            // 파일스트림을 연다
            using (Stream fileStream = new FileStream(filepath, FileMode.Open))
            {
                byte[] rbytes = new byte[CHUNK_SIZE];

                fileStream.Read(rbytes, 0, CHUNK_SIZE);
                stream.Write(rbytes, 0, CHUNK_SIZE);
            }


            //// 소켓을 생성한다.
            //using (Socket client = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp))
            //{
            //    // Connect 함수로 로컬(127.0.0.1)의 포트 번호 9999로 대기 중인 socket에 접속한다.
            //    client.Connect(new IPEndPoint(IPAddress.Parse("127.0.0.1"), 9999));
            //    // 보낼 메시지를 UTF8타입의 byte 배열로 변환한다.
            //    var data = Encoding.UTF8.GetBytes("this message is sent from C# client.");

            //    // big엔디언으로 데이터 길이를 변환하고 서버로 보낼 데이터의 길이를 보낸다. (4byte)
            //    client.Send(BitConverter.GetBytes(data.Length));
            //    // 데이터를 전송한다.
            //    client.Send(data);

            //    // 데이터의 길이를 수신하기 위한 배열을 생성한다. (4byte)
            //    data = new byte[4];
            //    // 데이터의 길이를 수신한다.
            //    client.Receive(data, data.Length, SocketFlags.None);
            //    // server에서 big엔디언으로 전송을 했는데도 little 엔디언으로 온다.
            //    // big엔디언과 little엔디언은 배열의 순서가 반대이므로 reverse한다.
            //    //Array.Reverse(data);
            //    // 데이터의 길이만큼 byte 배열을 생성한다.
            //    data = new byte[BitConverter.ToInt32(data, 0)];
            //    // 데이터를 수신한다.
            //    client.Receive(data, data.Length, SocketFlags.None);
            //    // 수신된 데이터를 UTF8인코딩으로 string 타입으로 변환 후에 콘솔에 출력한다.
            //    Console.WriteLine(Encoding.UTF8.GetString(data));
            //}

            //Console.WriteLine("Press any key...");
            //Console.ReadLine();
        }
    }
}