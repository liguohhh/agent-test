# AI应用后端接口

基于Python FastAPI框架实现的小型AI应用后端接口，集成DeepSeek大语言模型，提供中译英、英译中、内容总结等核心功能。

## 功能特性

- **DeepSeek模型集成**: 对接DeepSeek大语言模型API
- **多语言翻译**: 支持中译英、英译中翻译功能
- **智能总结**: 对长文本进行智能总结，提取关键信息
- **同步执行**: 同步任务执行模式，直接返回结果
- **流式响应**: 支持Server-Sent Events实时数据传输
- **RESTful API**: 标准化的接口设计
- **简单部署**: SQLite数据库，无需复杂配置

## 技术栈

- **后端框架**: FastAPI 0.104.1
- **数据库**: SQLite
- **大模型接口**: DeepSeek API (兼容OpenAI格式)
- **HTTP客户端**: OpenAI Python SDK
- **流式响应**: Server-Sent Events (SSE)
- **缓存策略**: 内存缓存 + 可选持久化

## 快速开始

### 1. 环境要求

- Python 3.8+
- pip (Python包管理器)

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env` 文件并配置相关参数：

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
```

### 4. 初始化数据库

```bash
python init_db.py
```

如需重置数据库（删除所有数据）：

```bash
python init_db.py --reset
```

### 5. 启动应用

```bash
python run.py
```

应用启动后，访问：
- 服务地址: http://localhost:8000
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/ping

## API接口

### 基础路径

所有API接口的基础路径为 `/api`

### 主要接口

#### 1. 健康检查

```http
GET /api/health
```

返回应用和外部服务的健康状态。

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
  "code": 200,
  "message": "执行成功",
  "data": {
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
    "model_used": "deepseek-chat",
    "cached": false
  }
}
```

#### 4. 流式执行功能

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
const eventSource = new EventSource('/api/stream', {
  method: 'POST',
  body: JSON.stringify({
    function_id: 'translation_zh_to_en',
    input: { text: '你好，世界！' }
  })
});

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

#### 5. 获取统计信息

```http
GET /api/stats
```

返回应用使用统计和性能数据。

#### 6. 缓存管理

```http
# 清空所有缓存
DELETE /api/cache

# 清空指定功能的缓存
DELETE /api/cache/{function_id}
```

## 支持的功能

### 1. 中译英翻译 (`translation_zh_to_en`)

- **功能**: 将中文文本翻译成英文
- **输入参数**: `text` (string) - 需要翻译的中文文本
- **最大输入长度**: 5000字符
- **预估执行时间**: 5秒

### 2. 英译中翻译 (`translation_en_to_zh`)

- **功能**: 将英文文本翻译成中文
- **输入参数**: `text` (string) - 需要翻译的英文文本
- **最大输入长度**: 5000字符
- **预估执行时间**: 5秒

### 3. 文本总结 (`text_summary`)

- **功能**: 对长文本进行智能总结，提取关键信息
- **输入参数**:
  - `text` (string) - 需要总结的文本内容
  - `summary_length` (string, 可选) - 总结长度: short/medium/long
- **最大输入长度**: 10000字符
- **预估执行时间**: 8秒

## 项目结构

```
agent-test/
├── app/                    # 应用主目录
│   ├── api/               # API路由
│   │   └── v1/           # API v1版本
│   ├── core/             # 核心功能（异常等）
│   ├── database/         # 数据库相关
│   ├── models/           # 数据模型
│   ├── services/         # 业务服务
│   ├── utils/            # 工具模块
│   ├── config.py         # 配置管理
│   └── main.py           # 应用入口
├── requirements.txt       # Python依赖
├── .env                  # 环境变量配置
├── init_db.py           # 数据库初始化脚本
├── run.py               # 应用启动脚本
├── README.md            # 项目文档
└── 架构设计文档.md       # 架构设计文档
```

## 开发说明

### 添加新功能

1. 在 `app/services/function_manager.py` 的 `_init_default_functions` 方法中注册新功能
2. 定义功能的输入schema、系统提示词和模型参数
3. 在 `_build_user_input` 方法中添加对应的输入格式化逻辑

### 自定义配置

通过修改 `app/config.py` 或环境变量来自定义应用配置。

### 日志

应用使用Python标准logging模块，日志级别可通过 `LOG_LEVEL` 环境变量配置。

## 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 支持

如有问题或建议，请联系开发团队。