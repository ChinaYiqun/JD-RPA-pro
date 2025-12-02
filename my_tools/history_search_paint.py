import os
import sys
import re
import json
import base64
from io import BytesIO
from PIL import Image, ImageDraw


# --------- 新增：用于从assistant消息中提取坐标 ---------
def extract_coordinate_from_assistant(content):
    """从assistant的content中提取相对坐标"""
    if not content:
        return None

    # 使用正则表达式查找tool_call中的JSON部分
    match = re.search(r'<tool_call>\s*({.*?})\s*</tool_call>', content, re.DOTALL)
    if not match:
        return None

    try:
        tool_call_json = json.loads(match.group(1))
        arguments = tool_call_json.get('arguments', {})
        coordinate = arguments.get('coordinate')
        # 确保坐标是列表且包含两个数值
        if isinstance(coordinate, list) and len(coordinate) == 2:
            return coordinate
        return None
    except json.JSONDecodeError:
        print(f"解析assistant消息中的JSON失败: {content}")
        return None


# --------- 修改：在图片上绘制坐标点（支持相对坐标） ---------
def draw_coordinate_on_image(base64_image_str, relative_coordinate):
    """
    在base64编码的图片上绘制坐标点，并返回新的base64字符串。
    坐标为相对坐标 (相对于1000x1000的画布)。
    """
    if not relative_coordinate or len(relative_coordinate) != 2:
        return base64_image_str  # 如果坐标无效，返回原图

    try:
        # 1. 解码图片并获取其原始尺寸
        if "base64," in base64_image_str:
            header, encoded = base64_image_str.split("base64,", 1)
        else:
            encoded = base64_image_str

        image_data = base64.b64decode(encoded)
        image = Image.open(BytesIO(image_data))
        img_width, img_height = image.size

        # 2. 将相对坐标转换为绝对坐标
        # 假设相对坐标是基于一个1000x1000的参考系
        rel_x, rel_y = relative_coordinate
        abs_x = (rel_x / 1000.0) * img_width
        abs_y = (rel_y / 1000.0) * img_height

        # 转换为整数坐标
        abs_x_int, abs_y_int = int(round(abs_x)), int(round(abs_y))

        # 3. 在图片上绘制标记
        draw = ImageDraw.Draw(image)
        radius = 15  # 圆点半径，可以根据图片大小调整
        draw.ellipse(
            (abs_x_int - radius, abs_y_int - radius, abs_x_int + radius, abs_y_int + radius),
            fill='red',
            outline='white',
            width=3
        )

        # 4. 将修改后的图片重新编码为base64
        buffered = BytesIO()
        image_format = image.format if image.format else 'PNG'
        image.save(buffered, format=image_format)
        img_byte = buffered.getvalue()
        img_base64 = base64.b64encode(img_byte)

        return f"data:image/{image_format.lower()};base64,{img_base64.decode('utf-8')}"

    except Exception as e:
        print(f"在图片上绘制坐标失败: {e}")
        return base64_image_str  # 绘制失败时，返回原图


# --------- 修改：格式化历史记录用于显示 ---------
def format_history_for_display(history):
    """格式化历史记录以便在Gradio中显示，包括在图片上绘制坐标"""
    display_html = ""

    for i, record in enumerate(history, 1):
        display_html += f"<div style='margin: 20px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px;'>"
        display_html += f"<h3>记录 {i}: {record.get('role', 'unknown')}</h3>"

        content = record.get("content", "")

        # 如果当前记录是assistant，且上一条是user，尝试提取坐标并绘制
        if record.get('role') == 'assistant' and i > 1:
            prev_record = history[i - 2]  # 因为enumerate从1开始，所以i-2是上一条记录的索引
            if prev_record.get('role') == 'user':
                relative_coordinate = extract_coordinate_from_assistant(content)
                if relative_coordinate:
                    # 遍历上一条user记录的content，寻找图片
                    for item in prev_record.get('content', []):
                        if isinstance(item, dict) and item.get('type') == 'image_url':
                            original_image_url = item['image_url']['url']
                            # 绘制坐标并获取新图片的base64
                            new_image_url = draw_coordinate_on_image(original_image_url, relative_coordinate)
                            # 在HTML中，显示带坐标的图片
                            display_html += f"<p><strong>操作位置 (相对坐标: {relative_coordinate}):</strong></p>"
                            display_html += f"<img src='{new_image_url}' style='max-width: 700px; margin: 10px 0; border: 3px solid red;'/>"

        # 正常显示当前记录的文本内容
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and "type" in item:
                    if item["type"] == "text" and "text" in item:
                        display_html += f"<p>{item['text']}</p>"
                    # 对于user消息中的图片，我们只在assistant消息中显示带标记的版本，这里不再重复显示
        else:
            # 对于assistant的content（通常是tool_call字符串），进行格式化显示
            if record.get('role') == 'assistant':
                display_html += f"<pre style='background-color: #f0f0f0; padding: 10px; border-radius: 5px; font-size: 0.9em;'>{content}</pre>"
            else:
                display_html += f"<p>{str(content)}</p>"

        display_html += "</div>"

    return display_html


# (以下代码与原版基本相同，此处为完整性再次列出)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
import gradio as gr
# 假设你的MongoDB客户端配置正确
from service.mgdb_client import MongoDBClient


def decode_base64_image(base64_str):
    """将base64编码的图片字符串转换为PIL Image对象（此函数在本脚本中未直接使用，但保留以防万一）"""
    if not base64_str:
        return None
    if "base64," in base64_str:
        base64_str = base64_str.split("base64,")[1]
    try:
        image_data = base64.b64decode(base64_str)
        return Image.open(BytesIO(image_data))
    except Exception as e:
        print(f"解码图片失败: {e}")
        return None


def search_history(tid):
    """根据tid搜索历史记录"""
    if not tid:
        return "请输入有效的TID"
    try:
        # 确保MongoDBClient能正确连接并获取数据
        mgdb_client = MongoDBClient()
        history = mgdb_client.get_history(tid)
        if not history:
            return f"未找到TID为 '{tid}' 的历史记录"
        return format_history_for_display(history)
    except Exception as e:
        return f"获取历史记录失败: {str(e)}"


# 创建Gradio界面
with gr.Blocks(title="任务历史记录查看器") as demo:
    gr.Markdown("# 任务历史记录查看器")
    with gr.Row():
        tid_input = gr.Textbox(label="TID", placeholder="请输入任务ID")
        search_btn = gr.Button("搜索")
    result_output = gr.HTML(label="历史记录")
    search_btn.click(
        fn=search_history,
        inputs=[tid_input],
        outputs=[result_output]
    )

if __name__ == "__main__":

    demo.launch(share=False, debug=True, server_name="0.0.0.0")
