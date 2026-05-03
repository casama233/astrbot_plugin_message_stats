"""
LLM 发言头衔分析模块

通过调用 AstrBot 的 LLM API（/api/v1/chat），
根据群成员的发言统计数据，使用 LLM 为每个成员生成个性化头衔。

在定时推送排行榜前调用，生成的头衔会嵌入到排行榜图片中。
"""

import json
import re
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field

import aiohttp
from astrbot.api import logger as astrbot_logger

from .models import UserData


# 默认的系统提示词模板（可被WebUI配置覆盖）
DEFAULT_SYSTEM_PROMPT = """你是一个擅长给群成员起有趣头衔的群聊分析师。
请根据以下群成员的发言统计数据，为每个成员生成一个富有创意、幽默且贴合其发言风格的头衔。

要求：
1. 头衔要简短（不超过6个汉字），朗朗上口
2. 结合数据特征（发言总数、排名、活跃天数等）进行创意发挥
3. 风格可以多样：霸气、搞怪、吐槽、中二均可
4. 不要使用侮辱性词汇
5. 对发言最多的前3名给出更夸张、更酷的头衔

请严格按照以下JSON格式返回，不要包含任何其他内容：
```json
{
  "titles": {
    "用户ID_1": "头衔1",
    "用户ID_2": "头衔2"
  }
}
```"""

# 默认的用户数据描述模板
DEFAULT_USER_PROMPT_TEMPLATE = """用户数据：
- 昵称：{nickname}
- 总发言数：{total_messages} 次
- 群内排名：第 {rank} 名
- 活跃天数：{active_days} 天
- 今日发言：{daily_count} 次
- 占比：{percentage:.1f}%
- 最后发言：{last_date}"""


@dataclass
class LLMConfig:
    """LLM 配置

    从插件配置中读取，控制 LLM 的行为。
    """
    enabled: bool = False
    api_base_url: str = "http://localhost:6185"
    api_key: str = ""
    model: str = ""
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    user_prompt_template: str = DEFAULT_USER_PROMPT_TEMPLATE
    timeout: int = 60
    max_retries: int = 2

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMConfig':
        """从字典创建配置"""
        return cls(
            enabled=data.get("llm_enabled", False),
            api_base_url=data.get("llm_api_base_url", "http://localhost:6185"),
            api_key=data.get("llm_api_key", ""),
            model=data.get("llm_model", ""),
            system_prompt=data.get("llm_system_prompt", DEFAULT_SYSTEM_PROMPT),
            user_prompt_template=data.get("llm_user_prompt_template", DEFAULT_USER_PROMPT_TEMPLATE),
            timeout=data.get("llm_timeout", 60),
            max_retries=data.get("llm_max_retries", 2),
        )


class LLMAnalyzer:
    """LLM 发言头衔分析器

    通过 HTTP API 调用 AstrBot 的 LLM 服务，
    根据群成员的发言统计数据生成个性化头衔。

    Attributes:
        config (LLMConfig): LLM 配置
        logger: 日志记录器
        session (Optional[aiohttp.ClientSession]): HTTP 会话
    """

    def __init__(self, config: LLMConfig = None):
        """初始化 LLM 分析器

        Args:
            config (LLMConfig, optional): LLM 配置
        """
        self.config = config or LLMConfig()
        self.logger = astrbot_logger
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建 HTTP 会话

        Returns:
            aiohttp.ClientSession: HTTP 会话
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"Content-Type": "application/json"}
            )
        return self._session

    async def cleanup(self):
        """清理 HTTP 会话资源"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def analyze_users(
        self,
        group_data: List[UserData],
        group_name: str = "",
    ) -> Dict[str, str]:
        """分析群成员数据，生成头衔

        构建描述所有用户的提示词，调用 LLM 批量生成头衔。

        Args:
            group_data (List[UserData]): 群成员数据列表
            group_name (str): 群组名称

        Returns:
            Dict[str, str]: 用户 ID 到头衔的映射字典
        """
        if not self.config.enabled or not group_data:
            return {}

        # 过滤掉 0 发言的用户
        active_users = [u for u in group_data if u.message_count > 0]
        if not active_users:
            return {}

        # 按发言数降序排序
        sorted_users = sorted(active_users, key=lambda x: x.message_count, reverse=True)

        # 构建用户数据描述
        user_descriptions = []
        for rank, user in enumerate(sorted_users, 1):
            # 计算活跃天数和今日发言
            active_days = 0
            daily_count = 0
            percentage = 0.0
            last_date = user.last_date or "未知"

            if hasattr(user, '_message_dates') and user._message_dates:
                active_days = len(user._message_dates)
                # 获取今日发言
                from datetime import date
                today_str = str(date.today())
                daily_count = user._message_dates.get(today_str, 0)

            # 计算占比
            total_all = sum(u.message_count for u in active_users)
            if total_all > 0:
                percentage = (user.message_count / total_all) * 100

            desc = self.config.user_prompt_template.format(
                nickname=user.nickname or f"用户{user.user_id}",
                total_messages=user.message_count,
                rank=rank,
                active_days=active_days,
                daily_count=daily_count,
                percentage=percentage,
                last_date=last_date,
            )
            user_descriptions.append(desc)

        # 构建完整提示词
        # 如果配置了 system_prompt，将其作为前置指令
        user_prompt = (
            f"以下是「{group_name}」群聊的群成员发言统计数据：\n\n"
            + "\n".join(user_descriptions)
            + "\n\n请为这些群成员生成头衔。"
        )
        
        if self.config.system_prompt and self.config.system_prompt.strip():
            full_prompt = self.config.system_prompt.strip() + "\n\n" + user_prompt
        else:
            full_prompt = user_prompt

        # 调用 LLM 并重试
        last_error = None
        for attempt in range(1 + self.config.max_retries):
            try:
                result = await self._call_llm_api(full_prompt)
                if result:
                    # 解析返回的 JSON
                    titles = self._parse_titles(result, sorted_users)
                    if titles:
                        self.logger.info(
                            f"✅ LLM 头衔生成成功: 为 {len(titles)}/{len(sorted_users)} 个用户生成了头衔"
                        )
                        return titles
                    else:
                        self.logger.warning(f"⚠️ LLM 返回的数据解析失败，尝试第 {attempt + 1} 次重试")
                else:
                    self.logger.warning(f"⚠️ LLM 返回为空，尝试第 {attempt + 1} 次重试")
            except (aiohttp.ClientError, asyncio.TimeoutError, json.JSONDecodeError) as e:
                last_error = e
                self.logger.warning(
                    f"⚠️ LLM API 调用失败(第{attempt + 1}次): {e}"
                )
                if attempt < self.config.max_retries:
                    await asyncio.sleep(2 * (attempt + 1))

        if last_error:
            self.logger.error(f"❌ LLM 头衔生成失败(已重试{self.config.max_retries}次): {last_error}")
        else:
            self.logger.error("❌ LLM 头衔生成失败: 无法解析返回值")
        return {}

    async def _call_llm_api(self, prompt: str) -> Optional[str]:
        """调用 AstrBot LLM API

        向 /api/v1/chat 发送 POST 请求，获取流式响应并拼接返回。

        Args:
            prompt (str): 发送给 LLM 的提示词

        Returns:
            Optional[str]: LLM 返回的文本内容
        """
        session = await self._get_session()
        api_url = f"{self.config.api_base_url.rstrip('/')}/api/v1/chat"

        # 构建请求体
        payload: Dict[str, Any] = {
            "message": prompt,
            "username": "message_stats_plugin",
            "session_id": "llm_title_generation",
            "enable_streaming": True,
        }

        # 如果配置了模型，指定模型
        if self.config.model:
            payload["selected_model"] = self.config.model

        # 构建请求头
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["X-API-Key"] = self.config.api_key

        self.logger.debug(f"调用 LLM API: {api_url}")

        try:
            async with session.post(
                api_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.logger.error(
                        f"LLM API 返回错误状态码 {response.status}: {error_text[:200]}"
                    )
                    return None

                # 处理 SSE 流式响应
                collected_text = []
                async for line in response.content:
                    decoded_line = line.decode("utf-8", errors="replace").strip()
                    if not decoded_line:
                        continue
                    # SSE 格式: "data: {json}"
                    if decoded_line.startswith("data: "):
                        data_str = decoded_line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data_obj = json.loads(data_str)
                            # 从响应中提取文本内容
                            content = data_obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                collected_text.append(content)
                        except (json.JSONDecodeError, KeyError, IndexError):
                            # 尝试直接提取文本
                            if isinstance(data_str, str):
                                collected_text.append(data_str)

                full_text = "".join(collected_text).strip()
                if full_text:
                    return full_text

                self.logger.warning("LLM 返回的 SSE 流中没有提取到有效文本内容")
                return None

        except aiohttp.ClientConnectorError as e:
            self.logger.error(f"无法连接到 LLM API ({api_url}): {e}")
            self.logger.info("💡 请确保 AstrBot 已启动，且 API 地址配置正确")
            return None
        except asyncio.TimeoutError:
            self.logger.error(f"LLM API 请求超时 ({self.config.timeout}秒)")
            return None
        except aiohttp.ClientError as e:
            self.logger.error(f"LLM API 请求失败: {e}")
            return None

    def _parse_titles(
        self,
        llm_response: str,
        sorted_users: List[UserData],
    ) -> Dict[str, str]:
        """解析 LLM 返回的 JSON，提取头衔

        支持多种 JSON 格式：
        - {"titles": {"user_id": "头衔", ...}}
        - {"用户ID": "头衔", ...}
        - 列表格式: [{"user_id": "...", "title": "..."}, ...]

        Args:
            llm_response (str): LLM 返回的文本
            sorted_users (List[UserData]): 排序后的用户列表

        Returns:
            Dict[str, str]: 用户 ID 到头衔的映射
        """
        # 尝试提取 JSON 块（可能在 ```json ... ``` 中）
        json_str = llm_response
        json_pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
        json_match = re.search(json_pattern, llm_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()

        # 尝试解析 JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            # 尝试查找第一个 { 和最后一个 }
            brace_start = llm_response.find("{")
            brace_end = llm_response.rfind("}")
            if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
                try:
                    data = json.loads(llm_response[brace_start : brace_end + 1])
                except json.JSONDecodeError:
                    self.logger.error("无法从 LLM 返回中解析 JSON")
                    self.logger.debug(f"LLM 原始返回: {llm_response[:500]}")
                    return {}
            else:
                self.logger.error("LLM 返回中未找到 JSON 结构")
                return {}

        if not isinstance(data, dict):
            self.logger.error(f"LLM 返回数据格式错误: 期望 dict, 得到 {type(data)}")
            return {}

        # 从嵌套的 titles 字段提取
        titles_raw = data.get("titles", data)
        if not isinstance(titles_raw, dict):
            self.logger.error(f"titles 字段格式错误: 期望 dict, 得到 {type(titles_raw)}")
            return {}

        # 验证并过滤头衔
        result = {}
        for user_id, title in titles_raw.items():
            if not isinstance(title, str) or not title.strip():
                continue
            # 清理头衔：移除多余符号
            clean_title = title.strip().strip('"').strip("'").strip("【】").strip("「」")
            if clean_title:
                result[str(user_id)] = clean_title

        # 如果没有匹配到任何用户，尝试用数字索引（排名）匹配
        if not result and titles_raw:
            keys = list(titles_raw.keys())
            # 检查 key 是否是数字（排名）
            all_numeric = all(k.lstrip('-').isdigit() for k in keys if k)
            if all_numeric and sorted_users:
                for i, user in enumerate(sorted_users):
                    rank_key = str(i + 1)
                    if rank_key in titles_raw:
                        title = titles_raw[rank_key]
                        if isinstance(title, str) and title.strip():
                            result[user.user_id] = title.strip().strip('"')

        return result
