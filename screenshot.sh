mkdir /e/Multishot/
while [ 1 ];
do mkdir /e/Multishot/`date +"%m-%d"` >/dev/null 2>&1;


## 判断前台程序
ForegroundWindow=`powershell -Command 'Add-Type @"
  using System;
  using System.Runtime.InteropServices;
  public class UserWindows {
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();
}
"@;
$a = [UserWindows]::GetForegroundWindow();
Get-Process | ? {$_.MainWindowHandle -eq $a};'|grep -E 'WeChat|QQ';`
# echo $ForegroundWindow
if [ "$ForegroundWindow" = "" ];
    then echo "激活窗口不在隐私规避软件内，运行截图";
else echo "隐私窗口，跳过截图";sleep 5;continue;
fi
## 判断前台程序


ffmpeg -f gdigrab -i desktop -s 2240x720 /e/Multishot/`date +"%m-%d"`/screenshot-`date +"%d %T" | sed -e "s/ /-/g; s/:/-/g"`.jpg >/dev/null 2>&1;
echo "截图成功`date +"%d %T" | sed -e "s/ /-/g; s/:/-/g"`"
sleep 5;
done