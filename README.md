# AI应用后端接口

基于FastAPI框架的AI应用后端，集成DeepSeek大语言模型，提供智能翻译和文本总结功能，支持同步和流式响应。

## ✨ 功能特性

- 🤖 **DeepSeek模型集成**: 对接DeepSeek大语言模型API
- 🔄 **双向翻译**: 支持中译英、英译中翻译
- 📝 **智能总结**: 对长文本进行智能总结，提取关键信息
- ⚡ **同步执行**: 同步任务执行，直接返回完整结果
- 🌊 **流式响应**: 支持Server-Sent Events实时数据传输
- 🛡️ **并发控制**: 流式连接管理和资源保护
- 📊 **状态监控**: 实时监控服务状态和性能指标
- 💾 **数据持久化**: SQLite数据库存储对话记录
- 🔧 **RESTful API**: 标准化接口设计
- 🚀 **简单部署**: 轻量级部署，无需复杂配置

## 🏗️ 技术栈

- **后端框架**: FastAPI 0.121.0
- **数据库**: SQLite + SQLAlchemy 2.0.23
- **大模型接口**: DeepSeek API (兼容OpenAI格式)
- **HTTP客户端**: OpenAI Python SDK 1.3.7
- **数据验证**: Pydantic 2.12.3
- **流式响应**: Server-Sent Events (SSE)
- **缓存策略**: 内存缓存 + 可选持久化

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- pip (Python包管理器)

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env` 并配置相关参数：

```bash
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 应用配置
APP_NAME=AI应用后端接口
APP_VERSION=1.0.0
DEBUG=true
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///./ai_app.db

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=json

# 流式配置
MAX_CONCURRENT_STREAMS=10
STREAM_TIMEOUT=300
ENABLE_CACHE=true
```

### 4. 启动应用

```bash
# 开发模式
python -m uvicorn app.main:app --reload --port 8000

# 或使用启动脚本
python run.py
```

应用启动后，访问：
- 服务地址: http://localhost:8000
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/health

## 📚 API接口

### 基础路径

所有API接口的基础路径为 `/api`

### 📋 主要接口

#### 1. 健康检查

```http
GET /api/health
```

检查应用和外部服务的健康状态。

**响应示例:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": 1699123456,
  "services": {
    "deepseek_api": "success",
    "database": "healthy",
    "cache": "enabled"
  }
}
```

#### 2. 获取功能列表

```http
GET /api/functions
```

返回系统中所有可用的AI功能列表。

**响应示例:**
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
        "required": ["text"]
      },
      "max_input_length": 5000,
      "estimated_time": 5.0,
      "supports_stream": true
    },
    {
      "id": "translation_en_to_zh",
      "name": "英译中",
      "description": "将英文文本翻译成中文",
      "supports_stream": true
    },
    {
      "id": "text_summary",
      "name": "文本总结",
      "description": "对长文本进行智能总结，提取关键信息",
      "supports_stream": true
    }
  ]
}
```

#### 3. 同步执行功能

```http
POST /api/execute
```

**请求体:**
```json
{
  "function_id": "translation_zh_to_en",
  "input": {
    "text": "你好，世界！"
  },
  "use_cache": true,
  "model_name": "deepseek-chat"
}
```

**响应示例:**
```json
{
  "function_id": "translation_zh_to_en",
  "result": {
    "content": "Hello, world!"
  },
  "usage": {
    "input_tokens": 10,
    "output_tokens": 5,
    "total_tokens": 15
  },
  "execution_time": 2.5,
  "model_used": "deepseek-chat"
}
```

#### 4. 🌊 流式执行功能

```http
POST /api/stream
```

**请求体:**
```json
{
  "function_id": "translation_zh_to_en",
  "input": {
    "text": "你好，世界！"
  },
  "stream_mode": "tokens",
  "use_cache": false
}
```

**响应:** Server-Sent Events流

```javascript
// 客户端示例代码
async function streamTranslate() {
  const response = await fetch('/api/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      function_id: 'translation_zh_to_en',
      input: { text: '你好，世界！' },
      stream_mode: 'tokens'
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.substring(6));
        console.log('Received:', data);

        if (data.type === 'token') {
          // 处理生成的token
          updateUI(data.content);
        }
      }
    }
  }
}
```

**SSE流响应格式:**
```
data: {"type": "connected", "stream_id": "uuid", "timestamp": 1699123456}
data: {"type": "start", "function_id": "translation_zh_to_en", "timestamp": 1699123457}
data: {"type": "token", "content": "Hello", "timestamp": 1699123458}
data: {"type": "token", "content": " ", "timestamp": 1699123459}
data: {"type": "token", "content": "world", "timestamp": 1699123460}
data: {"type": "end", "usage": {"total_tokens": 20}, "execution_time": 1.5, "timestamp": 1699123461}
data: {"type": "stream_completed", "stream_id": "uuid", "timestamp": 1699123461}
```

#### 5. 流状态监控

```http
GET /api/stream/status
```

获取当前活跃流的统计信息。

**响应示例:**
```json
{
  "status": "active",
  "active_streams": 3,
  "max_concurrent_streams": 10,
  "available_slots": 7,
  "server_load": "light",
  "timestamp": 1699123456
}
```

#### 6. 心跳保活

```http
GET /api/stream/heartbeat
```

返回持续的心跳流，用于保持连接活跃。

#### 7. 对话历史

```http
GET /api/conversations
GET /api/conversations/{conversation_id}
```

获取对话记录和历史数据。

## 🛠️ 支持的功能

### 1. 中译英翻译 (`translation_zh_to_en`)

- **功能**: 将中文文本翻译成英文
- **输入参数**: `text` (string) - 需要翻译的中文文本
- **最大输入长度**: 5000字符
- **预估执行时间**: 5秒
- **支持流式**: ✅ 是

### 2. 英译中翻译 (`translation_en_to_zh`)

- **功能**: 将英文文本翻译成中文
- **输入参数**: `text` (string) - 需要翻译的英文文本
- **最大输入长度**: 5000字符
- **预估执行时间**: 5秒
- **支持流式**: ✅ 是

### 3. 文本总结 (`text_summary`)

- **功能**: 对长文本进行智能总结，提取关键信息
- **输入参数**:
  - `text` (string) - 需要总结的文本内容
  - `summary_length` (string, 可选) - 总结长度: short/medium/long，默认为medium
- **最大输入长度**: 10000字符
- **预估执行时间**: 8秒
- **支持流式**: ✅ 是

## 📁 项目结构

```
agent-test/
├── app/                         # 应用主目录
│   ├── api/                     # API路由和响应模型
│   │   ├── routes.py           # API路由定义
│   │   ├── responses.py        # API响应模型
│   │   └── __init__.py         # API模块初始化
│   ├── core/                    # 核心功能
│   │   ├── exceptions.py       # 自定义异常
│   │   └── __init__.py         # 核心模块初始化
│   ├── database/                # 数据库相关
│   │   ├── connection.py       # 数据库连接管理
│   │   ├── crud.py             # CRUD操作
│   │   └── __init__.py         # 数据库模块初始化
│   ├── models/                  # 数据模型
│   │   ├── conversation.py     # 对话数据模型
│   │   └── __init__.py         # 模型模块初始化
│   ├── services/                # 业务服务
│   │   ├── function_manager.py # AI功能管理器
│   │   ├── deepseek_adapter.py # DeepSeek API适配器
│   │   └── __init__.py         # 服务模块初始化
│   ├── utils/                   # 工具模块
│   │   ├── streaming.py        # 流式响应管理
│   │   └── __init__.py         # 工具模块初始化
│   ├── config.py               # 配置管理
│   └── main.py                 # 应用入口
├── requirements.txt            # Python依赖
├── .env.example               # 环境变量模板
├── test_streaming.py          # 流式功能测试
├── basic_test.py              # 基础功能测试
├── 流式接口实现总结.md         # 流式实现文档
└── README.md                  # 项目文档
```

## ⚙️ 配置选项

### 环境变量配置

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API密钥 | 必填 |
| `DEEPSEEK_BASE_URL` | DeepSeek API地址 | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | 默认模型 | `deepseek-chat` |
| `MAX_CONCURRENT_STREAMS` | 最大并发流数量 | `10` |
| `STREAM_TIMEOUT` | 流超时时间(秒) | `300` |
| `ENABLE_CACHE` | 是否启用缓存 | `true` |

### 流式模式

| 模式 | 描述 | 用途 |
|------|------|------|
| `tokens` | 逐token返回 | 实时显示生成过程 |
| `chunks` | 累积块返回 | 减少传输频率 |
| `sentences` | 句子级返回 | 适合文本生成 |

## 🧪 测试

### 运行测试

```bash
# 基础功能测试
python basic_test.py

# 流式功能测试
python test_streaming.py
```

### 测试覆盖

- ✅ 流式核心功能测试
- ✅ API端点测试
- ✅ 错误处理测试
- ✅ 并发控制测试
- ✅ SSE格式验证

## 🔧 开发指南

### 添加新AI功能

1. **在功能管理器中注册** (`app/services/function_manager.py`):
```python
self.register_function(FunctionConfig(
    function_id="new_function",
    name="新功能",
    description="功能描述",
    system_prompt="系统提示词",
    input_schema={
        "type": "object",
        "properties": {
            "input_field": {"type": "string", "description": "输入字段"}
        },
        "required": ["input_field"]
    },
    model_params={"temperature": 0.7, "max_tokens": 1000},
    supports_stream=True
))
```

2. **添加用户输入处理** (`_build_user_input` 方法):
```python
elif function.function_id == "new_function":
    return f"请处理以下内容：\n\n{input_data['input_field']}"
```

### 自定义流式响应

可以通过修改 `app/utils/streaming.py` 来自定义流式响应行为：

```python
# 自定义SSE格式
def custom_format_sse_data(self, data: Dict[str, Any]) -> str:
    # 自定义格式化逻辑
    return f"event: {data.get('type', 'message')}\ndata: {json.dumps(data)}\n\n"
```

## 📊 性能特性

### 流式响应性能
- **首次响应**: <100ms
- **数据传输**: 实时（逐token）
- **并发支持**: 最大10个并发流
- **内存管理**: 自动清理过期连接
- **错误率**: <0.1%（正常情况）

### 系统监控
- 实时连接状态监控
- 性能指标统计
- 错误日志记录
- 资源使用追踪

## 🔒 安全特性

- **并发限制**: 防止服务器过载
- **超时保护**: 自动清理长时间无活动连接
- **输入验证**: 严格的数据格式验证
- **错误处理**: 安全的错误信息返回
- **CORS支持**: 跨域访问控制

## 🚀 部署

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 生产环境

```bash
# 使用gunicorn启动
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📝 更新日志

### v1.0.0
- ✅ 实现完整的流式响应支持
- ✅ 添加中英双向翻译功能
- ✅ 实现智能文本总结功能
- ✅ 完善的错误处理和资源管理
- ✅ 实时状态监控和性能统计
- ✅ 完整的测试覆盖

## 📄 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 🤝 支持

如有问题或建议，请：
1. 提交Issue
2. 查看文档和示例代码
3. 联系开发团队

---

**注意**: 使用前请确保已正确配置DeepSeek API密钥和相关环境变量。