"""
DeepSeek API适配器

封装DeepSeek API调用逻辑，提供同步和流式调用支持
"""

import asyncio
from typing import Any, Dict, Generator, Optional, Union

import openai
from openai import OpenAI, Stream
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from app.config import settings
from app.core.exceptions import DeepSeekAPIError, DeepSeekTimeoutError


class DeepSeekAdapter:
    """DeepSeek API适配器

    基于OpenAI SDK封装DeepSeek API调用逻辑，支持同步和流式调用
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        """初始化DeepSeek适配器"""
        self.api_key = api_key or settings.deepseek_api_key
        self.base_url = base_url or settings.deepseek_base_url
        self.model = model or settings.deepseek_model

        # 创建OpenAI客户端
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def create_chat_completion(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[ChatCompletion, Stream[ChatCompletionChunk]]:
        """创建聊天完成请求

        Args:
            messages: 对话消息列表
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            stream: 是否启用流式响应
            **kwargs: 其他API参数

        Returns:
            聊天完成结果或流式响应

        Raises:
            DeepSeekAPIError: API调用失败
            DeepSeekTimeoutError: 请求超时
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs
            )
            return response

        except openai.APIError as e:
            raise DeepSeekAPIError(f"DeepSeek API错误: {e.message}") from e
        except openai.Timeout as e:
            raise DeepSeekTimeoutError(f"DeepSeek API请求超时: {e}") from e
        except openai.RateLimitError as e:
            raise DeepSeekAPIError(f"DeepSeek API调用频率限制: {e.message}") from e
        except Exception as e:
            raise DeepSeekAPIError(f"DeepSeek API未知错误: {str(e)}") from e

    def complete_text(
        self,
        system_prompt: str,
        user_input: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """同步文本完成

        Args:
            system_prompt: 系统提示词
            user_input: 用户输入
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            包含生成结果和统计信息的字典
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]

        response = self.create_chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            **kwargs
        )

        # 提取结果
        content = response.choices[0].message.content or ""
        usage = response.usage

        return {
            "content": content,
            "usage": {
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0
            },
            "model": response.model,
            "finish_reason": response.choices[0].finish_reason
        }

    def stream_complete_text(
        self,
        system_prompt: str,
        user_input: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Generator[Dict[str, Any], None, None]:
        """流式文本完成

        Args:
            system_prompt: 系统提示词
            user_input: 用户输入
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Yields:
            流式响应数据块
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]

        response_stream = self.create_chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            **kwargs
        )

        try:
            for chunk in response_stream:
                if chunk.choices:
                    delta = chunk.choices[0].delta
                    if delta.content:
                        yield {
                            "type": "content",
                            "content": delta.content,
                            "model": chunk.model,
                            "timestamp": chunk.created
                        }

                    # 提取使用统计（通常在最后一块）
                    if chunk.usage:
                        yield {
                            "type": "usage",
                            "usage": {
                                "prompt_tokens": chunk.usage.prompt_tokens,
                                "completion_tokens": chunk.usage.completion_tokens,
                                "total_tokens": chunk.usage.total_tokens
                            }
                        }

                    # 检查是否完成
                    if chunk.choices[0].finish_reason:
                        yield {
                            "type": "finish",
                            "finish_reason": chunk.choices[0].finish_reason,
                            "model": chunk.model
                        }
                        break

        except Exception as e:
            yield {
                "type": "error",
                "error": str(e)
            }

    async def acomplete_text(
        self,
        system_prompt: str,
        user_input: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """异步文本完成

        Args:
            system_prompt: 系统提示词
            user_input: 用户输入
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            包含生成结果和统计信息的字典
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.complete_text,
            system_prompt,
            user_input,
            temperature,
            max_tokens,
            kwargs
        )

    async def astream_complete_text(
        self,
        system_prompt: str,
        user_input: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Generator[Dict[str, Any], None, None]:
        """异步流式文本完成

        Args:
            system_prompt: 系统提示词
            user_input: 用户输入
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 其他参数

        Yields:
            流式响应数据块
        """
        loop = asyncio.get_event_loop()

        # 在线程池中执行流式操作
        stream_generator = await loop.run_in_executor(
            None,
            self.stream_complete_text,
            system_prompt,
            user_input,
            temperature,
            max_tokens,
            kwargs
        )

        # 将生成器转换为异步生成器
        for chunk in stream_generator:
            yield chunk

    def validate_connection(self) -> Dict[str, Any]:
        """验证API连接

        Returns:
            连接验证结果
        """
        try:
            # 发送一个简单的测试请求
            response = self.create_chat_completion(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
                temperature=0
            )

            return {
                "status": "success",
                "model": response.model,
                "message": "DeepSeek API连接正常"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "DeepSeek API连接失败"
            }