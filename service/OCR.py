#!/usr/bin/python
# -*- coding: UTF-8 -*-
import datetime
import os
import re
import os
import shutil
import sys
import tempfile


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from paddleocr import PaddleOCR

from service.plan import PlanActionRequest, PlanActionResponse, ResultData, Answer, ActionInputs
from my_tools.pic_utils import get_image_size_from_base64, base64_to_img


class PaddleOCRSingleton:
    # 单例模式核心：类变量存储唯一实例
    _instance = None
    result = None

    def __new__(cls, *args, **kwargs):
        """确保只创建一个类实例"""
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化OCR模型（仅首次实例化时执行）"""
        # 防止重复初始化（单例模式下__init__可能被多次调用）
        if not hasattr(self, "ocr"):
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang="ch",  # 支持中文+英文
                use_gpu=False , # 关闭GPU
                show_log = False,
                ir_optim = False
            )

    def recognize(self, img_path: str):
        """
        识别图片中的文本
        :param img_path: 图片路径
        :return: OCR识别结果
        """
        if not img_path:
            raise ValueError("图片路径不能为空")

        # 执行OCR识别（启用方向分类）
        result = self.ocr.ocr(img_path, cls=True)
        self.result = result
        return result

    def get_text(self):
        """
        从OCR结果中提取所有文本
        :return: 包含所有识别文本的字符串
        """
        text_list = []
        ocr_result_str = ""
        for line in self.result:
            for word_info in line:
                bbox, (text, score) = word_info
                if text is None:
                    continue
                ocr_result_str += text + "\n"
        return ocr_result_str



    def get_text_position_center_list(self, target_text,match_type='contains'):
        position_list = []
        result = self.result
        for line in result:
            for word_info in line:
                bbox, (text, score) = word_info
                if text is None:
                    continue  # 跳过空文本
                # 根据匹配方式判断是否符合条件
                is_match = False
                if match_type == 'contains':
                    # 包含匹配：文本中存在目标子串（re.findall 非空）
                    if re.findall(target_text, text):
                        is_match = True
                elif match_type == 'equals':
                    # 精确匹配：文本与目标子串完全一致
                    if text == target_text:
                        is_match = True
                else:
                    raise ValueError(f"不支持的匹配方式：{match_type}，可选值为 'contains' 或 'exact'")

                if is_match:
                    # 计算文本框中心坐标（使用对角顶点求平均）
                    x = (bbox[0][0] + bbox[2][0]) / 2  # 左上角(x1,y1)和右下角(x3,y3)的x平均
                    y = (bbox[0][1] + bbox[2][1]) / 2  # 左上角和右下角的y平均
                    position_list.append((int(x), int(y)))

        position_list.sort(key=lambda x: (x[1], x[0]))
        return position_list

def is_ocr_task(request: PlanActionRequest) -> bool:
    print(request.task)
    """判断是否为OCR任务"""
    return request.task and "ocr" in request.task.lower()


def process_ocr_request(request: PlanActionRequest) -> PlanActionResponse:
    if not request.image:
        return PlanActionResponse(status=1, httpCode=400, message="Missing image")

    # 不指定扩展名，让 OCR 库根据文件内容识别
    tmp_fd, tmp_path = tempfile.mkstemp()  # 无扩展名
    
    try:
        base64_to_img(request.image, tmp_path)
        
        ocr = PaddleOCRSingleton()
        ocr.recognize(tmp_path)
        ocr_result_str = ocr.get_text()
        print("res:", ocr_result_str)
        
        return PlanActionResponse(
            status=0,
            httpCode=200,
            message="OK",
            result=ResultData(
                status="FINISH",
                answer=Answer(
                    actionType="ocr",
                    actionInputs=ActionInputs(
                        content=ocr_result_str,
                        startBox=None,
                        endBox=None,
                        key=None,
                        direction=None
                    ),
                    boxArgs=[],
                    otherArgs=[]
                )
            )
        )
    finally:
        os.close(tmp_fd)
        os.unlink(tmp_path)

# 使用示例
if __name__ == "__main__":
    # 多次实例化会得到同一个对象
    ocr1 = PaddleOCRSingleton()


    # 识别图片
    image_path = r"/home/lenovo/Project/ProjectDir/JD-RPA-pro/assert/0_screenshot.png" # resource/test/left_1.png

    result = ocr1.recognize(image_path)
    print("识别结果:", result)
     # 查找目标文本坐标
    target_text = "(\d+)秒|(\d+)分|(\d{2}:\d{2})" # jd_5e500c63eeec0
    target_text = "客服助手"  # jd_5e500c63eeec0
    positions = ocr1.get_text_position_center_list(target_text)
    print(f"文本 '{target_text}' 的坐标列表:", positions)
