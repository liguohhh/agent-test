"""
功能管理模块

负责AI功能的注册、管理和执行调度
"""

import json
import time
from typing import Any, Dict, Generator, List, Optional

from app.config import settings
from app.core.exceptions import FunctionNotFoundError, ValidationError
from app.services.deepseek_adapter import DeepSeekAdapter
from app.database.crud import ConversationCRUD
from app.database import get_db


class FunctionConfig:
    """功能配置类"""

    def __init__(
        self,
        function_id: str,
        name: str,
        description: str,
        system_prompt: str,
        input_schema: Dict[str, Any],
        model_params: Optional[Dict[str, Any]] = None,
        max_input_length: Optional[int] = None,
        estimated_time: Optional[float] = None,
        supports_stream: bool = True,
        is_active: bool = True
    ):
        self.function_id = function_id
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.input_schema = input_schema
        self.model_params = model_params or {}
        self.max_input_length = max_input_length
        self.estimated_time = estimated_time
        self.supports_stream = supports_stream
        self.is_active = is_active

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.function_id,
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "max_input_length": self.max_input_length,
            "estimated_time": self.estimated_time,
            "supports_stream": self.supports_stream,
            "model_params": self.model_params
        }

    def validate_input(self, input_data: Dict[str, Any]) -> None:
        """验证输入数据是否符合schema"""
        required_fields = self.input_schema.get("required", [])
        properties = self.input_schema.get("properties", {})

        # 检查必需字段
        for field in required_fields:
            if field not in input_data:
                raise ValidationError(f"缺少必需参数: {field}", field=field)

        # 检查字段类型
        for field, value in input_data.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type and not self._check_type(value, expected_type):
                    raise ValidationError(
                        f"参数 '{field}' 类型错误，期望 {expected_type}，实际 {type(value).__name__}",
                        field=field
                    )

        # 检查输入长度
        if self.max_input_length:
            total_length = sum(len(str(v)) for v in input_data.values())
            if total_length > self.max_input_length:
                raise ValidationError(
                    f"输入内容过长，最大允许 {self.max_input_length} 个字符"
                )

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查值类型是否符合期望"""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }

        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type is None:
            return True  # 未知类型，跳过检查

        return isinstance(value, expected_python_type)


class FunctionManager:
    """功能管理器

    负责AI功能的注册、管理和执行调度
    """

    def __init__(self):
        self._functions: Dict[str, FunctionConfig] = {}
        self._deepseek_adapter = DeepSeekAdapter()
        self._init_default_functions()

    def _init_default_functions(self) -> None:
        """初始化默认的AI功能"""

        # 中译英功能
        self.register_function(FunctionConfig(
            function_id="translation_zh_to_en",
            name="中译英",
            description="将中文文本翻译成英文",
            system_prompt="你是一个专业的中英翻译助手。请将用户提供的中文文本准确、自然地翻译成英文。保持原文的语气和含义，确保翻译结果符合英语表达习惯。",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "需要翻译的中文文本"
                    }
                },
                "required": ["text"]
            },
            model_params={
                "temperature": 0.3,
                "max_tokens": 2000
            },
            max_input_length=5000,
            estimated_time=5.0,
            supports_stream=True
        ))

        # 英译中功能
        self.register_function(FunctionConfig(
            function_id="translation_en_to_zh",
            name="英译中",
            description="将英文文本翻译成中文",
            system_prompt="你是一个专业的英中翻译助手。请将用户提供的英文文本准确、自然地翻译成中文。保持原文的语气和含义，确保翻译结果符合中文表达习惯。",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "需要翻译的英文文本"
                    }
                },
                "required": ["text"]
            },
            model_params={
                "temperature": 0.3,
                "max_tokens": 2000
            },
            max_input_length=5000,
            estimated_time=5.0,
            supports_stream=True
        ))

        # 文本总结功能
        self.register_function(FunctionConfig(
            function_id="text_summary",
            name="文本总结",
            description="对长文本进行智能总结，提取关键信息",
            system_prompt="你是一个专业的文本总结助手。请对用户提供的文本进行智能总结，提取关键信息和要点。总结应该简洁明了，保持原文的主要内容和逻辑结构。",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "需要总结的文本内容"
                    },
                    "summary_length": {
                        "type": "string",
                        "enum": ["short", "medium", "long"],
                        "description": "总结长度：short（简短）、medium（中等）、long（详细）",
                        "default": "medium"
                    }
                },
                "required": ["text"]
            },
            model_params={
                "temperature": 0.5,
                "max_tokens": 1000
            },
            max_input_length=10000,
            estimated_time=8.0,
            supports_stream=True
        ))

    def register_function(self, function_config: FunctionConfig) -> None:
        """注册新的AI功能"""
        self._functions[function_config.function_id] = function_config

    def get_function(self, function_id: str) -> FunctionConfig:
        """获取功能配置"""
        if function_id not in self._functions:
            raise FunctionNotFoundError(function_id)

        function = self._functions[function_id]
        if not function.is_active:
            raise FunctionNotFoundError(f"功能 '{function_id}' 已被禁用")

        return function

    def list_functions(self) -> List[Dict[str, Any]]:
        """获取所有可用功能列表"""
        return [
            func.to_dict()
            for func in self._functions.values()
            if func.is_active
        ]

    def execute_function(
        self,
        function_id: str,
        input_data: Dict[str, Any],
        model_name: Optional[str] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """同步执行AI功能"""
        start_time = time.time()

        # 获取功能配置
        function = self.get_function(function_id)

        # 验证输入参数
        function.validate_input(input_data)

        # 构建用户输入
        user_input = self._build_user_input(function, input_data)

        # 准备模型参数
        model_params = function.model_params.copy()
        if model_name:
            # 临时替换模型进行测试
            adapter = DeepSeekAdapter(model=model_name)
        else:
            adapter = self._deepseek_adapter

        # 执行AI调用
        result = adapter.complete_text(
            system_prompt=function.system_prompt,
            user_input=user_input,
            **model_params
        )

        # 计算执行时间
        execution_time = time.time() - start_time

        # 构建返回结果
        response = {
            "function_id": function_id,
            "result": {
                "content": result["content"]
            },
            "usage": result["usage"],
            "execution_time": execution_time,
            "model_used": result["model"],
            "cached": False  # TODO: 实现缓存逻辑
        }

        # 保存对话记录
        try:
            db = next(get_db())
            crud = ConversationCRUD(db)
            crud.create_conversation(
                function_id=function_id,
                function_name=function.name,
                model_used=result["model"],
                user_input=user_input,
                ai_response=result["content"],
                total_tokens=result["usage"]["total_tokens"],
                execution_time=execution_time,
                metadata={"input_data": input_data, "model_params": model_params}
            )
        except Exception as e:
            # 记录错误但不影响响应
            print(f"保存对话记录失败: {e}")

        return response

    def stream_execute_function(
        self,
        function_id: str,
        input_data: Dict[str, Any],
        model_name: Optional[str] = None,
        use_cache: bool = False
    ) -> Generator[Dict[str, Any], None, None]:
        """流式执行AI功能"""
        start_time = time.time()

        # 获取功能配置
        function = self.get_function(function_id)

        # 验证输入参数
        function.validate_input(input_data)

        # 检查是否支持流式
        if not function.supports_stream:
            raise ValidationError(f"功能 '{function_id}' 不支持流式响应")

        # 构建用户输入
        user_input = self._build_user_input(function, input_data)

        # 准备模型参数
        model_params = function.model_params.copy()
        if model_name:
            adapter = DeepSeekAdapter(model=model_name)
        else:
            adapter = self._deepseek_adapter

        # 发送开始信号
        yield {
            "type": "start",
            "function_id": function_id,
            "timestamp": int(time.time())
        }

        # 用于收集完整内容和统计信息
        full_content = ""
        usage_info = None
        finish_reason = None

        try:
            # 执行流式AI调用
            for chunk in adapter.stream_complete_text(
                system_prompt=function.system_prompt,
                user_input=user_input,
                **model_params
            ):
                if chunk["type"] == "content":
                    full_content += chunk["content"]
                    yield {
                        "type": "token",
                        "content": chunk["content"],
                        "timestamp": chunk["timestamp"]
                    }

                elif chunk["type"] == "usage":
                    usage_info = chunk["usage"]

                elif chunk["type"] == "finish":
                    finish_reason = chunk["finish_reason"]
                    break

                elif chunk["type"] == "error":
                    yield {
                        "type": "error",
                        "message": chunk["error"],
                        "timestamp": int(time.time())
                    }
                    return

        except Exception as e:
            yield {
                "type": "error",
                "message": f"流式执行错误: {str(e)}",
                "timestamp": int(time.time())
            }
            return

        # 计算执行时间
        execution_time = time.time() - start_time

        # 发送结束信号
        yield {
            "type": "end",
            "usage": usage_info or {"total_tokens": 0},
            "execution_time": execution_time,
            "timestamp": int(time.time()),
            "finish_reason": finish_reason
        }

        # 保存对话记录
        try:
            db = next(get_db())
            crud = ConversationCRUD(db)
            crud.create_conversation(
                function_id=function_id,
                function_name=function.name,
                model_used=model_name or settings.deepseek_model,
                user_input=user_input,
                ai_response=full_content,
                total_tokens=usage_info["total_tokens"] if usage_info else 0,
                execution_time=execution_time,
                metadata={"input_data": input_data, "model_params": model_params, "stream": True}
            )
        except Exception as e:
            # 记录错误但不影响响应
            print(f"保存流式对话记录失败: {e}")

    def _build_user_input(self, function: FunctionConfig, input_data: Dict[str, Any]) -> str:
        """根据功能配置构建用户输入"""
        if function.function_id == "translation_zh_to_en":
            return f"请将以下中文翻译成英文：\n\n{input_data['text']}"

        elif function.function_id == "translation_en_to_zh":
            return f"请将以下英文翻译成中文：\n\n{input_data['text']}"

        elif function.function_id == "text_summary":
            summary_length = input_data.get("summary_length", "medium")
            length_desc = {
                "short": "简短",
                "medium": "中等长度",
                "long": "详细"
            }.get(summary_length, "中等长度")

            return f"请对以下文本进行{length_desc}总结：\n\n{input_data['text']}"

        else:
            # 默认格式化
            return json.dumps(input_data, ensure_ascii=False, indent=2)

    def validate_connection(self) -> Dict[str, Any]:
        """验证DeepSeek API连接"""
        return self._deepseek_adapter.validate_connection()