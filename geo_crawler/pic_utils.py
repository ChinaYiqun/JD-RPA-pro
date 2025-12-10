import base64
import cv2
import numpy as np
from PIL import Image, ImageDraw

def decode_base64_image(base64_str: str) -> bool:
    """验证base64编码的图片是否有效"""
    try:
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
        base64.b64decode(base64_str, validate=True)
        return True
    except (base64.binascii.Error, ValueError):
        return False


def image_to_base64(image_path):
    """将图片文件转换为base64编码字符串"""
    try:
        with open(image_path, "rb") as image_file:
            base64_str = base64.b64encode(image_file.read()).decode('utf-8')
            base64_str = f"data:image/jpeg;base64,{base64_str}"
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]
            return base64_str
    except Exception as e:
        print(f"转换图片为base64时出错: {str(e)}")
        return None


def base64_to_img(base64_str, output_path):
    """将base64编码字符串转换为图片文件"""
    try:
        # 移除可能存在的data URI前缀（如"data:image/jpeg;base64,"）
        if base64_str.startswith('data:image/'):
            base64_data = base64_str.split(',')[1]
        else:
            base64_data = base64_str

        # 解码base64数据并写入文件
        img_data = base64.b64decode(base64_data)
        with open(output_path, 'wb') as img_file:
            img_file.write(img_data)
        return True  # 转换成功返回True
    except Exception as e:
        print(f"转换base64为图片时出错: {str(e)}")
        return False  # 转换失败返回False


def find_all_matches(image_path, template_paths, threshold=0.65, show=False, iou_threshold=0.3):
    """
    在图像中查找所有与模板列表中任一模板相似的区域，并使用NMS去除重叠矩形框

    参数:
    image_path: 原始图像路径
    template_paths: 模板图像路径列表（支持多个模板）
    threshold: 匹配阈值，值越高匹配要求越严格
    iou_threshold: NMS交并比阈值，值越低去重越严格（0-1之间）

    返回:
    所有匹配区域的坐标列表 (x, y, width, height)
    """
    # 读取原始图像
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法读取图像文件: {image_path}")

    # 转换为灰度图（仅需执行一次）
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 验证模板路径是否为列表
    if not isinstance(template_paths, list):
        raise TypeError("template_paths 必须是模板图像路径的列表")

    # 存储所有模板的初始匹配结果 (x, y, w, h, score)
    initial_matches = []

    # 循环处理每个模板
    for template_path in template_paths:
        # 读取模板图像
        template = cv2.imread(template_path)
        if template is None:
            raise ValueError(f"无法读取模板文件: {template_path}")

        # 获取当前模板的高度和宽度
        h, w = template.shape[:2]

        # 转换模板为灰度图
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        # 进行模板匹配
        result = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)

        # 找出所有匹配值大于阈值的位置
        locations = np.where(result >= threshold)

        # 收集当前模板的匹配区域 (x, y, width, height, score)
        for pt in zip(*locations[::-1]):
            x, y = pt
            score = result[y, x]  # 获取当前匹配点的分数
            initial_matches.append((x, y, w, h, score))

    # 非极大值抑制(NMS)函数，去除重叠矩形框
    def nms(boxes, iou_threshold):
        if len(boxes) == 0:
            return []

        # 将坐标转换为左上角和右下角 (x1, y1, x2, y2)
        x1 = np.array([box[0] for box in boxes])
        y1 = np.array([box[1] for box in boxes])
        x2 = np.array([box[0] + box[2] for box in boxes])
        y2 = np.array([box[1] + box[3] for box in boxes])

        # 计算每个框的面积
        areas = (x2 - x1 + 1) * (y2 - y1 + 1)

        # 使用预先保存的分数进行排序
        scores = np.array([box[4] for box in boxes])
        order = scores.argsort()[::-1]  # 降序排列的索引

        keep = []
        while order.size > 0:
            # 选择当前置信度最高的框
            i = order[0]
            keep.append(i)

            # 计算与其他框的交并比
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            # 计算交叠区域的宽和高
            w_inter = np.maximum(0, xx2 - xx1 + 1)
            h_inter = np.maximum(0, yy2 - yy1 + 1)

            # 计算交叠面积和IOU
            inter_area = w_inter * h_inter
            iou = inter_area / (areas[i] + areas[order[1:]] - inter_area)

            # 保留IOU小于阈值的框
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]  # +1是因为inds是从order[1:]开始计算的

        # 返回保留的框，只包含坐标和尺寸信息
        return [(boxes[i][0], boxes[i][1], boxes[i][2], boxes[i][3]) for i in keep]

    # 应用NMS过滤重叠框（处理所有模板的合并结果）
    if initial_matches:
        matches = nms(initial_matches, iou_threshold)
    else:
        matches = []

    if show:
        # 在图像上绘制NMS处理后的匹配区域
        for (x, y, w, h) in matches:
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # 显示结果图像
        cv2.imshow('Matches', img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return matches




def mark_coordinate_on_image(coordinate, image_path, output_path=None):
    """
    在图片上标记指定坐标

    参数:
        coordinate: 元组 (x, y) 表示要标记的坐标
        image_path: 输入图片路径
        output_path: 输出图片路径，如果为None则覆盖原图
    """
    # 打开图片
    img = Image.open(image_path).convert('RGB')
    draw = ImageDraw.Draw(img)

    x, y = coordinate

    # 绘制标记 (红色十字)
    draw.line((x - 10, y, x + 10, y), fill="red", width=2)  # 水平线
    draw.line((x, y - 10, x, y + 10), fill="red", width=2)  # 垂直线

    # 保存图片
    if output_path is None:
        output_path = image_path
    img.save(output_path)
if __name__ == '__main__':

     find_all_matches(f"resource/left_1.png", [ "resource/new_message_button_1.png"],show=True)

