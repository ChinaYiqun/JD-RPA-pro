import os
import sys
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
import  pyperclip
# -----------------------------
# 获取当前屏幕真实分辨率（用于坐标映射）
# -----------------------------
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
print(f"[INFO] 检测到主屏幕分辨率为: {SCREEN_WIDTH} x {SCREEN_HEIGHT}")

# -----------------------------
# 配置区
# -----------------------------
KIMI_URL = "https://www.kimi.com/"

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
{"name": <function-name>, "arguments": <args-json-object>}
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
    path = "kimi_temp_screenshot.png"
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

# -----------------------------
# 网页版 Kimi 控制逻辑（Edge 浏览器）
# -----------------------------
def open_kimi_in_edge():
    """启动 Edge 并打开 Kimi 网页"""
    print("正在启动 Microsoft Edge 并打开 Kimi 网页...")
    # 使用 edge://newtab 保证新标签页打开，避免被默认页干扰
    cmd = f'start msedge --new-window "{KIMI_URL}"'
    subprocess.run(cmd, shell=True)
    time.sleep(8)  # 等待页面加载

def focus_edge_kimi_window():
    """聚焦包含 Kimi 的 Edge 窗口"""
    for _ in range(15):  # 延长等待时间，网页加载较慢
        # Edge 窗口标题通常包含页面标题，如 "Kimi - 月之暗面" 或 "moonshot"
        for keyword in ["Kimi", "moonshot", "月之暗面"]:
            windows = gw.getWindowsWithTitle(keyword)
            if windows:
                win = windows[0]
                try:
                    win.activate()
                    time.sleep(1)
                    print(f"已聚焦浏览器窗口: {win.title}")
                    return win
                except Exception as e:
                    print(f"激活窗口失败: {e}")
        time.sleep(1)
    raise RuntimeError("未能找到或激活 Kimi 网页窗口")

def new_chat_web():
    """在网页中新建对话（点击右上角 '+'）"""
    time.sleep(0.1)  # 短暂延迟确保剪贴板操作完成
    pyautogui.hotkey('ctrl', 'k')  # 全选
    time.sleep(0.1)
    return

def click_input_area_web():
    """点击网页底部的输入框（通常有 placeholder 如“有问题尽管问”）"""
    prompt = """
    用户命令：点击 Kimi 网页底部的文本输入区域（通常有浅灰色文字如“尽管问”或“输入问题”）。
    如果找到输入框，请点击它；
    如果已聚焦（光标闪烁），可直接返回 terminate success。
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
    print("点击输入框成功" if success else "点击输入框失败")
    return success

def type_and_send_query(query: str):
    """输入问题并按 Enter 发送，发送后立即终止任务（成功条件：Enter 已按下）"""
    prompt = f"""
你正在操作 Kimi 网页版，输入框已经聚焦。

请严格按顺序执行以下两个操作，然后立即终止任务：
1. 使用 type 动作输入完整问题文本；
2. 使用 key 动作按下 "enter" 键；
3. 立即返回 terminate 动作，status 为 "success"。

用户问题：
“{query}”

必须返回以下三个动作（顺序不可变）：
<tool_call>
{{"name": "computer_use", "arguments": {{"action": "type", "text": "{query}"}}}}
</tool_call>
<tool_call>
{{"name": "computer_use", "arguments": {{"action": "key", "keys": ["enter"]}}}}
</tool_call>
<tool_call>
{{"name": "computer_use", "arguments": {{"action": "terminate", "status": "success"}}}}
<tool_call>

不要做任何其他操作（如点击、滚动、等待回复等）。
"""
    # 最多 1 轮即可完成（模型一次性输出三个动作）
    success = execute_with_qwen_vl(prompt, max_steps=1)
    print(f"已提交查询: {query}" if success else f"提交失败: {query}")
    return success


def extract_kimi_reference_links(num_links=3):
    """尝试提取 Kimi 回答中的参考资料链接（最多 num_links 个）"""
    links = []
    for i in range(num_links):
        print(f"正在提取第 {i + 1} 个参考链接...")
        prompt = f'''
        如果页面右侧或回答下方存在“参考资料”、“引用”、“来源”等区域，并且包含可点击的链接（通常带有地球图标、URL 或“查看原文”字样），
        请右键点击第 {i + 1} 个这样的链接，然后选择“复制链接地址”。

        如果找不到第 {i + 1} 个链接，请直接返回 terminate success。

        返回格式：
       <tool_call>
        {{"name": "computer_use", "arguments": {{"action": "right_click", "coordinate": [x, y]}}}}
       </tool_call>
        或
       <tool_call>
        {{"name": "computer_use", "arguments": {{"action": "terminate", "status": "success"}}}}
       </tool_call>
        '''
        success = execute_with_qwen_vl(prompt, max_steps=3)
        if not success:
            # 即使模型返回 success，也可能没找到链接
            link = pyperclip.paste().strip()
            if link and link.startswith(('http://', 'https://')):
                links.append(link)
                print(f"提取到链接: {link}")
            else:
                print("未检测到有效链接，停止提取")
                break
        else:
            # 模型可能执行了右键，但需手动复制（有些浏览器右键菜单需再点“复制链接”）
            # 为简化，我们假设右键后自动复制（或依赖后续粘贴）
            time.sleep(0.5)
            link = pyperclip.paste().strip()
            if link and link.startswith(('http://', 'https://')):
                links.append(link)
                print(f"提取到链接: {link}")
            else:
                # 尝试左键点击“复制”选项（复杂，暂不实现）
                print("未获取到链接，停止提取")
                break
    return links


def copy_kimi_response():
    """
    构建提示词调用大模型点击Kimi左下角的复制回答按钮，并获取内容。
    返回值为从剪贴板中读取的内容。
    """
    prompt = """
    请执行以下步骤来复制Kimi的回答：

    1. 在当前页面查找并定位到左下角带有“复制”、“复制回答”或类似含义的按钮（位于输入框上方），形状为两个叠加的小正方形。
    2. 执行鼠标左键单击动作以激活复制功能。
    3. 如果成功复制了回答，请立即终止任务，并返回 terminate success。

    返回格式：
   <tool_call>
    {"name": "computer_use", "arguments": {"action": "left_click", "coordinate": [x, y]}}
   </tool_call>
    或
   <tool_call>
    {"name": "computer_use", "arguments": {"action": "terminate", "status": "success"}}
   </tool_call>
    """

    # 调用 execute_with_qwen_vl 函数执行提示词操作
    success = execute_with_qwen_vl(prompt, max_steps=2)

    if not success:
        print("未能成功复制回答")
        return ""

    # 等待一小段时间确保复制操作完成
    time.sleep(1)

    # 使用 pyperclip 获取剪贴板内容
    content = pyperclip.paste()

    # 清除剪贴板以防影响后续操作
    pyperclip.copy('')

    print(f"已复制的内容: {content}")
    return content



def main():
    if not os.path.exists('queries.csv'):
        pd.DataFrame([{"query": "Kimi 是什么？"}]).to_csv('queries.csv', index=False, encoding='utf-8')
        print("已创建示例 queries.csv，请编辑后重新运行。")
        return

    df_queries = pd.read_csv('queries.csv')

    # 启动网页版 Kimi
    open_kimi_in_edge()
    focus_edge_kimi_window()
    i = 0
    for index, row in df_queries.iterrows():
        i = i + 1
        if i == 3: break
        query = str(row['query']).strip()
        if not query:
            continue
        print(f"\n{'=' * 50}")
        print(f"处理查询 {index + 1}/{len(df_queries)}: {query}")

        try:
            # 每个 query 新建一个对话
            new_chat_web()
            print("新建对话")
            time.sleep(2)

            if not click_input_area_web():
                print("无法点击输入框，跳过此 query")
                continue

            if not type_and_send_query(query):
                print("无法发送查询")
                continue

            # 等待 Kimi 回复加载（含参考资料）
            print("等待 Kimi 回复及参考资料加载...")
            time.sleep(80)  # 可根据网络调整

            # 复制Kimi的回答
            content = copy_kimi_response()
            # === 新增：提取参考链接 ===
            links = extract_kimi_reference_links(num_links=3)
            print(f"共提取到 {len(links)} 个参考链接")

            # 保存到 CSV
            result_df = pd.DataFrame([{
                'query': query,
                'content': content,
                'links': str(links)  # 转为字符串存储
            }])

            result_df.to_csv(
                'query_results.csv',
                mode='a',
                index=False,
                encoding='utf-8',
                header=not os.path.exists('query_results.csv')
            )
            print(f"结果已保存到 query_results.csv")

        except Exception as e:
            print(f"处理查询 {index + 1} 时出错: {e}")
            import traceback
            traceback.print_exc()

    print("\n所有查询处理完毕，结果已保存至 query_results.csv")

# -----------------------------
# 入口
# -----------------------------
if __name__ == "__main__":
    current = gw.getActiveWindow()
    if current:
        current.minimize()
    time.sleep(2)
    main()