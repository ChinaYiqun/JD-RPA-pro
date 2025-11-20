import os
import sys

import sys
import io
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from service.mgdb_client import MongoDBClient
from configs.llm_config import *
from openai import OpenAI
import base64
import io
from PIL import Image
import random
import copy
import json
from io import BytesIO
import re



REFERENCE_RESOLUTIONS = [
    (1920, 1080), (1920, 1200), (1920, 1440), (1856, 1392), (1792, 1344), (1680, 1050)
]


def prompt_variants(original_json, n = 5):
    """
    输入一个对话 JSON（list of dict），输出 n 个变体，仅改写 user message 中的文本指令部分。
    """
    # 1. 深拷贝
    import copy
    base_sample = copy.deepcopy(original_json)

    # 2. 提取 user 消息中的 instruct 文本
    user_msg = None
    text_block_idx = -1
    for msg in base_sample:
        if msg["role"] == "user":
            for i, block in enumerate(msg["content"]):
                if block["type"] == "text":
                    original_instruct = block["text"]
                    user_msg = msg
                    text_block_idx = i
                    break
            if user_msg is not None:
                break

    # 3. 调用 LLM 生成 n 个改写版本
    instruction = f"""给定原始的计算机代理指令："{original_instruct}"
生成 {n} 个多样但语义等效的改写。
- 保持动作（例如，点击、输入、滚动）和目标（例如，按钮名称、位置）。
- 变换措辞、词序、语态（主动/被动）、同义词。
- 不要改变意义，也不要增删步骤。

输出格式：仅 JSON 字符串列表。
示例： ["点击右下角的 '提交' 按钮。", ...]
"""
    # 调用 LLM
    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
    )
    messages = [
                {"role": "system", "content": [{"type": "text", "text": "你是一位擅长对提示词进行改写的助手。"}]},
                {"role": "user", "content": instruction}
            ]
    chat_completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.0,
        stream=False,
        tool_choice="none",
    )
    variants = chat_completion.choices[0].message.content    
    variants = json.loads(variants)  
    print("原始模型输出:\n", variants)
    if len(variants) < n:
        # 若生成不足 n 条，用原始指令补足
        variants += [original_instruct] * (n - len(variants))

    # 4. 构造输出：对每个 variant，替换 instruct
    output_list = []
    for var_text in variants[:n]:
        new_sample = copy.deepcopy(base_sample)
        # 找到 user 的 content 中 text block 并替换
        for msg in new_sample:
            if msg["role"] == "user":
                for block in msg["content"]:
                    if block["type"] == "text":
                        block["text"] = var_text
                        break
                break
        output_list.append(new_sample)
    return output_list


def parse_tool_call(content):
    pattern = r'<tool_call>(.*?)</tool_call>'
    tool_call_matches = re.findall(pattern, content, re.DOTALL)
    for tool_call in tool_call_matches:
        tool_call = tool_call.strip()
        tool_call = json.loads(tool_call)
    return tool_call

def pic_variants(original_json, n=5):
    outputs = []
    
    # 为每个目标分辨率生成一个新对话
    for idx in range(n):
        target_w, target_h = REFERENCE_RESOLUTIONS[idx % len(REFERENCE_RESOLUTIONS)]
        new_dialog = copy.deepcopy(original_json)
        
        # 当前有效的缩放比例（初始为 1.0，无图时不变坐标）
        scale_x, scale_y = 1.0, 1.0

        # 逐条处理消息
        for msg in new_dialog:
            if msg["role"] == "user":
                # 查找该 user 消息中的 image_url
                for block in msg["content"]:
                    if block["type"] == "image_url":
                        url = block["image_url"]["url"]
                        origin_size = block.get("origin_size", [1920, 1080])
                        orig_w, orig_h = origin_size
                        # 独立处理这张图 
                        # 1. 解码
                        b64_data = url.split(",", 1)[1]
                        img_bytes = base64.b64decode(b64_data)
                        img = Image.open(BytesIO(img_bytes)).convert("RGB")
                        
                        # 2. resize 到目标分辨率（拉伸）
                        resized = img.resize((target_w, target_h))
                        
                        # 3. 重编码
                        buffer = BytesIO()
                        fmt = url.split(";")[0].split("/")[1] if "/;" in url else "png"
                        if fmt.lower() in ("jpg", "jpeg"):
                            resized.save(buffer, format="JPEG", quality=95)
                        else:
                            resized.save(buffer, format="PNG")
                        b64_new = base64.b64encode(buffer.getvalue()).decode()
                        new_url = f"image/{fmt};base64,{b64_new}"
                        
                        # 4. 更新 URL
                        block["image_url"]["url"] = new_url
                        

        outputs.append(new_dialog)
    
    return outputs


def position_variants(original_json, n=2, pixel=2):
    """
    对对话中所有点击坐标做随机偏移增强。
    
    Args:
        original_json: 原始JSON
        n: 生成变体数量（默认 2）
        pixel: 最大偏移量（±pixel），默认 5 像素
    
    Returns:
        List[JSON]: 长度为 n 的增强样本列表
    """
    
    outputs = []
    for _ in range(n):
        new_json = copy.deepcopy(original_json)
        
        for msg in new_json:
            if msg["role"] == "assistant" and isinstance(msg["content"], str):
                tool_call = parse_tool_call(msg["content"])
                if tool_call and "arguments" in tool_call:
                    args = tool_call["arguments"]
                    action = args.get("action")
                    # 仅处理点击类动作
                    if action in ["left_click", "right_click", "double_click", "click"]:
                        coord = args.get("coordinate")
                        if isinstance(coord, list) and len(coord) == 2:
                            x, y = coord
                            # 随机偏移：[-pixel, +pixel]
                            dx = random.randint(-pixel, pixel)
                            dy = random.randint(-pixel, pixel)
                            new_x = x + dx
                            new_y = y + dy
                            args["coordinate"] = [new_x, new_y]
                            # 重新放入
                            tool_str = json.dumps(tool_call, ensure_ascii=False, indent=4)
                            msg["content"] = f"<tool_call>\n{tool_str}\n<tool_call>"
        
        outputs.append(new_json)
    
    return outputs


if __name__ == "__main__":

    # 强制 stdout 使用 UTF-8 编码（适用于重定向/管道场景）
    # 为了能python -m my_tools.augment > position_variants.txt
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    #name = "default_task_"
    client = MongoDBClient()
    #history_sample = client.get_history(name)

    # 返回的每个json保存到当前 save 目录下
    save_dir = r"D:\pycharmProject\dataset\save\save" #os.path.join(os.path.dirname(__file__), "save")
    os.makedirs(save_dir, exist_ok=True)


    query_history_by_prefix = client.query_history_by_prefix("yq_")
    print(f"query_history_by_prefix:{query_history_by_prefix}")

    from tqdm import tqdm
    for history_id, history_data in tqdm(query_history_by_prefix.items(), desc="Processing histories"):

        print(f"History ID: {history_id}")
        with open(os.path.join(save_dir, f"{history_id}.json"), "w", encoding="utf-8") as f:
            json.dump(history_data, f, ensure_ascii=False, indent=4)
        print("\n" + "="*50 + "\n")
        prompt_variants_json = prompt_variants(history_data, n=1)

        for i, prompt_variant in enumerate(prompt_variants_json):
            with open(os.path.join(save_dir, f"{history_id}_prompt_variants{i}.json"), "w", encoding="utf-8") as f:
                json.dump(prompt_variant, f, ensure_ascii=False, indent=4)

            pic_variants_json = pic_variants(history_data, n=2)
            for j, pic_variant in enumerate(pic_variants_json):
                with open(os.path.join(save_dir, f"{history_id}_pic_variants{i}_{j}.json"), "w", encoding="utf-8") as f:
                    json.dump(pic_variant, f, ensure_ascii=False, indent=4)

                position_variants_json = position_variants(pic_variant, n=2, pixel=2)
                for k, variant in enumerate(position_variants_json):
                    with open(os.path.join(save_dir, f"{history_id}_position_variants{i}_{j}_{k}.json"), "w", encoding="utf-8") as f:
                        json.dump(variant, f, ensure_ascii=False, indent=4)

