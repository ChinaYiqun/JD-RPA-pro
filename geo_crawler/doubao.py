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
import pygetwindow as gw
import pandas as pd
# Configuration constants
MAX_AUTOMATION_LOOPS = 6
SEARCH_WAIT_SECONDS = 60
SCROLL_PAUSE_SECONDS = 1
REFERENCE_LINK_COUNT = 3

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Window initialization
current_window = gw.getActiveWindow()
if current_window:
    current_window.minimize()
time.sleep(3)
from common import *


def run_automation_phase(target_phase, task_prompt):
    """Helper function to execute an automation phase"""
    tid = f"tmp_{target_phase}_{time.time()}"
    print(tid)
    execute_automation_loop(default_task=task_prompt, max_loops=MAX_AUTOMATION_LOOPS, tid=tid)


def open_doubao_and_navigate():
    """Phase 1: Open Doubao and navigate to search bar"""
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
    run_automation_phase(target_phase, task_prompt)


def perform_search(query):
    """Perform search with given query"""
    paste_text_at_mouse_position(query)
    press_enter()
    time.sleep(SEARCH_WAIT_SECONDS)


def scroll_and_copy_content():
    """Scroll to bottom and copy all content"""
    scroll_and_pause(total_pixels_to_scroll=5000, pause_seconds=SCROLL_PAUSE_SECONDS)
    click_at_mouse_position()
    content = paste_all()
    print(content)
    return content


def expand_reference_details():
    """Phase 2: Expand reference details panel"""
    target_phase = "doubao_cua_2"
    task_prompt = '''step 1 点击页面下方的x篇资料 step 2 界面右侧出现参考资料列表则结束任务
    按照如下格式返回动作：
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
    </tool_call>
    或
    <tool_call>
    {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
    </tool_call>
    '''
    run_automation_phase(target_phase, task_prompt)


def extract_reference_links(num_links):
    """Phase 3: Extract reference links from right panel"""
    links = []
    for i in range(num_links):
        target_phase = f"doubao_cua_3_{i}"
        task_prompt = f'''step1 右键点击右侧的第{i + 1}个链接,step2 复制链接地址'''+'''
        <tool_call>
        {"name": "computer_use", "arguments": {"action": "right_click", "coordinate": [x, y]}}
        </tool_call>
        或
        <tool_call>
        {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
        </tool_call>
        或
        <tool_call>
        {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
        </tool_call>
        '''
        run_automation_phase(target_phase, task_prompt)
        link = get_clipboard_text()
        links.append(link)
    print(links)
    return links


import os  # Ensure os is imported (should already be present)

# ... existing code ...

if __name__ == "__main__":
    df_queries = pd.read_csv('queries.csv')

    # New: Remove results list - we'll save incrementally
    # results = []

    # Main workflow execution
    for index, row in df_queries.iterrows():
        query = row['query']
        print(f"Processing query {index + 1}/{len(df_queries)}: {query}")

        # New: Wrap query processing in try-except to isolate errors
        try:
            open_doubao_and_navigate()
            perform_search(query)
            content = scroll_and_copy_content()
            expand_reference_details()
            links = extract_reference_links(REFERENCE_LINK_COUNT)

            # New: Create single result DataFrame and append to CSV
            result_df = pd.DataFrame([{
                'query': query,
                'content': content,
                'links': str(links)
            }])

            # Append with header only if file doesn't exist yet
            result_df.to_csv(
                'query_results.csv',
                mode='a',  # Append mode
                index=False,
                encoding='utf-8',
                header=not os.path.exists('query_results.csv')  # Header for first write only
            )
            print(f"Query {index + 1} results appended to query_results.csv")

        except Exception as e:
            print(f"Error processing query {index + 1}: {str(e)}")
            # Continue to next query after error

        finally:
            # New: Ensure window closes even if error occurs
            close_current_window()

    print("All queries processed. Results saved to query_results.csv")