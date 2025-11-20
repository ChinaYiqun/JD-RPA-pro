import os
import sys
import time
import json
import requests
import pyautogui
import base64
from PIL import ImageGrab
from io import BytesIO
import tkinter as tk
from tkinter import ttk




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

            if action_type == "click" and len(box_args) >= 2:
                # 从boxArgs解析坐标
                x, y = int(box_args[0]), int(box_args[1])
                print(f"执行单击动作: ({x}, {y})")
                pyautogui.click(x, y)
            elif action_type == "double_click" and len(box_args) >= 2:
                # 支持双击动作
                x, y = int(box_args[0]), int(box_args[1])
                print(f"执行双击动作: ({x}, {y})")
                pyautogui.doubleClick(x, y)

            elif action_type == "answer":
                break

            # 等待动作执行完成
            time.sleep(3)
    except Exception as e:
        print(f"执行过程中发生异常: {str(e)}")
        execution_success = False
    finally:
        print("自动化循环结束")

        # 新增：创建结果显示窗口
        root = tk.Tk()
        root.title("执行结果")
        root.geometry("300x150")  # 设置窗口大小
        root.resizable(False, False)  # 禁止调整窗口大小

        # 根据执行状态显示不同内容
        if execution_success:
            message = "OK Success"
            color = "#008000"  # 绿色
        else:
            message = "Exception"
            color = "#FF0000"  # 红色

        # 创建标签显示结果
        label = ttk.Label(
            root,
            text=message,
            font=("SimHei", 24, "bold"),
            foreground=color
        )
        label.pack(expand=True)

        # 居中显示窗口
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry('{}x{}+{}+{}'.format(width, height, x, y))

        # 显示窗口
        root.mainloop()


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.insert(0, parent_dir)

    # ================= 已经在业务流程里面的TASK  =================#
    # click_search.py [ok]
    # hangup2reception.py [ok]
    # hangup_click_frist_message.py [ok]
    # pop_up_close.py
    # reception2hangup.py [ok]
    # reception_click_frist_message.py [ok]
    # transfer.py [ok]
    # search_first_customer.py [ok]
    # online_list_first_customer_name.py [ok]

    # from test import taskConfig, get_task_by_phase
    # result = taskConfig()
    # tasks = result.get("result", {}).get("tasks", [])
    # target_phase = "reception_click_frist_message"
    # task_prompt = get_task_by_phase(tasks, target_phase)

    # ================= 不在业务流程里面的TASK  =================#
    from dataset_generate.other_tasks import tasks_dict
    # open_merchant_backend [ok]
    # open_data_table [ok]
    # list_product [ok]
    # delist_product [ok]
    # check_new_message_in_online_consultation [ok]
    # click_i_know_right_panel [ok]
    # click_service_order_and_input [ok]
    # click_phone_and_close_popup [ok]
    # toggle_layout_compact_to_normal [ok]
    # select_enter_to_send_message [ok]
    # click_check_subsidy_and_close [ok]

    target_phase = "open_robot_chat"
    task_prompt = tasks_dict[target_phase]

    import pygetwindow as gw
    current_window = gw.getActiveWindow()
    if current_window:
        current_window.minimize()
    time.sleep(3)
    execute_automation_loop(default_task = task_prompt,max_loops=10,tid=f"yq_{target_phase}")
