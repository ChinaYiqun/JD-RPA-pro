import json
import os
# 添加Pydantic相关导入
from pydantic import BaseModel
from typing import Optional, Dict

# 定义响应模型类
class ResultModel(BaseModel):
    status: int
    httpCode: int
    message: str
    result: Optional[Dict] = None




def get_config():
    file_path = "configs/task/20251105-3.json"
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            # 使用模型返回结果
            return ResultModel(
                    status=1,
                    httpCode=404,
                    message=f"配置文件不存在",
                    result=None
                )

        # 读取配置文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            task_data = json.load(f)

        if "tasks" in task_data and isinstance(task_data["tasks"], list):

            for task_item in task_data["tasks"]:
                if isinstance(task_item, dict) and "task" in task_item and isinstance(task_item["task"], str):
                    task_item["task"] = task_item["task"].replace('\\"', '"')




        # 构建响应结构
        return ResultModel(
                status=0,
                httpCode=200,
                message="OK",
                result=task_data
            )

    except Exception as e:
        # 捕获文件读取异常
        return ResultModel(
                status=1,
                httpCode=500,
                message=f"读取配置失败：{str(e)}",
                result=None
            )