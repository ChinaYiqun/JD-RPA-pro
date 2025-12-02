import base64
import datetime
import json
import requests
import os


API_HOST = "http://127.0.0.1:6666"


#API_HOST = "http://124.223.85.176:8000"



def taskConfig(api_url=API_HOST + "/api/lam/taskConfig"):
    try:
        response = requests.get(api_url)
        result = response.json()
        print(json.dumps(result, indent=4, ensure_ascii=False))

    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {str(e)}")
    except json.JSONDecodeError as e:
        print(f"解析响应JSON时出错: {str(e)}")


def test_plan_action(image_path, task_prompt,api_url=API_HOST + "/api/lam/planAction"):
    """
    测试POST /api/lam/planAction接口
    :param image_path: 图片文件路径
    :param api_url: 接口URL，默认使用本地测试地址
    """
    try:
        # 1. 读取图片并转换为Base64编码
        if not os.path.exists(image_path):
            print(f"图片文件不存在: {image_path}")
            return

        with open(image_path, "rb") as f:
            image_data = f.read()
            base64_image = base64.b64encode(image_data).decode("utf-8")  # 编码并转为字符串

        # 2. 构造请求参数
        request_data = {
            "uid": "test_user_123",
            "tid": "tmp__" + datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
            "task": task_prompt,  # 首次调用必填
            "language": "中文",
            "image": base64_image
        }
        print(f"tid: {request_data['tid']}")
        # 3. 发送POST请求
        response = requests.post(api_url, json=request_data)
        response.raise_for_status()  # 检查HTTP错误状态码

        # 4. 处理响应
        result = response.json()
        print("接口响应结果:")
        print(json.dumps(result, indent=4, ensure_ascii=False))

    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {str(e)}")
    except json.JSONDecodeError as e:
        print(f"解析响应JSON时出错: {str(e)}")
    except Exception as e:
        print(f"处理过程发生错误: {str(e)}")