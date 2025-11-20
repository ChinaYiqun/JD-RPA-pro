# =========================== 全局开关 =========================== #
# 设置为 True 使用本地部署模型，False 使用在线 API
USE_LOCAL_MODEL = False

# =========================== 本地模型配置 ======================= #
LOCAL_CONFIG = {
    # Qwen3-VL-8B-Instruct（部署在 GPU 2，端口 8888）
    "qwen3-vl-8b": {
        "base_url": "http://127.0.0.1:8888/v1",
        "api_key": "",  # 本地模型可以不需要 apikey
        "model": "/home/lenovo/Project/ModelDir/Qwen3-VL-8B-Instruct/"
    },
    # 可扩展其他本地模型
    # "qwen3-vl-32b": {
    #     "base_url": "http://127.0.0.1:8123/v1",
    #     "api_key": "",
    #     "model": "/home/lenovo/Project/ModelDir/Qwen3-VL-32B-Instruct/"
    # }
}

# 当前使用的本地模型名称（必须是 LOCAL_CONFIG 中的 key）
CURRENT_LOCAL_MODEL = "qwen3-vl-8b"

# =========================== 在线 API 配置 ====================== #
REMOTE_CONFIG = {
    # OpenRouter - Qwen3-VL-8B
    "openrouter-qwen3vl-8b": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": "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",
        "model": "qwen/qwen3-vl-8b-instruct"
    },
    # DashScope - qwen3-vl-plus
    "dashscope-qwen3vl-plus": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": "sk-b970141d531246f79f01cce4b2074f2e",
        "model": "qwen3-vl-plus"
    },
    # Volces Doubao
    "doubao-ui-tars": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "api_key": "8375698b-d883-4222-b1c4-af4c872419c9",
        "model": "doubao-1-5-ui-tars-250428"
    },
    # OpenRouter - Gemini 2.5 Pro
    "openrouter-gemini-2.5": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": "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",
        "model": "google/gemini-2.5-pro"
    },
    # OpenRouter - Claude Sonnet 4.5
    "openrouter-claude-sonnet": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": "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",
        "model": "anthropic/claude-sonnet-4.5"
    },
    # OpenRouter - Qwen3-VL-30B
    "openrouter-qwen3vl-30b": {
        "base_url": "https://openrouter.ai/api/v1",
        "api_key": "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",
        "model": "qwen/qwen3-vl-30b-a3b-instruct"
    }
}

# 当前使用的远程模型名称（必须是 REMOTE_CONFIG 中的 key）
CURRENT_REMOTE_MODEL = "openrouter-qwen3vl-8b"
CURRENT_REMOTE_MODEL = "dashscope-qwen3vl-plus"


# =========================== 自动选择配置 ======================= #
if USE_LOCAL_MODEL:
    config = LOCAL_CONFIG[CURRENT_LOCAL_MODEL]
else:
    config = REMOTE_CONFIG[CURRENT_REMOTE_MODEL]

base_url = config["base_url"]
api_key = config["api_key"]
model = config["model"]
