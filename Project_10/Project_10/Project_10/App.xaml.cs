using System.Configuration;
using System.Data;
using System.Windows;

namespace Project_10
{
    /// <summary>
    /// Interaction logic for App.xaml
    /// </summary>
    public partial class App : Application
    {
        string userName = Environment.UserName;
        public static string path = $"C:\\Users\\{userName}\\Desktop\\LMS5_Project_10\\Project_10\\Project_10\\Project_10\\Image\\";
    }

}
