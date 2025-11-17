import sys
import subprocess
from typing import Union

import win32gui
import win32con
import time
from PIL import ImageGrab
import datetime
import os  
import pyautogui
import pyperclip
from openai import OpenAI


def perform_action(current_action: str, param: Union[tuple, list, str]):
    #### {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
    if current_action == "terminate":
        sys.exit(0)

    
    if current_action == "type" or current_action == "key":
        if "enter" == param:
            pyautogui.press('enter')
            return
        pyperclip.copy(param)  # 将文本复制到剪贴板
        pyautogui.hotkey('ctrl', 'v')

    if current_action == "click":
        x, y = param
        pyautogui.click(x=x, y=y, button="left")

    if current_action == "left_click":
        x, y = param
        pyautogui.click(x=x, y=y, button="left")  # 左键单击
    
    if current_action == "mouse_move":
        x, y = param
        pyautogui.moveTo(x=x, y=y)
    
    if current_action == "scroll":
        #滚轮的滚动次数，z值为正时向上滚动，为负时向下滚动   
        count = param
        # 使用简单的非线性变换，使得z值较小时放大倍数较大，z值较大时放大倍数较小
        # 同时确保输出不会太大或太小，平滑过渡
        max_output = 1000
        sensitivity = 2.0  # 调整此参数可以控制整体灵敏度
        
        sign = 1 if count > 0 else -1
        abs_count = abs(count)  
        #应用非线性变换
        adjusted_count = sign * max_output * (abs_count / (10 + abs_count)) * sensitivity
        
        #确保值域在-1000到1000之间
        scroll_val = int(max(-max_output, min(max_output, adjusted_count)))
    
        pyautogui.scroll(scroll_val)
    if current_action == "wait":
        times = param
        time.sleep(times)


def screenshot_with_timestamp():
    """
    截取屏幕并保存到当前工作目录的tmp文件夹中（不存在则创建），
    返回以时间戳命名的图片完整路径
    
    返回:
        str: 截图图片的完整路径（如"./tmp/screenshot_20251017153045123.png"）
    """
    # 定义tmp文件夹路径（当前工作目录下的tmp文件夹）
    tmp_dir = os.path.join(os.getcwd(), "tmp")  # 跨平台路径拼接（Windows/Linux通用）
    
    # 若tmp文件夹不存在，则创建（exist_ok=True确保目录存在时不报错）
    os.makedirs(tmp_dir, exist_ok=True)
    
    # 截取屏幕
    screenshot = ImageGrab.grab()
    
    # 生成精确到毫秒的时间戳（避免文件名重复）
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]  # 取微秒前3位作为毫秒
    
    # 构建图片文件名（仅文件名部分）
    filename = f"screenshot_{timestamp}.png"
    
    # 构建完整保存路径（tmp文件夹 + 文件名）
    save_path = os.path.join(tmp_dir, filename)
    
    # 保存图片到tmp文件夹
    screenshot.save(save_path)
    
    return save_path  # 返回完整路径，方便后续使用



def wait_x_seconds(x):
    """
    让程序暂停等待x秒
    
    参数:
        x: 等待的秒数（支持整数或浮点数，如3表示3秒，0.5表示0.5秒）
    """
    # 调用time.sleep()实现等待
    time.sleep(x)



def minimize_current_window():
    """缩小当前活动窗口（跨平台实现）"""
    platform = sys.platform
    try:
        if platform.startswith('win32'):
            # Windows系统：使用win32gui库

            # 获取当前活动窗口句柄
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                # 最小化窗口（SW_MINIMIZE = 6）
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                return True
            else:
                print("未找到当前活动窗口")
                return False

        elif platform.startswith('darwin'):
            # macOS系统：使用PyObjC调用AppKit框架
            from AppKit import NSWorkspace, NSApplication
            # 获取当前最前端的应用
            workspace = NSWorkspace.sharedWorkspace()
            front_app = workspace.frontmostApplication()
            if front_app:
                # 获取应用的主窗口并最小化
                app = front_app.activationPolicy()
                windows = NSApplication.sharedApplication().windows()
                if windows:
                    # 最小化第一个窗口（通常是主窗口）
                    windows[0].miniaturize_(None)
                    return True
            print("未找到可最小化的窗口")
            return False

        elif platform.startswith('linux'):
            # Linux系统：使用xdotool工具（需提前安装）
            try:
                # 调用xdotool命令最小化当前活动窗口
                subprocess.run(
                    ['xdotool', 'getactivewindow', 'windowminimize'],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                return True
            except subprocess.CalledProcessError:
                print("调用xdotool失败，请确保已安装xdotool（sudo apt install xdotool）")
                return False

        else:
            print(f"不支持的操作系统：{platform}")
            return False

    except ImportError as e:
        if platform.startswith('win32'):
            print(f"请安装依赖：pip install pywin32（错误：{e}）")
        elif platform.startswith('darwin'):
            print(f"请安装依赖：pip install pyobjc（错误：{e}）")
        return False
    except Exception as e:
        print(f"操作失败：{str(e)}")
        return False


