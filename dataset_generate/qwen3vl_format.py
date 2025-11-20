import base64
import json
import os
from pathlib import Path


def find_json_files(directory: str) -> list:
    """
    遍历指定目录（含子目录）下所有 .json 文件，返回绝对路径列表
    :param directory: 目标目录路径（相对/绝对路径均可）
    :return: 所有 .json 文件的绝对路径列表
    """
    json_files = []
    root_dir = Path(directory).resolve()
    for json_path in root_dir.rglob("*.json"):
        if json_path.is_file():
            json_files.append(str(json_path))
    return json_files


# ------------------- 使用示例 -------------------
if __name__ == "__main__":
    save_dir = r"D:\pycharmProject\dataset\save\save"  # 原始JSON目录
    json_list = find_json_files(save_dir)

    if json_list:
        print(f"共找到 {len(json_list)} 个 JSON 文件：")
        for file in json_list:
            print(file)
    else:
        print(f"在目录 {save_dir} 中未找到 JSON 文件")
        # 如果没有找到文件，直接退出
        exit()

    # --- 配置参数 ---
    output_dir = r"D:\pycharmProject\dataset\save\qwen3vl_format"  # 输出目标JSON目录
    image_dir = os.path.join(output_dir, "images")  # 图片保存目录
    output_json_name = "formatted_data.json"  # 输出目标JSON文件名
    output_json_path = os.path.join(output_dir, output_json_name)

    # --- 初始化操作 ---
    os.makedirs(image_dir, exist_ok=True)  # 创建图片目录（不存在则创建）

    # 检查目标JSON文件是否存在，如果存在则读取已有数据，否则初始化一个空列表
    existing_data = []
    if os.path.exists(output_json_path):
        try:
            with open(output_json_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                # 确保读取的数据是一个列表
                if not isinstance(existing_data, list):
                    print(f"警告：{output_json_path} 内容格式不正确，将被覆盖。")
                    existing_data = []
        except json.JSONDecodeError:
            print(f"警告：{output_json_path} 已损坏或为空，将被覆盖。")
            existing_data = []

    # --- 遍历处理每个原始JSON文件 ---
    from tqdm import tqdm
    for json_file_path in tqdm(json_list, desc="Processing JSON files"):
        # 从文件路径中获取文件名（不含后缀）
        name = os.path.basename(json_file_path).split(".")[0]
        print(f"\n--- 开始处理文件: {name}.json ---")

        # 读取原始JSON文件
        try:
            # 使用 json_file_path 直接打开，更可靠
            with open(json_file_path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
            print("原始JSON文件读取成功")
        except FileNotFoundError:
            print(f"错误：未找到原始文件 {json_file_path}")
            continue  # 跳过当前文件，继续处理下一个
        except json.JSONDecodeError:
            print(f"错误：原始文件 {json_file_path} 不是有效JSON格式")
            continue  # 跳过当前文件，继续处理下一个

        # 初始化单个样本的数据结构
        formatted_sample = {
            "image": [],  # 存储提取的图片文件名
            "conversations": []  # 存储转换后的对话
        }
        image_cache = {}  # 缓存图片base64，避免重复保存

        # --- 核心转换逻辑 ---
        for turn_idx, turn in enumerate(loaded_data, 1):
            role = turn.get("role")
            content = turn.get("content")

            if not role or content is None:
                print(f"跳过第{turn_idx}轮：无角色或无内容")
                continue

            new_role = "gpt" if role == "assistant" else "human"

            content_blocks = []
            if isinstance(content, list):
                content_blocks = content
            elif isinstance(content, str):
                content_blocks = [{"type": "text", "text": content}]
            else:
                print(f"跳过第{turn_idx}轮：content类型异常（{type(content)}）")
                continue

            current_turn_text = ""
            for block in content_blocks:
                if not isinstance(block, dict):
                    print(f"跳过第{turn_idx}轮无效block：{block}")
                    continue

                block_type = block.get("type")
                if block_type == "text":
                    text = block.get("text", "").strip()
                    if text:
                        current_turn_text += text + "\n"

                elif block_type == "image_url":
                    image_url = block.get("image_url", {}).get("url", "").strip()
                    if not image_url or image_url in ["“", "\"", "'"]:
                        print(f"第{turn_idx}轮图片URL无效：{image_url}")
                        continue

                    b64_key = image_url.split(",", 1)[1] if "," in image_url else image_url
                    if len(b64_key) < 100 or not all(
                            c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=" for c in b64_key):
                        print(f"第{turn_idx}轮base64无效，跳过该图片")
                        continue

                    if b64_key not in image_cache:
                        try:
                            img_data = base64.b64decode(b64_key)
                            # 使用原始文件名前缀确保图片唯一性
                            img_filename = f"{name}_image_{len(image_cache)}.png"
                            img_save_path = os.path.join(image_dir, img_filename)

                            with open(img_save_path, "wb") as img_f:
                                img_f.write(img_data)

                            image_cache[b64_key] = img_filename
                            formatted_sample["image"].append(f"images/{img_filename}")
                            print(f"第{turn_idx}轮图片保存成功：{img_save_path}")
                        except Exception as e:
                            print(f"第{turn_idx}轮图片保存失败：{str(e)[:50]}")
                            continue

                    current_turn_text += "<image>\n"

            current_turn_text = current_turn_text.strip()
            if current_turn_text:
                formatted_sample["conversations"].append({
                    "from": new_role,
                    "value": current_turn_text
                })
                print(f"第{turn_idx}轮转换完成：{new_role} - {current_turn_text[:30]}...")

        # --- 将转换好的样本追加到目标JSON文件 ---
        if formatted_sample["conversations"]:  # 确保样本有有效对话内容
            existing_data.append(formatted_sample)

            try:
                with open(output_json_path, "w", encoding="utf-8") as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=2)
                print(f"成功：样本已追加到 {output_json_path}")
            except Exception as e:
                print(f"错误：无法将样本写入文件 {output_json_path}。错误信息: {e}")
        else:
            print(f"警告：文件 {name}.json 转换后无有效对话，已跳过。")

    print("\n所有文件处理完毕！")

    # ------------------- 新增：处理特定样本 -------------------
    print("开始处理特定样本...")
    modified_output_json_name = "formatted_data_modified.json"
    modified_output_json_path = os.path.join(output_dir, modified_output_json_name)

    # 读取已生成的JSON文件
    try:
        with open(output_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"读取 {output_json_path} 失败：{e}")
        exit()

    # 遍历每个样本进行处理
    for sample in data:
        images = sample.get("image", [])
        # 检查是否有包含特定关键词的图片
        if any("check_new_message_in_online_consultation" in img for img in images):
            print(f"处理包含目标图片的样本：{images}")

            # 只保留第一张图片
            if images:
                sample["image"] = [images[0]]
                print(f"已保留第一张图片：{sample['image'][0]}")

            # 处理对话：删除倒数第3和倒数第2条
            conversations = sample.get("conversations", [])
            if len(conversations) >= 4:  # 确保有足够对话可删除
                original_len = len(conversations)
                sample["conversations"] = conversations[:-3] + conversations[-1:]
                print(f"已删除倒数第3和第2条对话，对话数量从 {original_len} 减少到 {len(sample['conversations'])}")

    # 保存修改后的数据
    try:
        with open(modified_output_json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已成功保存修改后的数据到 {modified_output_json_path}")
    except Exception as e:
        print(f"保存修改后的数据失败：{e}")

