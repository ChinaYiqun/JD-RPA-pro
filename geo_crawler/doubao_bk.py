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

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
import pygetwindow as gw
current_window = gw.getActiveWindow()
if current_window:
    current_window.minimize()
time.sleep(3)
from common import *

if __name__ == "__main__":


    # cua_1 打开豆包,定位到搜索栏
    target_phase = "doubao_cua_1"
    task_prompt = '''
    step 1 双击打卡豆包
    step 2 鼠标点击左侧新对话
    step 3 鼠标点击定位到到中间的搜索栏
    按照如下格式返回动作：
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "double_click", "coordinate": [x, y]}}
    </tool_call>
    或者
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
    </tool_call>
    或者
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
    </tool_call>
    '''
    tid = f"tmp_{target_phase}_{time.time()}"
    execute_automation_loop(default_task = task_prompt,max_loops=10,tid=tid)
    # =====================================

    # 搜索内容并等待页面结果
    search_name = "最近5000以内的笔记本电脑梯队咋样，哪款性价比最稳？"
    paste_text_at_mouse_position(search_name)
    press_enter()
    time.sleep(60)
    # =====================================


    # 滚动到页面底端，复制粘贴所有内容
    scroll_and_pause(total_pixels_to_scroll=5000, pause_seconds=1)
    click_at_mouse_position()
    content = paste_all()
    print(content)
    #==================================


    # cua_2 点击展开资料详情
    target_phase = "doubao_cua_2"

    task_prompt = '''step 1 点击页面下方的x篇资料 step 2 界面右侧出现参考资料列表则结束任务
    按照如下格式返回动作：
    '''  +  '''
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
    </tool_call>
    或
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "terminate", "status为": "success"}}
    </tool_call>

    '''
    tid = f"tmp_{target_phase}_{time.time()}"
    execute_automation_loop(default_task = task_prompt,max_loops=10,tid=tid)
    #==================================

    # cua_3 遍历复制链接地址
    links = []
    for i in range(3):
        target_phase = f"doubao_cua_3_{i}"

        task_prompt = f'''step1 右键点击右侧的第{i+1}个链接,step2 复制链接地址
        '''  +  '''
        <tool_call>
        {"name": "computer_use", "arguments": {"action": "right_click", "coordinate": [x, y]}}
        </tool_call>
        或
        <tool_call>
        {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
        </tool_call>
        或
        <tool_call>
        {"name": "computer_use", "arguments": {"action": "terminate", "status为": "success"}}
        </tool_call>

        '''
        tid = f"tmp_{target_phase}_{time.time()}"
        execute_automation_loop(default_task=task_prompt, max_loops=10, tid=tid)
        link = get_clipboard_text()
        links.append(link)
    print(links)
    # ==================================


    close_current_window()
