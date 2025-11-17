import base64
import hashlib
import hmac
import json
import logging
import string
import uuid
import time
from random import random

logging.basicConfig(
    level=logging.INFO,  # 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  # 日志格式
)


logger = logging.getLogger(__name__)
def generate_sign(app_key, timestamp, params_str):
    """
    生成HmacSHA256签名
    加密源：app-key + "; " + timestamp + ";" + 地址栏参数
    """
    # 构造签名源字符串
    sign_source = f"{app_key};{timestamp};{params_str}"
    print(f"sign_source:{sign_source}")
    # 使用HmacSHA256算法生成签名
    key = "1234567".encode('utf-8')
    message = sign_source.encode('utf-8')
    signature = hmac.new(key, message, hashlib.sha256).digest()
    print(f"sign:{signature}")
    # 将签名进行base64编码
    sign = base64.b64encode(signature).decode('utf-8')
    return sign


def get_task_config(requests=None):
    """
    发送GET请求到/api/lam/taskConfig，获取任务配置
    """
    # 确保requests库可用
    if requests is None:
        import requests

    timestamp = str(int(time.time() * 1000))  # 毫秒级时间戳
    app_key = "lam-client"

    # 构造地址栏参数（query params）
    params_str_dict = {"appKey": app_key, "timestamp": timestamp}
    # 构造签名用的参数字符串（格式与服务端约定一致）
    params_str_sign = f"appKey:{app_key},timestamp:{timestamp}"

    # 生成签名
    sign = generate_sign(app_key, timestamp, params_str_sign)
 
    # 构造请求头
    headers = {
        "Content-Type": "application/json",
        "Connection": "keep-alive",
        "app-key": app_key,
        "timestamp": timestamp,
        "sign": sign
    }

    response = None
    result = {}

    try:
        logger.info("Start GET request to /api/lam/taskConfig")
        response = requests.get(
            "http://47.101.55.163:8000/api/lam/taskConfig",
            headers=headers,
            params=params_str_dict  # GET参数通过params传递
        )
        response.raise_for_status()  # 触发HTTP错误状态码异常
        result = response.json()
        formatted_json = json.dumps(result, ensure_ascii=False, indent=2)

        # 若开启打印，直接输出格式化结果

        logger.info("\n" + "-" * 50)
        logger.info("格式化后的任务配置JSON：")
        logger.info("-" * 50 + "\n")
        logger.info(f"taskConfig result: {formatted_json}")

    except requests.exceptions.RequestException as e:
        logger.warning(f"GET request failed: {e}")
        if response:
            logger.info(f"Response status: {response.status_code}, content: {response.text}")

    except json.JSONDecodeError:
        logger.warning("Failed to parse taskConfig response as JSON")

    return result


import base64


def image_to_base64(image_path):
    """
    将图片文件转换为base64编码字符串

    参数:
        image_path (str): 图片文件的路径

    返回:
        str: 图片的base64编码字符串

    异常:
        FileNotFoundError: 图片路径不存在时抛出
        Exception: 其他文件读取或编码错误时抛出
    """
    try:
        # 以二进制模式打开图片文件
        with open(image_path, 'rb') as img_file:
            # 读取图片二进制数据
            image_data = img_file.read()
            # 进行base64编码并转换为字符串
            base64_str = base64.b64encode(image_data).decode('utf-8')
            return base64_str
    except FileNotFoundError:
        raise FileNotFoundError(f"图片路径不存在: {image_path}")
    except Exception as e:
        raise Exception(f"图片转换base64失败: {str(e)}")


def call_planner(task: str, unique_str: str = "111", requests=None,image_path: str = None):
    # 确保requests库可用
    if requests is None:
        import requests
    payload = {
        "uid": '127.0.0.1',
        "tid": str(uuid.uuid5(uuid.NAMESPACE_URL, task + f"[unique_str={unique_str}]")),
        "language": "string",
        "task": task,
        "image": image_to_base64(image_path)
    }

    timestamp = str(int(time.time() * 1000))  # 使用毫秒时间戳
    app_key = "lam-client"

    # 构造地址栏参数字符串
    params_str = {"appKey": app_key, "timestamp": timestamp}
    params_str_sign = f"appKey:{app_key},timestamp:{timestamp}"

    # 生成签名
    sign = generate_sign(app_key, timestamp, params_str_sign)

    headers = {
        "Content-Type": "application/json",
        "Connection": "keep-alive",  # 启用长连接
        "app-key": app_key,
        "timestamp": timestamp,
        "sign": sign
    }
    response = None
    result = {}

    try:
        logger.info(f"Start Request Uptime: ")
        response = requests.post(
            "http://47.101.55.163:8000/api/lam/planAction",
            data=json.dumps(payload),  # 将字典转为 JSON 字符串
            headers=headers, params=params_str
        )
        response.raise_for_status()
        result = response.json()
        logger.info(f"result: {result}")

    except requests.exceptions.RequestException as e:
        logger.warning(f"请求失败: {e}")
        if response:
            logger.info(response)

    except json.JSONDecodeError:
        logger.warning("无法解析响应内容为 JSON 格式")

    return result


import secrets
import string


def generate_random_string(
        length: int = 10,
        include_upper: bool = True,
        include_lower: bool = True,
        include_digits: bool = True,
        include_special: bool = False
) -> str:
    """
    生成随机字符串，支持自定义长度和字符类型

    参数:
        length: 字符串长度（必须为正整数，默认10）
        include_upper: 是否包含大写字母（A-Z，默认True）
        include_lower: 是否包含小写字母（a-z，默认True）
        include_digits: 是否包含数字（0-9，默认True）
        include_special: 是否包含特殊字符（如!@#$等，默认False）

    返回:
        str: 生成的随机字符串

    异常:
        ValueError: 当长度小于等于0，或未启用任何字符类型时抛出
    """
    # 验证长度合法性
    if length <= 0:
        raise ValueError("字符串长度必须为正整数")

    # 定义字符集
    chars = ""
    if include_upper:
        chars += string.ascii_uppercase  # 大写字母：A-Z
    if include_lower:
        chars += string.ascii_lowercase  # 小写字母：a-z
    if include_digits:
        chars += string.digits  # 数字：0-9
    if include_special:
        chars += string.punctuation  # 特殊字符：!@#$%^&*()等

    # 验证字符集非空
    if not chars:
        raise ValueError("至少需要启用一种字符类型（大写/小写/数字/特殊字符）")

    # 生成随机字符串（使用secrets确保高随机性）
    return ''.join(secrets.choice(chars) for _ in range(length))

get_task_config()
# reception_click_frist_message = "用户原始命令为：认真观察'在线咨询'的列表是否存在用户消息，点击第一个用户消息。参考操作步骤为:\n如果列表里面有用户消息，只需要点击第一个用户，在finished action里面content为'已经点击'。\n\n如果'在线咨询'的列表为空，不存在用户消息，不要做任何操作，在finished action里面content为'无历史消息'"
# call_planner(reception_click_frist_message,"111",requests=None,image_path="grounding/1366x768_003.png")
