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

def get_last_n_assistant_outputs(history: List[dict], n: int = 5) -> List[str]:
    """从 history 中提取最近 n 条 assistant 的 output_text（纯字符串）"""
    outputs = []
    for record in reversed(history):
        if record.get("role") == "assistant":
            content = record.get("content")
            if isinstance(content, str):
                outputs.append(content.strip())
            elif isinstance(content, list):
                # 多模态格式：取第一个 text block
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        outputs.append(item.get("text", "").strip())
                        break
                else:
                    outputs.append("")  # 无文本则空字符串
            if len(outputs) >= n:
                break
    return list(reversed(outputs))  # 保持时间顺序


def is_repeating(outputs: List[str], threshold: int = 3) -> bool:
    """判断最近 outputs 是否连续重复 ≥ threshold 次"""
    if len(outputs) < threshold:
        return False
    last = outputs[-1]
    if not last:  # 空输出不计入
        return False
    return all(out == last for out in outputs[-threshold:])


def process_request(request: PlanActionRequest) -> PlanActionResponse:
    tid = request.tid
    mgdb_client = MongoDBClient()
    history = mgdb_client.get_history(tid)
    flag = len(history) > 0

    os.makedirs(f"./task/{tid}", exist_ok=True)

    base64_image = request.image
    width, height = get_image_size_from_base64(base64_image)

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    original_screenshot_path = f"./task/{tid}/{timestamp}.jpg"
    base64_to_img(base64_image, original_screenshot_path)

    task = request.task
    if flag:
        task = "继续下一步操作，或者结束任务"

    # ====== 新增：重复检测逻辑 ======
    last_outputs = get_last_n_assistant_outputs(history, n=5)
    repeat_count = 0
    if last_outputs:
        last_output = last_outputs[-1]
        # 计算连续重复次数
        for out in reversed(last_outputs):
            if out == last_output:
                repeat_count += 1
            else:
                break

    # 如果已经重复 >=3 次
    if repeat_count >= 3:
        # 第4次及以上：直接返回 FINISH
        if repeat_count >= 4:
            print(f"TID={tid}: 模型输出已连续重复 {repeat_count} 次，强制终止任务。")
            return PlanActionResponse(
                status=0,
                httpCode=200,
                message="OK",
                result=ResultData(
                    status="FINISH",
                    answer=Answer(
                        actionType="finished",
                        actionInputs=ActionInputs(content=None),
                        boxArgs=[],
                        otherArgs=[]
                    )
                )
            )
        else:
            # 第3次：修改提示词，提醒模型
            task = (
                "【重要提醒】你已连续输出完全相同的内容三次！请立即改变策略，尝试不同的操作或重新分析界面。"
                "不要重复之前的回答。" + task
            )
            print(f"TID={tid}: 检测到连续重复3次，已修改提示词提醒模型。")

    # 调用模型
    action_list, param_list, updated_history = get_cua_response(task, original_screenshot_path, history)

    # 保存历史
    mgdb_client.save_history(tid, updated_history)

    # ====== 后续动作解析逻辑（保持不变）======
    action_type = None
    box_args = []
    content = None
    key = None
    wait_time = None
    if action_list and len(action_list) > 0:
        original_action = action_list[0]
        if original_action in ["left_click", "click"]:
            action_type = "click"
        elif original_action == "double_click":
            action_type = "double_click"
        elif original_action == "right_click":
            action_type = "right_click"
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

        if param_list and len(param_list) > 0:
            param = param_list[0]
            if action_type in ["click", "double_click", "left_click", "right_click"] and isinstance(param, tuple) and len(param) == 2:
                box_args = [str(param[0]), str(param[1])]
                draw_text_on_image(f"action:{original_action}", param, original_screenshot_path, f"./img_mark_log/{tid}/{timestamp}.jpg")
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

    # 返回响应（保持原逻辑）
    if action_type == "type":
        return PlanActionResponse(
            status=0,
            httpCode=200,
            message="OK",
            result=ResultData(
                status="FINISH",
                answer=Answer(
                    actionType=action_type,
                    actionInputs=ActionInputs(content=content),
                    boxArgs=[],
                    otherArgs=[]
                )
            )
        )

    if action_type in ["click", "double_click", "left_click", "right_click"]:
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
                    actionInputs=ActionInputs(content=content),
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
                    actionInputs=ActionInputs(content=None),
                    boxArgs=[],
                    otherArgs=[]
                )
            )
        )

    # 默认 fallback
    return PlanActionResponse(
        status=0,
        httpCode=200,
        message="OK",
        result=ResultData(
            status="FINISH",
            answer=Answer(
                actionType="finished",
                actionInputs=ActionInputs(content="模型未返回有效动作，任务终止"),
                boxArgs=[],
                otherArgs=[]
            )
        )
    )
