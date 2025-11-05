# AI应用后端接口

基于FastAPI和DeepSeek API的流式AI应用后端服务，支持实时文本翻译和摘要功能。

## 🚀 功能特性

- **流式响应**: 支持Server-Sent Events (SSE)的实时流式输出
- **多语言支持**: 中英文互译和文本摘要功能
- **会话记录**: 完整的对话历史存储和管理
- **高并发**: 支持多个并发流式连接
- **RESTful API**: 标准的REST接口设计
- **自动文档**: 完整的API文档和交互式测试界面

## 📁 项目结构

```
agent-test/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI应用主入口
│   ├── config.py            # 应用配置管理
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py        # API路由定义
│   │   └── responses.py     # API响应模型
│   ├── models/
│   │   ├── __init__.py
│   │   └── conversation.py  # 数据库模型
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_service.py    # DeepSeek AI服务
│   │   ├── function_manager.py # AI功能管理
│   │   └── database.py      # 数据库服务
│   └── utils/
│       ├── __init__.py
│       ├── dependencies.py  # 依赖注入
│       ├── exceptions.py    # 自定义异常
│       └── streaming.py     # 流式响应工具
├── .env                     # 环境变量配置
├── requirements.txt         # 依赖包列表
├── run.py                   # 应用启动脚本
└── README.md               # 项目文档
```

## 🛠️ 安装与配置

### 1. 环境要求

- Python 3.11+
- pip 包管理器

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 环境配置

创建 `.env` 文件并配置以下参数：

```env
# DeepSeek API配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 应用配置
APP_NAME=AI应用后端接口
APP_VERSION=1.0.0
DEBUG=false
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///./ai_app.db

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json

# 流式响应配置
STREAM_TIMEOUT=300
MAX_CONCURRENT_STREAMS=100
```

## 🚀 启动服务

### 使用启动脚本（推荐）

```bash
python run.py
```

### 直接启动

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后，访问：
- API服务：http://0.0.0.0:8000
- API文档：http://0.0.0.0:8000/docs
- 交互式API文档：http://0.0.0.0:8000/redoc

## 📚 API接口文档

### 基础信息

- **基础路径**: 所有API接口的基础路径为 `/api`
- **响应格式**: JSON
- **错误处理**: 统一错误响应格式

### 1. 获取功能列表

**接口地址**：`GET /api/functions`

**描述**：获取系统中所有可用的AI功能列表

**响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "translation_zh_to_en",
      "name": "中译英",
      "description": "将中文文本翻译成英文",
      "input_schema": {
        "type": "object",
        "properties": {
          "text": {
            "type": "string",
            "description": "需要翻译的中文文本"
          }
        },
        "required": [
          "text"
        ]
      },
      "max_input_length": 5000,
      "estimated_time": 5,
      "supports_stream": true,
      "model_used": null
    },
    {
      "id": "translation_en_to_zh",
      "name": "英译中",
      "description": "将英文文本翻译成中文",
      "input_schema": {
        "type": "object",
        "properties": {
          "text": {
            "type": "string",
            "description": "需要翻译的英文文本"
          }
        },
        "required": [
          "text"
        ]
      },
      "max_input_length": 5000,
      "estimated_time": 5,
      "supports_stream": true,
      "model_used": null
    },
    {
      "id": "text_summary",
      "name": "文本总结",
      "description": "对长文本进行智能总结，提取关键信息",
      "input_schema": {
        "type": "object",
        "properties": {
          "text": {
            "type": "string",
            "description": "需要总结的文本内容"
          },
          "summary_length": {
            "type": "string",
            "enum": [
              "short",
              "medium",
              "long"
            ],
            "description": "总结长度：short（简短）、medium（中等）、long（详细）",
            "default": "medium"
          }
        },
        "required": [
          "text"
        ]
      },
      "max_input_length": 10000,
      "estimated_time": 8,
      "supports_stream": true,
      "model_used": null
    }
  ]
}
```

### 2. 同步执行功能

**接口地址**：`POST /api/execute`

**描述**：同步执行指定的AI功能，直接返回完整结果

**请求体**：
```json
{
    "function_id": "zh-en_translation",
    "input": {
        "text": "你好世界"
    },
    "use_cache": true,
    "model_name": "deepseek-chat"
}
```

**响应**：
```json
{
    "function_id": "zh-en_translation",
    "result": {
        "content": "Hello World"
    },
    "usage": {
        "input_tokens": 10,
        "output_tokens": 5,
        "total_tokens": 15
    },
    "execution_time": 1.234,
    "model_used": "deepseek-chat",
    "cached": false
}
```

**错误响应**：
```json
{
    "code": 404,
    "message": "功能不存在",
    "error_code": "FUNCTION_NOT_FOUND",
    "details": {
        "function_id": "invalid_function"
    }
}
```

### 3. 流式执行功能

**接口地址**：`POST /api/stream`

**描述**：流式执行指定的AI功能，通过Server-Sent Events实时返回生成结果

**请求体**：
```json
{
    "function_id": "zh-en_translation",
    "input": {
        "text": "你好世界，这是一个流式翻译测试"
    },
    "stream_mode": "tokens"
}
```

**流式响应**：Server-Sent Events (SSE) 格式

**响应事件类型**：

1. **开始事件**：
```
data: {"type": "start", "stream_id": "uuid", "timestamp": 1699123456}
```

2. **Token事件**：
```
data: {"type": "token", "content": "Hello", "timestamp": 1699123457}
data: {"type": "token", "content": " ", "timestamp": 1699123458}
data: {"type": "token", "content": "World", "timestamp": 1699123459}
```

3. **结束事件**：
```
data: {"type": "end", "result": "完整结果", "usage": {"total_tokens": 20}, "timestamp": 1699123460}
```

4. **错误事件**：
```
data: {"type": "error", "message": "错误信息", "timestamp": 1699123461}
```

**流模式选项**：
- `tokens`: 逐token返回，实时性最高
- `chunks`: 累积块返回，减少传输频率
- `sentences`: 句子级返回，适合文本生成

### 错误处理

所有API错误都遵循统一响应格式：

```json
{
    "code": "错误码",
    "message": "错误描述",
    "error_code": "内部错误码",
    "details": {}
}
```

**常见错误码**：
- `400`: 请求参数错误
- `404`: 功能不存在
- `500`: 服务器内部错误




## 🔧 技术栈

- **后端框架**: FastAPI
- **AI服务**: DeepSeek API
- **数据库**: SQLite
