import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

import time
import pygetwindow as gw
import pandas as pd

# Configuration constants
MAX_AUTOMATION_LOOPS = 5
SEARCH_WAIT_SECONDS = 35
SCROLL_PAUSE_SECONDS = 1
REFERENCE_LINK_COUNT = 3

edge_path="C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
gptlink = 'https://copilot.microsoft.com/'

# Window initialization
current_window = gw.getActiveWindow()
if current_window:
    current_window.minimize()
time.sleep(0.3)

from common import *


def run_automation_phase(target_phase, task_prompt):
    """Helper function to execute an automation phase"""
    tid = f"crawler_{target_phase}_{time.time()}"
    print(tid)
    execute_automation_loop(default_task=task_prompt, max_loops=MAX_AUTOMATION_LOOPS, tid=tid)

import subprocess

def openedge():
    #打开浏览器
    subprocess.Popen(edge_path)
    time.sleep(1)
    print('打开浏览器')

def opengpt(gptlink):
    fast_key_ctrl_t
    #在浏览器里打开ai网页
    perform_search(gptlink)
    time.sleep(1)
    print('打开网页')

def perform_search(query):
    paste_text_at_mouse_position(query)
    press_enter()
    time.sleep(2)
    print('执行搜索')

def scroll():
    scroll_and_pause(total_pixels_to_scroll=5000, pause_seconds=SCROLL_PAUSE_SECONDS)

def newchat():
    target_phase = "newchat"
    task_prompt = '''
        step1 鼠标点击左边的新聊天按钮
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


def copy_content():
    scroll()
    target_phase = "copy_content"
    task_prompt = '''
        step1 鼠标点击生成内容下方的复制标志
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
    return get_clipboard_text()


def extract_reference_links(num_links):
    links = []
    for i in range(num_links):
        target_phase = "copy_links"
        task_prompt = '''
            step1 右键点击右侧的第{i}个链接
            按照如下格式返回动作：
            <tool_call>
            {"name": "computer_use", "arguments": {"action": "right_click", "coordinate": [x, y]}}
            </tool_call>
            或者
            <tool_call>
            {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
            </tool_call>
            '''
        run_automation_phase(target_phase, task_prompt)
        time.sleep(0.01)
        click_text_position(r"复制链接", match_type='contains')
        link = get_clipboard_text()
        links.append(link + '\n')
    print(links)
    return links


if __name__ == "__main__":

    df_queries = pd.read_csv('queries.csv')
    openedge()

    for index, row in df_queries.iterrows():
        if  index<5:
            opengpt(gptlink)
            query = row['query']
            print(f"加载列内容 {index + 1}/{len(df_queries)}: {query}")
            #click_text_position(r"向Copilot发送消息", match_type='contains')
            perform_search(query)
            time.sleep(30)
            content = copy_content()
            click_text_position(r"全部显示", match_type='contains')
            links = extract_reference_links(REFERENCE_LINK_COUNT)

            # New: Create single result DataFrame and append to CSV
            result_df = pd.DataFrame([{
                'query': query,
                'content': content,
                'links': str(links)
            }])

            # 输出
            result_df.to_csv(
                'output.csv',
                mode='a',  # Append mode
                index=False,
                encoding='utf-8',
                header=not os.path.exists('output.csv')  # Header for first write only
            )
            print(f"列{index + 1}结果已追加到output.csv")

        else:
            continue

    print("任务结束。结果保存至output.csv")