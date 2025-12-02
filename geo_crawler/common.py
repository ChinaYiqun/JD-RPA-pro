import os
import sys
import time
import json
import requests
import pyautogui
import base64
from PIL import ImageGrab
from io import BytesIO

import pyperclip

import signal

import pygetwindow as gw

def close_current_window():
    """关闭当前活动窗口"""
    current_window = gw.getActiveWindow()
    if current_window:
        current_window.close()


def capture_screenshot():
    """捕获屏幕截图并转换为base64编码"""
    screenshot = ImageGrab.grab()
    buffer = BytesIO()
    screenshot.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode()


def execute_automation_loop(default_task=r'''
        用户原始命令为：Step1 界面右侧的“查询补贴资格”，Step 2 关闭弹窗 Step3 停止任务
        如果有这样的按钮返回action为'left_click'，coordinate为[x, y]；
        判断是点击成功，若点击返回action为'terminate'，status为'success'。有任何执行失败返回action为'terminate'，status为'failure'。
        按照如下格式返回动作：
        <tool_call>
        {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
        </tool_call>
        或者
        <tool_call>
        {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
        </tool_call>



''',
                            max_loops=10,
                            tid = f"default_task_{int(time.time())}"  ):
    # {int(time.time())}
    """
    执行自动化循环

    Args:
        default_task: 默认用户输入任务
        max_loops: 最大循环次数，防止无限循环
    """
    loop_count = 0

    uid = "default_user"
    execution_success = True
    try:
        while loop_count < max_loops:
            loop_count += 1
            print(f"循环次数: {loop_count}/{max_loops}")


            screenshot_base64 = capture_screenshot()


            api_url = "http://localhost:6666/api/lam/planAction"
            payload = {
                "uid": uid,
                "tid": tid,
                "task": default_task,
                "language": "中文",
                "image": screenshot_base64
            }


            response = requests.post(api_url, json=payload)
            response_data = response.json()


            if response_data.get("result", {}).get("status") == "FINISH":
                print("收到终止信号，结束循环")
                break


            action_type = response_data.get("result", {}).get("answer", {}).get("actionType")
            action_inputs = response_data.get("result", {}).get("answer", {}).get("actionInputs", {})

            box_args = response_data.get("result", {}).get("answer", {}).get("boxArgs", [])

            if (action_type == "click" or action_type == "left_click") and len(box_args) >= 2:
                # 从boxArgs解析坐标
                x, y = int(box_args[0]), int(box_args[1])
                print(f"执行单击动作: ({x}, {y})")
                pyautogui.click(x, y)
            elif action_type == "double_click" and len(box_args) >= 2:
                # 支持双击动作
                x, y = int(box_args[0]), int(box_args[1])
                print(f"执行双击动作: ({x}, {y})")
                pyautogui.doubleClick(x, y)
            elif action_type == "right_click" and len(box_args) >= 2:
                # 支持右键点击动作
                x, y = int(box_args[0]), int(box_args[1])
                print(f"执行右键点击动作: ({x}, {y})")
                pyautogui.rightClick(x, y)

            elif action_type == "answer":
                break

            # 等待动作执行完成
            time.sleep(3)
    except Exception as e:
        print(f"执行过程中发生异常: {str(e)}")
        execution_success = False
    finally:
        print(f"tid: {tid} 自动化循环结束")

def paste_text_at_mouse_position(text: str):

    """将指定文本复制到剪贴板并粘贴到当前鼠标位置"""
    pyperclip.copy(text)  # 复制文本到剪贴板
    time.sleep(0.1)  # 短暂延迟确保剪贴板操作完成
    pyautogui.hotkey('ctrl', 'v')  # 使用Ctrl+V粘贴文本（Windows系统）
    time.sleep(0.1)  # 短暂延迟确保剪贴板操作完成


def paste_all():
    time.sleep(0.1)  # 短暂延迟确保剪贴板操作完成
    pyautogui.hotkey('ctrl', 'a')  # 全选
    time.sleep(0.1)

    # 保存原始SIGINT( Ctrl+C )信号处理器
    original_sigint_handler = signal.getsignal(signal.SIGINT)
    try:
        # 临时忽略SIGINT信号，防止模拟Ctrl+C导致程序退出
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        pyautogui.hotkey('ctrl', 'c')  # 复制
        time.sleep(0.1)  # 等待复制操作完成
    finally:
        # 恢复原始SIGINT信号处理器
        signal.signal(signal.SIGINT, original_sigint_handler)

    return pyperclip.paste()

def press_enter():
    """Simulate pressing the Enter key"""
    pyautogui.press('enter')

# 获取粘贴板文本
def get_clipboard_text():
    """获取粘贴板文本"""
    return pyperclip.paste()

def click_at_mouse_position():
    """在当前鼠标位置执行单击操作"""
    x, y = pyautogui.position()  # 获取当前鼠标位置
    pyautogui.click(x, y)  # 在当前鼠标位置执行单击操作

def scroll_and_pause(total_pixels_to_scroll, pause_seconds):
    """
    向下滚动指定的总像素数，每滚动一段距离后停顿。

    :param total_pixels_to_scroll: 每次停顿前需要滚动的总像素数
    :param pause_seconds: 每滚动一段距离后的停顿时间（秒）
    """
    print(f"开始滚动，每向下滚动 {total_pixels_to_scroll} 像素，停顿 {pause_seconds} 秒。")
    print("按 Ctrl+C 可随时退出程序。")

    try:
        while True:
            # 获取当前鼠标位置，以便滚动后能回到原位（可选步骤，但推荐）
            # 有些应用的滚动行为会依赖鼠标位置
            current_x, current_y = pyautogui.position()

            # 向下滚动
            # pyautogui.scroll() 的参数是滚动的“步长”。
            # 在大多数系统和应用中，1 个单位大约等于 1 行文本的高度。
            # 为了精确滚动 500 像素，我们需要一个循环来累积滚动距离。
            # 这里我们每次滚动 10 像素，直到累积达到 500 像素。
            scroll_amount = 0
            while scroll_amount < total_pixels_to_scroll:
                # 每次滚动 10 像素
                pyautogui.scroll(-500)
                scroll_amount += 500
                time.sleep(0.01)  # 短暂延时，使滚动更平滑

            # 滚动完成后，将鼠标移回原位
            pyautogui.moveTo(current_x, current_y)

            print(f"已滚动 {total_pixels_to_scroll} 像素，开始停顿 {pause_seconds} 秒...")
            time.sleep(pause_seconds)

            # 检测是否还能继续滚动
            # 原理：滚动后立即尝试再次向下滚动一小段距离，然后检查鼠标位置是否发生了变化。
            # 如果鼠标位置（特别是 y 坐标）没有变化，说明已经滚动到底部了。
            # 注意：这个方法并非 100% 可靠，因为某些应用的滚动不会改变鼠标位置。
            pyautogui.scroll(-50)
            new_x, new_y = pyautogui.position()

            # 如果位置没有变化，说明滚动到底部
            if new_y == current_y:
                print("检测到已滚动至底部，程序即将退出。")
                break
            else:
                # 如果还能滚动，就把页面滚回到之前的位置，准备下一轮循环
                pyautogui.scroll(50)
                pyautogui.moveTo(current_x, current_y)

    except KeyboardInterrupt:
        print("\n程序被用户手动中断。")
    except Exception as e:
        print(f"\n发生错误: {e}")