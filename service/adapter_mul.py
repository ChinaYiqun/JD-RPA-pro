from configs.llm_config import *
from configs.prompt import *

from openai import OpenAI
import base64
from PIL import Image
import re
import json

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        image = base64.b64encode(image_file.read()).decode('utf-8')
    return image

def construct_system_prompt(instruct: str, image_path: str, history: list = None) -> list:
    """构造包含历史上下文的消息列表"""
    base64_image = encode_image(image_path)
    image_format = image_path.split('.')[-1]
    image_url = {
        "type": "image_url",
        "image_url": {"url": f"data:image/{image_format};base64,{base64_image}"}
    }
    
    # 初始化历史记录
    history = history if history is not None else []

    
    if "qwen" in model.lower():
        user_text = {"type": "text", "text": instruct}
        new_content = [image_url, user_text]
        if not history:
            return [
                {"role": "system", "content": [{"type": "text", "text": qwen_system_prompt}]},
                {"role": "user", "content": new_content}
            ]
        return history + [{"role": "user", "content": new_content}]
    

    
    # 默认消息格式
    return history + [{"role": "user", "content": [image_url, {"type": "text", "text": instruct}]}]

def parser_action(content: str, image_path: str) -> tuple:
    """解析模型输出的动作和参数"""
    image = Image.open(image_path)
    width, height = image.width, image.height


    if "qwen" in model.lower() :
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
                action = data['arguments'].get('action')
                if not action:
                    continue

                if action in ['left_click', 'right_click', 'mouse_move']:
                    coordinate = data['arguments'].get('coordinate')
                    if isinstance(coordinate, list) and len(coordinate) == 2:
                        x, y = coordinate
                        x_abs = int(x / 1000 * width)
                        y_abs = int(y / 1000 * height)
                        action_list.append(action)
                        param_list.append((x_abs, y_abs))
                elif action == 'type':
                    text = data['arguments'].get('text')
                    if text is not None:
                        action_list.append(action)
                        param_list.append(text)
                elif action == 'key':
                    keys = data['arguments'].get('keys')
                    if keys is not None:
                        action_list.append(action)
                        param_list.append(keys[0])
                elif action == 'scroll':
                    pixels= data['arguments'].get('pixels')
                    if pixels is not None:
                        action_list.append(action)
                        param_list.append(pixels)
                elif action == "wait":
                    seconds = data["arguments"].get("time")
                    if seconds is not None:
                        action_list.append(action)
                        param_list.append(seconds)
                elif action == "terminate":
                    status = data["arguments"].get("status")
                    action_list.append(action)
                    param_list.append(status or "success")
                elif action == "answer":
                    text = data["arguments"].get("text")
                    if text is not None:
                        action_list.append(action)
                        param_list.append(text)

            except (json.JSONDecodeError, KeyError) as e:
                print(f"解析错误: {e}, 内容: {json_str}")

        return action_list, param_list


def get_cua_response(instruct: str, image_path: str, history: list = None) -> tuple:


    """获取模型响应并维护历史上下文"""
    print("😑 输入:\n", instruct, image_path)

    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
    )

    # 构造包含历史的消息
    messages = construct_system_prompt(instruct, image_path, history)

    print("😊 调用的模型:\n", base_url, model)
    chat_completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.0,
        stream=False,
        tool_choice="none",
    )
    # 输出全部响应内容
    print("😆 模型响应:\n", chat_completion)

    output_text = chat_completion.choices[0].message.content      
    print("😆 原始模型输出:\n", output_text)

    # 解析动作和参数
    action, param_list = parser_action(output_text, image_path)
    print("😂 action 解析&坐标转换结果:\n", action, param_list)

    # 更新历史上下文（添加当前轮次的模型响应）
    updated_history = messages + [{"role": "assistant", "content": output_text}]
    return action, param_list, updated_history

if __name__ == "__main__":
    pass

