import datetime
import json
import os

from pydantic import BaseModel
from typing import Optional, List

from my_tools.pic_utils import base64_to_img, get_image_size_from_base64, draw_text_on_image
from service.adapter_mul import get_cua_response
from service.mgdb_client import MongoDBClient


# 请求参数模型
class PlanActionRequest(BaseModel):
    uid: str  # 用户ID
    tid: str  # 客户端生成的任务ID
    task: Optional[str] = None  # 可选，首次调用时必填
    language: Optional[str] = "中文"  # 可选，默认中文
    image: str  # 当前屏幕截图的Base64编码

# 响应参数模型 - 嵌套结构
class ActionInputs(BaseModel):
    startBox: Optional[str] = None
    endBox: Optional[str] = None
    content: Optional[str] = None
    key: Optional[str] = None
    direction: Optional[str] = None

class Answer(BaseModel):
    actionType: str
    actionInputs: ActionInputs
    boxArgs: List[str]
    otherArgs: List[str]

class ResultData(BaseModel):
    status: str
    answer: Answer

class PlanActionResponse(BaseModel):
    status: int
    httpCode: int
    message: str
    result: ResultData

def process_request(request: PlanActionRequest) -> PlanActionResponse:
    # tid = request.tid
    # # 判断是否存在以tid 为名称的文件夹 flag 标志
    # flag = os.path.exists(f"./task/{tid}")
    # # 以tid 名称建一个文件夹，如果存在文件夹了，则不创建
    # os.makedirs(f"./task/{tid}", exist_ok=True)
    #
    # base64_image = request.image
    # width, height = get_image_size_from_base64(base64_image)
    #
    #
    #
    # timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    #
    # original_screenshot_path = f"./task/{tid}/{timestamp}.jpg"
    # base64_to_img(base64_image, original_screenshot_path)
    #
    # task = request.task
    # history = []
    # history_file_path = f"./task/{tid}/history.json"
    #
    # if flag:
    #     task = "继续下一步操作，或者结束任务"
    #     # 从 ./task/{tid}/history.json 文件中读取内容
    #     try:
    #         if os.path.exists(history_file_path):
    #             with open(history_file_path, "r", encoding="utf-8") as f:
    #                 history = json.load(f)
    #     except (json.JSONDecodeError, IOError) as e:
    #         # 如果文件损坏或读取失败，从空历史开始
    #         print(f"警告：读取历史文件失败，从空历史开始: {e}")
    #         history = []
    #
    # action_list, param_list, updated_history = get_cua_response(task, original_screenshot_path, history)
    #
    # # 将更新后的完整历史记录写入JSON文件（updated_history已包含所有历史+当前交互）
    # # 使用"w"模式覆盖写入，因为updated_history已经包含了完整的历史记录
    # with open(history_file_path, "w", encoding="utf-8") as f:
    #     json.dump(updated_history, f, indent=4, ensure_ascii=False)

    tid = request.tid
    # 初始化MongoDB客户端
    mgdb_client = MongoDBClient()
    # 从MongoDB获取历史记录
    history = mgdb_client.get_history(tid)
    # 判断是否为续传任务（有历史记录即为续传）
    flag = len(history) > 0

    # 保留任务文件夹用于存储截图（原逻辑不变）
    os.makedirs(f"./task/{tid}", exist_ok=True)

    base64_image = request.image
    width, height = get_image_size_from_base64(base64_image)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    original_screenshot_path = f"./task/{tid}/{timestamp}.jpg"
    base64_to_img(base64_image, original_screenshot_path)

    task = request.task
    # 续传任务使用固定提示（原逻辑不变）
    if flag:
        task = "继续下一步操作，或者结束任务"

    # 获取模型响应（原逻辑不变）
    action_list, param_list, updated_history = get_cua_response(task, original_screenshot_path, history)

    # 将更新后的历史记录保存到MongoDB（替换原文件写入逻辑）
    mgdb_client.save_history(tid, updated_history)


    action_type = None
    box_args = []
    content = None
    key = None
    wait_time = None
    if action_list and len(action_list) > 0:
        # 动作类型映射
        original_action = action_list[0]
        if original_action in ["left_click", "click"]:
            action_type = "click"
        elif original_action == "type":
            action_type = "type"
        elif original_action == "key":
            action_type = "hotkey"
        elif original_action == "wait":
            action_type = "wait"
        elif original_action == "terminate":
            action_type = "finished"
        elif original_action == "answer":
            action_type = "answer"


        # 参数解析
        if param_list and len(param_list) > 0:
            param = param_list[0]
            if action_type == "click" and isinstance(param, tuple) and len(param) == 2:
                # 坐标转换为字符串格式
                box_args = [str(param[0]), str(param[1])]
                # 将坐标绘制到
                draw_text_on_image(f"action:{original_action}", param, original_screenshot_path,f"./img_mark_log/{tid}/{timestamp}.jpg")
            elif action_type == "type" and isinstance(param, str):
                content = param
            elif action_type == "hotkey" and isinstance(param, str):
                key = param
            elif action_type == "wait" and isinstance(param, (int, float)):
                wait_time = param
            elif action_type == "answer":
                content = param
            elif action_type == "finished":
                content = param
    if action_type == "click":
        return PlanActionResponse(
            status=0,
            httpCode=200,
            message="OK",
            result=ResultData(
                status="CONTINUE",
                answer=Answer(
                    actionType=action_type,
                    actionInputs=ActionInputs(
                        startBox=f"({box_args[0]},{box_args[1]})" if box_args else None,
                        content=content,
                        key=key,
                    ),
                    boxArgs=box_args,
                    otherArgs=[str(wait_time)] if wait_time else []
                )
            )
        )
    if action_type == "answer":
        return PlanActionResponse(
            status=0,
            httpCode=200,
            message="OK",
            result=ResultData(
                status="FINISH",
                answer=Answer(
                    actionType=action_type,
                    actionInputs=ActionInputs(
                        content=content,
                    ),
                    boxArgs=[],
                    otherArgs=[]
                )
            )
        )
    if action_type == "finished":
        return PlanActionResponse(
            status=0,
            httpCode=200,
            message="OK",
            result=ResultData(
                status="FINISH",
                answer=Answer(
                    actionType=action_type,
                    actionInputs=ActionInputs(
                        content=None,
                    ),
                    boxArgs=[],
                    otherArgs=[]
                )
            )
        )
