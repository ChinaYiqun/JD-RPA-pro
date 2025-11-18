import os
import shutil
import sys



current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
import gradio as gr
import base64
from io import BytesIO
from PIL import Image
from service.mgdb_client import MongoDBClient


def decode_base64_image(base64_str):
    """将base64编码的图片字符串转换为PIL Image对象"""
    if not base64_str:
        return None

    # 移除可能的前缀（如"data:image/png;base64,"）
    if "base64," in base64_str:
        base64_str = base64_str.split("base64,")[1]

    try:
        image_data = base64.b64decode(base64_str)
        return Image.open(BytesIO(image_data))
    except Exception as e:
        print(f"解码图片失败: {e}")
        return None


def format_history_for_display(history):
    """格式化历史记录以便在Gradio中显示"""
    display_html = ""

    for i, record in enumerate(history, 1):
        display_html += f"<div style='margin: 20px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px;'>"
        display_html += f"<h3>记录 {i}</h3>"

        if "role" in record:
            display_html += f"<p><strong>{record['role']}</strong></p>"

        if "content" in record:
            content = record["content"]
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and "type" in item:
                        if item["type"] == "text" and "text" in item:
                            display_html += f"<p>{item['text']}</p>"
                        elif item["type"] == "image_url" and "image_url" in item:
                            image_url = item["image_url"]["url"]
                            # 直接使用base64字符串在HTML中显示图片
                            display_html += f"<img src='{image_url}' style='max-width: 500px; margin: 10px 0;'/>"
            else:
                display_html += f"<p>{str(content)}</p>"

        display_html += "</div>"

    return display_html


def search_history(tid):
    """根据tid搜索历史记录"""
    if not tid:
        return "请输入有效的TID"

    try:
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
    demo.launch(share=False)