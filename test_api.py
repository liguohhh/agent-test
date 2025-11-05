"""
API测试脚本

用于测试AI应用后端接口的基本功能
"""

import asyncio
import json
import time
from typing import Dict, Any

import httpx


class APITester:
    """API测试类"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)

    def test_health(self) -> bool:
        """测试健康检查"""
        try:
            response = self.client.get(f"{self.base_url}/api/health")
            print(f"健康检查: {response.status_code}")
            if response.status_code == 200:
                print(f"响应: {response.json()}")
                return True
            else:
                print(f"错误: {response.text}")
                return False
        except Exception as e:
            print(f"健康检查失败: {e}")
            return False

    def test_functions(self) -> bool:
        """测试功能列表"""
        try:
            response = self.client.get(f"{self.base_url}/api/functions")
            print(f"功能列表: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"可用功能数量: {len(data.get('data', []))}")
                for func in data.get('data', []):
                    print(f"  - {func['id']}: {func['name']}")
                return True
            else:
                print(f"错误: {response.text}")
                return False
        except Exception as e:
            print(f"功能列表测试失败: {e}")
            return False

    def test_translation(self) -> bool:
        """测试翻译功能"""
        try:
            # 中译英测试
            request_data = {
                "function_id": "translation_zh_to_en",
                "input": {"text": "你好，世界！这是一个测试。"},
                "use_cache": False
            }

            response = self.client.post(
                f"{self.base_url}/api/execute",
                json=request_data
            )
            print(f"中译英翻译: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"原文: 你好，世界！这是一个测试。")
                print(f"译文: {data.get('data', {}).get('result', {}).get('content', '')}")
                print(f"执行时间: {data.get('data', {}).get('execution_time', 0):.2f}秒")
                print(f"Token使用: {data.get('data', {}).get('usage', {})}")
                return True
            else:
                print(f"翻译失败: {response.text}")
                return False
        except Exception as e:
            print(f"翻译功能测试失败: {e}")
            return False

    def test_summary(self) -> bool:
        """测试总结功能"""
        try:
            # 文本总结测试
            long_text = """
            人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，它试图创建能够执行通常需要人类智能的任务的机器。
            这些任务包括学习、推理、问题解决、感知和语言理解。AI技术在过去几十年中取得了显著进展，
            特别是在机器学习、深度学习、自然语言处理和计算机视觉等领域。现代AI系统能够在各种应用中发挥作用，
            包括自动驾驶汽车、语音识别、图像分析、医疗诊断和推荐系统等。然而，AI的发展也带来了一些挑战和争议，
            包括隐私问题、就业影响、算法偏见和安全风险等。
            """

            request_data = {
                "function_id": "text_summary",
                "input": {
                    "text": long_text,
                    "summary_length": "short"
                },
                "use_cache": False
            }

            response = self.client.post(
                f"{self.base_url}/api/execute",
                json=request_data
            )
            print(f"文本总结: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"总结结果: {data.get('data', {}).get('result', {}).get('content', '')}")
                return True
            else:
                print(f"总结失败: {response.text}")
                return False
        except Exception as e:
            print(f"总结功能测试失败: {e}")
            return False

    def test_stream(self) -> bool:
        """测试流式响应"""
        try:
            request_data = {
                "function_id": "translation_zh_to_en",
                "input": {"text": "这是一个流式响应测试。"},
                "use_cache": False
            }

            with self.client.stream(
                "POST",
                f"{self.base_url}/api/stream",
                json=request_data
            ) as response:
                print(f"流式响应: {response.status_code}")

                if response.status_code == 200:
                    content_parts = []
                    for line in response.iter_lines():
                        if line.startswith(b"data: "):
                            try:
                                data = json.loads(line[6:].decode('utf-8'))
                                if data.get("type") == "token":
                                    content_parts.append(data.get("content", ""))
                                    print(f"收到token: {data.get('content', '')}")
                                elif data.get("type") == "end":
                                    print("流式响应结束")
                                    break
                                elif data.get("type") == "error":
                                    print(f"流式响应错误: {data.get('message', '')}")
                                    return False
                            except json.JSONDecodeError:
                                continue

                    full_content = "".join(content_parts)
                    print(f"完整内容: {full_content}")
                    return True
                else:
                    print(f"流式响应失败: {response.text}")
                    return False
        except Exception as e:
            print(f"流式响应测试失败: {e}")
            return False

    def test_stats(self) -> bool:
        """测试统计信息"""
        try:
            response = self.client.get(f"{self.base_url}/api/stats")
            print(f"统计信息: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"缓存统计: {json.dumps(data.get('cache', {}), indent=2, ensure_ascii=False)}")
                print(f"流式统计: {json.dumps(data.get('streaming', {}), indent=2, ensure_ascii=False)}")
                return True
            else:
                print(f"获取统计信息失败: {response.text}")
                return False
        except Exception as e:
            print(f"统计信息测试失败: {e}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 50)
        print("开始API功能测试")
        print("=" * 50)

        tests = [
            ("健康检查", self.test_health),
            ("功能列表", self.test_functions),
            ("中译英翻译", self.test_translation),
            ("文本总结", self.test_summary),
            ("流式响应", self.test_stream),
            ("统计信息", self.test_stats),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            print(f"\n{'-' * 20} {test_name} {'-' * 20}")
            try:
                if test_func():
                    print(f"✅ {test_name} 测试通过")
                    passed += 1
                else:
                    print(f"❌ {test_name} 测试失败")
            except Exception as e:
                print(f"❌ {test_name} 测试异常: {e}")
            time.sleep(1)  # 避免请求过快

        print("\n" + "=" * 50)
        print(f"测试完成: {passed}/{total} 通过")
        print("=" * 50)

        return passed == total


def main():
    """主函数"""
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    print(f"测试目标: {base_url}")

    tester = APITester(base_url)
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()