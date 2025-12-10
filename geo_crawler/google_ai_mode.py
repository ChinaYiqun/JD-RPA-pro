import pyautogui
import os
import time
import re
import subprocess
import pandas as pd
import pygetwindow as gw
import pyautogui
from PIL import Image
import base64
import json

from openai import OpenAI
import pyperclip

SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()  # 获取当前屏幕分辨率


MULTI_RES_COORDS = {
    # 分辨率: {
    #     "元素名": (相对 x, 相对 y)
    # }
    (2560, 1600): {  # 2K 屏幕
        "ai_mode_button": (0.66367, 0.479375),  # (1699, 767) (近似)
        "close_advertisement": (0.347265625, 0.21125),  # (889, 338) (近似)
        "input_box": (0.485546875, 0.499375),  # (1243, 799) (近似)
        "space_area": (0.146875, 0.238125),  # (376, 381)(近似)
        "response_area": (0.37109375, 0.52375),  # 196, 262 (近似)
        "new_chat_button": (0.02265625, 0.23625),  # (58, 378) (近似)
        "link_copy_options": [
            (0.689453125, 0.33375),  # (1765, 534) (近似)
            (0.6921875, 0.445),  # (1772, 712) (近似)
            (0.6921875, 0.56875)   # (1772, 910) (近似)
        ]
    },
    (1920, 1080): {  # 1080P
        "ai_mode_button": (0.688, 0.435),  # 1321, 470 (近似)
        "close_advertisement": (0.3693, 0.2639),  # 709, 285 (近似)
        "input_box": (0.456, 0.494),  # 876, 534 (近似)
        "space_area": (0.140625, 0.29629),  # (270, 320)(近似)
        "response_area": (0.102, 0.242),  # 196, 262 (近似)
        "new_chat_button": (0.02604, 0.29259),  # (50, 316) (近似)
        "link_copy_options": [
            (0.7875, 0.398),  # (1512, 430) (近似)
            (0.7817, 0.5537),  # (1501, 598) (近似)
            (0.777, 0.706)   # (1492, 763) (近似)
        ]
    }
    # 可继续添加其他分辨率...
}

def get_coords_for_resolution(res_width, res_height):
    """根据当前分辨率获取坐标字典"""
    target_res = (res_width, res_height)
    if target_res in MULTI_RES_COORDS:
        return MULTI_RES_COORDS[target_res]
    else:
        # 如果未找到精确匹配，返回默认或最接近的
        print(f"[WARN] 未找到分辨率 {res_width}x{res_height} 的预设坐标，使用默认缩放逻辑")
        # 可以选择返回 2K 的相对坐标作为 fallback
        return MULTI_RES_COORDS[(1920, 1080)]

def get_absolute_coords(res_width, res_height, element_key):
    """获取指定分辨率下某元素的绝对坐标"""
    coords_map = get_coords_for_resolution(res_width, res_height)
    rel_x, rel_y = coords_map[element_key]
    return int(rel_x * res_width), int(rel_y * res_height)


SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()  # 获取当前屏幕分辨率
# input_x, input_y = get_absolute_coords(SCREEN_WIDTH, SCREEN_HEIGHT, "input_box")
# print(input_x, input_y)
# pyautogui.click(input_x, input_y)


DEFAULT_BROWSER = "edge"
GOOGLE_AI_URL = "https://www.google.com"  # 或你的 Google AI 具体 URL

SUPPORTED_BROWSERS = {
    "edge": {
        # 关键：添加 --start-maximized 参数
        "cmd": 'start msedge  "{url}"'
    },
    "chrome": {
        "cmd": 'start chrome  "{url}"'
    },
    # 可扩展其他浏览器
}

# Qwen3-VL 配置（本地部署）
LOCAL_CONFIG = {
    "qwen3-vl-8b": {
        "base_url": "http://10.103.62.29:8123/v1",
        "api_key": "",
        "model": "/home/lenovo/Project/ModelDir/Qwen3-VL-8B-Instruct/"
    }
}

selected_model = "qwen3-vl-8b"
base_url = LOCAL_CONFIG[selected_model]["base_url"]
api_key = LOCAL_CONFIG[selected_model]["api_key"]

MODEL_ID_FOR_API = LOCAL_CONFIG[selected_model]["model"]

# -----------------------------
# Qwen 系统提示（强调输入图是 1000x1000）
# -----------------------------
qwen_system_prompt = """You are a helpful assistant.
# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{"type": "function", "function": {"name": "computer_use", "description": "Use a mouse and keyboard to interact with a computer, and take screenshots.\n* This is an interface to a desktop GUI. You do not have access to a terminal or applications menu. You must click on desktop icons to start applications.\n* The screenshot you receive is always resized to 1000x1000 pixels.\n* All coordinates you output must be in this 1000x1000 image coordinate system (i.e., x and y are integers between 0 and 1000).\n* Some applications may take time to start or process actions, so you may need to wait and take successive screenshots to observe results.", "parameters": {"properties": {"action": {"description": "The action to perform...", "enum": ["key", "type", "mouse_move", "left_click", "left_click_drag", "right_click", "middle_click", "double_click", "triple_click", "scroll", "hscroll", "wait", "terminate", "answer"], "type": "string"}, "keys": {"type": "array"}, "text": {"type": "string"}, "coordinate": {"type": "array"}, "pixels": {"type": "number"}, "time": {"type": "number"}, "status": {"type": "string", "enum": ["success", "failure"]}}, "required": ["action"], "type": "object"}}}
</tools>

For each function call, return a json object with function name and arguments within <tool_call><tool_call> XML tags:
<tool_call>
{"name": "computer_use", "arguments": <args-json-object>}
</tool_call>
"""


# -----------------------------
# 工具函数（Qwen 相关）
# -----------------------------
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def construct_system_prompt(instruct: str, image_path: str, history: list = None) -> list:
    base64_image = encode_image(image_path)
    image_format = image_path.split('.')[-1]
    image_url = {
        "type": "image_url",
        "image_url": {"url": f"data:image/{image_format};base64,{base64_image}"}
    }
    history = history or []
    user_text = {"type": "text", "text": instruct}
    new_content = [image_url, user_text]
    if not history:
        return [
            {"role": "system", "content": [{"type": "text", "text": qwen_system_prompt}]},
            {"role": "user", "content": new_content}
        ]
    return history + [{"role": "user", "content": new_content}]


def parser_action(content: str, image_path: str) -> tuple:
    pattern = r'<tool_call>(.*?)</tool_call>'
    tool_call_matches = re.findall(pattern, content, re.DOTALL)
    if not tool_call_matches:
        return None, None

    action_list = []
    param_list = []

    for tool_call in tool_call_matches:
        json_str = tool_call.strip()
        try:
            data = json.loads(json_str)
            args = data['arguments']
            action = args.get('action')
            if not action:
                continue

            if action in ['left_click', 'right_click', 'mouse_move', 'double_click']:
                coord = args.get('coordinate')
                if isinstance(coord, list) and len(coord) == 2:
                    x_1000, y_1000 = coord
                    x_real = int(x_1000 * (SCREEN_WIDTH / 1000))
                    y_real = int(y_1000 * (SCREEN_HEIGHT / 1000))
                    x_real = max(0, min(x_real, SCREEN_WIDTH - 1))
                    y_real = max(0, min(y_real, SCREEN_HEIGHT - 1))
                    action_list.append(action)
                    param_list.append((x_real, y_real))
            elif action == 'type':
                text = args.get('text')
                if text is not None:
                    action_list.append(action)
                    param_list.append(text)
            elif action == 'key':
                keys = args.get('keys')
                if keys:
                    action_list.append(action)
                    param_list.append(keys[0])
            elif action == 'scroll':
                pixels = args.get('pixels')
                if pixels is not None:
                    action_list.append(action)
                    param_list.append(pixels)
            elif action == 'wait':
                seconds = args.get('time')
                if seconds is not None:
                    action_list.append(action)
                    param_list.append(float(seconds))
            elif action == 'terminate':
                status = args.get('status', 'success')
                action_list.append(action)
                param_list.append(status)
            elif action == 'answer':
                text = args.get('text')
                if text is not None:
                    action_list.append(action)
                    param_list.append(text)
        except Exception as e:
            print(f"解析错误: {e}, 内容: {json_str}")

    return action_list, param_list


def execute_action(action, param):
    """执行单个动作"""
    print(f"执行动作: {action}, 参数: {param}")
    try:
        if action == 'mouse_move':
            x, y = param
            pyautogui.moveTo(x, y)
        elif action == 'left_click':
            x, y = param
            pyautogui.click(x, y)
        elif action == 'right_click':
            x, y = param
            pyautogui.rightClick(x, y)
        elif action == 'double_click':
            x, y = param
            pyautogui.doubleClick(x, y)
        elif action == 'type':
            pyperclip.copy(str(param))  # 确保是字符串
            time.sleep(0.1)
            pyautogui.hotkey('ctrl', 'v')  # Windows/Linux
        elif action == 'key':
            pyautogui.press(param)
        elif action == 'scroll':
            pyautogui.scroll(int(param))
        elif action == 'wait':
            time.sleep(param)
        elif action == 'terminate':
            return param
        elif action == 'answer':
            print(f"模型回答: {param}")
    except Exception as e:
        print(f"执行动作失败: {e}")
    return None


def capture_screenshot():
    path = "google_temp_screenshot.png"
    screenshot = pyautogui.screenshot()
    resized = screenshot.resize((1000, 1000), Image.LANCZOS)
    resized.save(path)
    return path


def execute_with_qwen_vl(task_prompt: str, max_steps=5):
    client = OpenAI(base_url=base_url, api_key=api_key)
    history = None
    step = 0

    while step < max_steps:
        step += 1
        print(f"\n--- Step {step} ---")
        screenshot_path = capture_screenshot()

        messages = construct_system_prompt(task_prompt, screenshot_path, history)

        try:
            response = client.chat.completions.create(
                model=MODEL_ID_FOR_API,
                messages=messages,
                temperature=0.0,
                stream=False,
                tool_choice="none"
            )
            output_text = response.choices[0].message.content
            print("模型输出:", output_text)

            actions, params = parser_action(output_text, screenshot_path)
            if not actions:
                print("未解析到有效动作，终止。")
                break

            terminated = False
            for act, par in zip(actions, params):
                result = execute_action(act, par)
                if act == 'terminate':
                    print(f"任务终止，状态: {result}")
                    terminated = True
                    return result == 'success'
                time.sleep(0.5)

            history = messages + [{"role": "assistant", "content": output_text}]

            if terminated:
                break

            time.sleep(1)

        except Exception as e:
            print(f"调用模型出错: {e}")
            break

    print("达到最大步数，任务可能未完成。")
    return False

def open_google_ai_in_browser(browser_name=None):
    """启动浏览器并打开 Google AI Mode，确保窗口最大化"""
    if browser_name is None:
        browser_name = DEFAULT_BROWSER  # 强制使用 Edge

    if browser_name not in SUPPORTED_BROWSERS:
        raise ValueError(f"不支持的浏览器: {browser_name}")

    browser_config = SUPPORTED_BROWSERS[browser_name]
    print(f"正在启动 {browser_name} 并打开 Google AI Mode...")

    cmd = browser_config["cmd"].format(url=GOOGLE_AI_URL)
    # 在 Windows 上使用 shell=True 执行 start 命令
    subprocess.run(cmd, shell=True)

    return browser_name


def click_maximize_button():
    """
    使用 Qwen-VL 识别 Edge 浏览器窗口右上角的“最大化”按钮（□ 图标），
    并左键点击它以最大化窗口。
    如果窗口已最大化（按钮变为“还原”图标），则直接返回成功。
    """
    prompt = """
你正在操作 Microsoft Edge 浏览器窗口（Windows 系统）。

任务目标：
- 在当前屏幕中定位最前端的 Edge 浏览器窗口；
- 查看其**右上角的三个窗口控制按钮**（从左到右通常是：最小化 —、最大化 □、关闭 ×）；
- 判断中间的“最大化”按钮状态：
  - 如果它是 **□（空心方框）**，说明窗口**尚未最大化** → 请**左键点击该按钮**；
  - 如果它已变为 **❐（两个重叠方框）或 ↓（向下箭头）**，说明窗口**已经最大化** → 无需操作，直接返回 terminate success。

重要提示：
- 按钮位于窗口最右上角，紧邻关闭按钮（×）；
- 只有在看到明确的 □ 图标时才点击；
- 坐标必须基于当前 1000x1000 截图；
- 不要点击网页内容、地址栏、标签页或关闭按钮！

返回格式（二选一）：

<tool_call>
{"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
</tool_call>
（[x, y] 是 □ 按钮中心在 1000x1000 图中的坐标）

或

<tool_call>
{"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
</tool_call>
（如果窗口已最大化）
"""
    success = execute_with_qwen_vl(prompt, max_steps=2)
    print("窗口已最大化" if success else "未能完成最大化操作")
    return success

def type_and_send_query(query: str):
    time.sleep(1)
    input_x, input_y = get_absolute_coords(SCREEN_WIDTH, SCREEN_HEIGHT, "input_box")
    pyautogui.click(input_x, input_y)
    pyperclip.copy(str(query))  # 确保是字符串
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'v')  # Windows/Linux
    pyautogui.press('enter')

def copy_google_response():
    input_x, input_y = get_absolute_coords(SCREEN_WIDTH, SCREEN_HEIGHT, "space_area")
    pyautogui.click(input_x, input_y)
    pyautogui.hotkey('ctrl', 'a')
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.1)
    content = pyperclip.paste()
    time.sleep(0.1)
    input_x, input_y = get_absolute_coords(SCREEN_WIDTH, SCREEN_HEIGHT, "space_area")
    pyautogui.click(input_x, input_y)
    return content

def extract_google_reference_links():
    """尝试提取 Google AI 回答中的参考链接"""
    links = []

    coords_map = get_coords_for_resolution(SCREEN_WIDTH, SCREEN_HEIGHT)
    point = coords_map["link_copy_options"]

    for i in range(len(point)):
        x = point[i][0] * SCREEN_WIDTH
        y = point[i][1] * SCREEN_HEIGHT
        pyautogui.rightClick(x, y)
        time.sleep(2)
        """点击 Google AI 的复制链接"""
        prompt = """
            请左键点击页面右侧的"复制链接"按钮。如果存在"复制链接"按钮，左键点击"复制链接"按钮后再返回 terminate success。否则直接返回terminate success
            返回格式：
           <tool_call>
            {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
           </tool_call>
            或
           <tool_call>
            {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
           </tool_call>
            """
        success = execute_with_qwen_vl(prompt, max_steps=3)

        if success:
            links.append(pyperclip.paste())
        print(links)
        time.sleep(1)
        #pyautogui.leftClick(2525, 201)
    return links

def new_chat():
    input_x, input_y = get_absolute_coords(SCREEN_WIDTH, SCREEN_HEIGHT, "new_chat_button")
    pyautogui.click(input_x, input_y)
    # pyautogui.click(input_x, input_y)


if __name__ == "__main__":
    current = gw.getActiveWindow()
    if current:
        current.minimize()
    time.sleep(1)
    # 启动 Google AI Mode - 使用Edge浏览器
    browser_used = open_google_ai_in_browser("edge")
    time.sleep(3)
    click_maximize_button()
    time.sleep(1)
    input_x, input_y = get_absolute_coords(SCREEN_WIDTH, SCREEN_HEIGHT, "ai_mode_button")
    pyautogui.click(input_x, input_y)
    time.sleep(10)
    input_x, input_y = get_absolute_coords(SCREEN_WIDTH, SCREEN_HEIGHT, "close_advertisement")
    pyautogui.click(input_x, input_y)
    time.sleep(1)
    input_x, input_y = get_absolute_coords(SCREEN_WIDTH, SCREEN_HEIGHT, "input_box")
    pyautogui.click(input_x, input_y)

    if not os.path.exists('queries.csv'):
        pd.DataFrame([{"query": "What is the best laptop under 5000 yuan?"}]).to_csv('queries.csv', index=False,
                                                                                     encoding='utf-8')
        print("已创建示例 queries.csv，请编辑后重新运行。")

    df_queries = pd.read_csv('queries.csv')

    for index, row in df_queries.iterrows():
        if index == 5:
            break
        time.sleep(3)
        query = str(row['query']).strip()
        if not query:
            continue
        print(f"\n{'=' * 50}")
        print(f"处理查询 {index + 1}/{len(df_queries)}: {query}")

        try:
            # 输入并发送问题
            type_and_send_query(query)
            time.sleep(30)  # 可根据网络调整

            # 复制回答
            content = copy_google_response()
            print(content)

            links = extract_google_reference_links()

            print(links)

            # 保存到 CSV
            result_df = pd.DataFrame([{
                'query': query,
                'content': content,
                'links': str(links)  # 转为字符串存储
            }])

            result_df.to_csv(
                'google_query_results.csv',
                mode='a',
                index=False,
                encoding='utf-8',
                header=not os.path.exists('google_query_results.csv')
            )
            print(f"结果已保存到 google_query_results.csv")
            new_chat()

        except Exception as e:
            print(f"处理查询 {index + 1} 时出错: {e}")
            import traceback
            traceback.print_exc()