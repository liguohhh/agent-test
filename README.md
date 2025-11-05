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

### 1. 流式AI接口

#### 1.1 创建流式会话

**接口地址**：`POST /api/stream`

**请求体**：
```json
{
    "prompt": "用户输入的文本内容",
    "function_id": "zh-en_translation"
}
```

**支持的功能ID**：
- `zh-en_translation`: 中文到英文翻译
- `en-zh_translation`: 英文到中文翻译
- `text_summarization`: 文本摘要

**响应**：Server-Sent Events (SSE) 流式数据

**响应格式**：
```
data: {"type": "start", "stream_id": "uuid", "timestamp": "2025-01-01T00:00:00Z"}

data: {"type": "token", "content": "第", "stream_id": "uuid", "timestamp": "2025-01-01T00:00:00Z"}

data: {"type": "token", "content": "一", "stream_id": "uuid", "timestamp": "2025-01-01T00:00:00Z"}

data: {"type": "end", "stream_id": "uuid", "final_result": "完整结果", "timestamp": "2025-01-01T00:00:00Z"}
```

**错误事件**：
```
data: {"type": "error", "error": "错误信息", "stream_id": "uuid", "timestamp": "2025-01-01T00:00:00Z"}
```

#### 1.2 查询流状态

**接口地址**：`GET /api/stream/status`

**响应**：
```json
{
    "active_streams": 2,
    "max_concurrent_streams": 100
}
```

#### 1.3 流心跳检测

**接口地址**：`GET /api/stream/heartbeat`

**响应**：
```json
{
    "status": "alive",
    "timestamp": "2025-01-01T00:00:00Z"
}
```

### 2. 传统API接口

#### 2.1 获取可用AI功能

**接口地址**：`GET /api/functions`

**响应**：
```json
{
    "functions": [
        {
            "id": "zh-en_translation",
            "name": "中英翻译",
            "description": "将中文文本翻译为英文",
            "examples": ["你好世界", "今天天气很好"]
        },
        {
            "id": "en-zh_translation",
            "name": "英中翻译",
            "description": "将英文文本翻译为中文",
            "examples": ["Hello World", "The weather is nice today"]
        },
        {
            "id": "text_summarization",
            "name": "文本摘要",
            "description": "对长文本进行智能摘要",
            "examples": ["这是一段需要摘要的文本..."]
        }
    ]
}
```

#### 2.2 执行AI功能

**接口地址**：`POST /api/execute`

**请求体**：
```json
{
    "function_id": "zh-en_translation",
    "prompt": "你好世界"
}
```

**响应**：
```json
{
    "success": true,
    "conversation_id": "uuid",
    "function_id": "zh-en_translation",
    "response": "Hello World",
    "execution_time": 1.234,
    "tokens_used": 25,
    "error": null
}
```

#### 2.3 获取历史记录

**接口地址**：`GET /api/history`

**响应**：
```json
{
    "conversations": [
        {
            "id": 1,
            "conversation_id": "uuid",
            "function_id": "zh-en_translation",
            "function_name": "中英翻译",
            "model_used": "deepseek-chat",
            "user_input": "你好世界",
            "ai_response": "Hello World",
            "total_tokens": 25,
            "execution_time": 1.234,
            "status": "completed",
            "created_at": "2025-01-01T00:00:00Z"
        }
    ]
}
```

#### 2.4 获取会话详情

**接口地址**：`GET /api/history/{conversation_id}`

**响应**：
```json
{
    "id": 1,
    "conversation_id": "uuid",
    "function_id": "zh-en_translation",
    "function_name": "中英翻译",
    "model_used": "deepseek-chat",
    "user_input": "你好世界",
    "ai_response": "Hello World",
    "total_tokens": 25,
    "execution_time": 1.234,
    "status": "completed",
    "created_at": "2025-01-01T00:00:00Z"
}
```

### 3. 系统接口

#### 3.1 健康检查

**接口地址**：`GET /health`

**响应**：
```json
{
    "status": "healthy",
    "timestamp": "2025-01-01T00:00:00Z",
    "version": "1.0.0"
}
```

## 💡 使用示例

### Python客户端示例

#### 流式翻译示例

```python
import requests
import json

def stream_translation():
    """流式翻译示例"""
    url = "http://localhost:8000/api/stream"
    data = {
        "prompt": "你好世界，这是一个流式翻译的测试。",
        "function_id": "zh-en_translation"
    }

    print("开始流式翻译...")
    response = requests.post(url, json=data, stream=True)

    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data_str = line[6:]  # 移除 'data: ' 前缀
                try:
                    event_data = json.loads(data_str)
                    event_type = event_data.get('type')

                    if event_type == 'start':
                        print(f"[开始] 流ID: {event_data.get('stream_id')}")
                    elif event_type == 'token':
                        content = event_data.get('content', '')
                        print(content, end='', flush=True)
                    elif event_type == 'end':
                        print(f"\n[完成] 结果: {event_data.get('final_result')}")
                        break
                    elif event_type == 'error':
                        print(f"\n[错误] {event_data.get('error')}")
                        break
                except json.JSONDecodeError:
                    continue

if __name__ == "__main__":
    stream_translation()
```

#### 传统API调用示例

```python
import requests

def translate_text():
    """传统翻译示例"""
    url = "http://localhost:8000/api/execute"
    data = {
        "function_id": "zh-en_translation",
        "prompt": "你好世界"
    }

    response = requests.post(url, json=data)
    result = response.json()

    if result['success']:
        print(f"翻译结果: {result['response']}")
        print(f"执行时间: {result['execution_time']}秒")
        print(f"使用Token: {result['tokens_used']}")
    else:
        print(f"执行失败: {result['error']}")

def get_history():
    """获取历史记录"""
    url = "http://localhost:8000/api/history"
    response = requests.get(url)
    result = response.json()

    print("历史记录:")
    for conv in result['conversations']:
        print(f"- {conv['function_name']}: {conv['user_input']} -> {conv['ai_response']}")

if __name__ == "__main__":
    translate_text()
    get_history()
```

### JavaScript客户端示例

```javascript
// 流式翻译示例
async function streamTranslation() {
    const response = await fetch('http://localhost:8000/api/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            prompt: '你好世界，这是一个流式翻译测试。',
            function_id: 'zh-en_translation'
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let result = '';

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const data = JSON.parse(line.substring(6));
                    if (data.type === 'token') {
                        result += data.content;
                        console.log('当前结果:', result);
                    } else if (data.type === 'end') {
                        console.log('最终结果:', data.final_result);
                        return;
                    }
                } catch (e) {
                    // 忽略解析错误
                }
            }
        }
    }
}

// 调用流式翻译
streamTranslation();
```

## 🔧 技术栈

- **后端框架**: FastAPI
- **AI服务**: DeepSeek API
- **数据库**: SQLite (SQLAlchemy ORM)
- **流式技术**: Server-Sent Events (SSE)
- **异步处理**: asyncio
- **配置管理**: pydantic-settings
- **日志系统**: loguru
- **API文档**: OpenAPI/Swagger

## 🚦 错误处理

系统提供完整的错误处理机制：

- **HTTP状态码**: 标准的HTTP状态码
- **错误信息**: 详细的错误描述和堆栈信息
- **流式错误**: 通过SSE事件推送错误信息
- **超时处理**: 流式连接超时自动断开
- **资源保护**: 最大并发流数量限制

## 📊 监控和日志

- **健康检查**: `/health` 端点监控服务状态
- **流状态**: `/api/stream/status` 监控活跃流数量
- **心跳检测**: `/api/stream/heartbeat` 检测流服务状态
- **结构化日志**: JSON格式的日志输出
- **性能指标**: 执行时间、Token使用量等

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如果您在使用过程中遇到问题，请：

1. 查看 [API文档](http://0.0.0.0:8000/docs)
2. 检查环境配置是否正确
3. 查看日志输出获取错误信息
4. 提交 Issue 获取帮助

---

**注意**: 请确保正确配置DeepSeek API密钥，否则AI功能将无法正常工作。