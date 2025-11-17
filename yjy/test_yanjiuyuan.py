import os
import os
import time

from PIL import Image, ImageDraw, ImageFont

from yanjiuyuancall import *
get_task_config()
reception_click_frist_message = "用户原始命令为：认真观察'在线咨询'的列表是否存在用户消息，点击第一个用户消息。参考操作步骤为:\n如果列表里面有用户消息，只需要点击第一个用户，在finished action里面content为'已经点击'。\n\n如果'在线咨询'的列表为空，不存在用户消息，不要做任何操作，在finished action里面content为'无历史消息'"

# 遍历 指定目录 的所有图片
for filename in os.listdir("grounding"):

    image_path = os.path.join("grounding", filename)


    response_result = call_planner(reception_click_frist_message, generate_random_string(), requests=None,
                               image_path=image_path)
    time.sleep(1)
    # 解析返回结果中的boxArgs和actionType的值
    if response_result and 'result' in response_result and 'answer' in response_result['result']:
        answer = response_result['result']['answer']
        # 提取actionType
        action_type = answer.get('actionType', '未找到actionType')
        # 提取boxArgs
        box_args = answer.get('boxArgs', '未找到boxArgs')

        # 打印输出
        print(f"actionType的值为: {action_type}")
        print(f"boxArgs的值为: {box_args}")

        # 检查box_args是否有值
        if box_args and box_args != '未找到boxArgs' and len(box_args)> 0:
            try:
                # 定义原始图片路径和保存目录
                original_image_path = image_path
                save_directory = "annotated"

                # 创建保存目录（如果不存在）
                os.makedirs(save_directory, exist_ok=True)

                # 读取原始图片
                image = Image.open(original_image_path)
                draw = ImageDraw.Draw(image)

                # 尝试获取字体，如果失败则使用默认字体
                try:
                    font = ImageFont.truetype("simhei.ttf", 16)  # 使用黑体字体，大小为16
                except:
                    font = None  # 使用默认字体

                # 处理坐标点
                if isinstance(box_args, list) and len(box_args) >= 2:
                    try:
                        # 尝试将坐标转换为整数
                        x, y = int(box_args[0]), int(box_args[1])

                        # 在图片上标注坐标点（绘制一个红色的圆）
                        radius = 5
                        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill='red', outline='red')

                        # 在坐标点旁边添加文本标注
                        label = f"position: ({x}, {y})"
                        text_position = (x + 10, y - 20)
                        draw.text(text_position, label, fill='red', font=font)

                        # 生成保存文件名
                        original_filename = os.path.basename(original_image_path)
                        annotated_filename = f"annotated_{original_filename}"
                        save_path = os.path.join(save_directory, annotated_filename)

                        # 保存标注后的图片
                        image.save(save_path)
                        print(f"已将标注后的图片保存到: {save_path}")
                    except ValueError:
                        print(f"无法将boxArgs转换为整数坐标: {box_args}")
                else:
                    print(f"boxArgs格式不符合预期: {box_args}")
            except Exception as e:
                print(f"标注图片时出错: {str(e)}")


    break