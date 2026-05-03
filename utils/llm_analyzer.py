"""
LLM 发言头衔分析模块

通过 AstrBot 内置的 Provider 系统调用 LLM，
根据群成员的发言统计数据，使用 LLM 为每个成员生成个性化头衔。

在定时推送排行榜前调用，生成的头衔会嵌入到排行榜图片中。
"""

import json
import re
import asyncio
from typing import List, Dict, Any, Optional

from astrbot.api import logger as astrbot_logger

from .models import UserData


# 默认的系统提示词
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


class LLMAnalyzer:
    """LLM 发言头衔分析器

    通过 AstrBot 内置 Provider 系统调用 LLM，
    根据群成员的发言统计数据生成个性化头衔。

    Attributes:
        context: AstrBot上下文对象
        provider_id (str): 指定的 LLM Provider ID（为空则使用默认）
        system_prompt (str): 系统提示词
        max_retries (int): 重试次数
        logger: 日志记录器
    """

    def __init__(
        self,
        context,
        provider_id: str = "",
        system_prompt: str = "",
        max_retries: int = 2,
    ):
        """初始化 LLM 分析器

        Args:
            context: AstrBot上下文对象
            provider_id (str): Provider ID，留空则使用默认
            system_prompt (str): 系统提示词，留空使用默认
            max_retries (int): 重试次数
        """
        self.context = context
        self.provider_id = provider_id
        self.system_prompt = system_prompt.strip() or DEFAULT_SYSTEM_PROMPT
        self.max_retries = max_retries
        self.logger = astrbot_logger

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
        if not group_data:
            return {}

        # 过滤掉 0 发言的用户
        active_users = [u for u in group_data if u.message_count > 0]
        if not active_users:
            return {}

        # 按发言数降序排序
        sorted_users = sorted(active_users, key=lambda x: x.message_count, reverse=True)

        # 构建用户数据描述
        user_descriptions = []
        total_all = sum(u.message_count for u in active_users)
        for rank, user in enumerate(sorted_users, 1):
            active_days = len(user._message_dates) if hasattr(user, '_message_dates') and user._message_dates else 0
            percentage = (user.message_count / total_all * 100) if total_all > 0 else 0
            last_date = user.last_date or "未知"

            desc = (
                f"用户数据：\n"
                f"- 昵称：{user.nickname or f'用户{user.user_id}'}\n"
                f"- 总发言数：{user.message_count} 次\n"
                f"- 群内排名：第 {rank} 名\n"
                f"- 活跃天数：{active_days} 天\n"
                f"- 占比：{percentage:.1f}%\n"
                f"- 最后发言：{last_date}"
            )
            user_descriptions.append(desc)

        # 构建完整提示词
        prompt = (
            f"以下是「{group_name}」群聊的群成员发言统计数据：\n\n"
            + "\n\n".join(user_descriptions)
            + "\n\n请为这些群成员生成头衔。"
        )

        # 调用 LLM 并重试
        last_error = None
        for attempt in range(1 + self.max_retries):
            try:
                result = await self._call_llm(prompt)
                if result:
                    titles = self._parse_titles(result, sorted_users)
                    if titles:
                        self.logger.info(
                            f"✅ LLM 头衔生成成功: 为 {len(titles)}/{len(sorted_users)} 个用户生成了头衔"
                        )
                        return titles
                    else:
                        self.logger.warning(f"⚠️ LLM 返回解析失败，尝试第 {attempt + 1} 次")
                else:
                    self.logger.warning(f"⚠️ LLM 返回为空，尝试第 {attempt + 1} 次")
            except Exception as e:
                last_error = e
                self.logger.warning(f"⚠️ LLM 调用失败(第{attempt + 1}次): {e}")
                if attempt < self.max_retries:
                    await asyncio.sleep(2 * (attempt + 1))

        if last_error:
            self.logger.error(f"❌ LLM 头衔生成失败(已重试{self.max_retries}次): {last_error}")
        else:
            self.logger.error("❌ LLM 头衔生成失败: 无法解析返回值")
        return {}

    async def _call_llm(self, prompt: str) -> Optional[str]:
        """通过 AstrBot Provider 调用 LLM

        使用 context.llm_generate() 调用 AstrBot 已配置的 LLM。

        Args:
            prompt (str): 发送给 LLM 的提示词

        Returns:
            Optional[str]: LLM 返回的文本内容
        """
        try:
            llm_kwargs = {
                "prompt": prompt,
                "system_prompt": self.system_prompt,
            }

            # 如果指定了 Provider ID，尝试使用
            if self.provider_id and self.provider_id.strip():
                try:
                    provider = self.context.get_provider_by_id(
                        provider_id=self.provider_id.strip()
                    )
                    if provider:
                        llm_kwargs["chat_provider_id"] = self.provider_id.strip()
                        self.logger.info(f"使用指定 Provider: {self.provider_id}")
                    else:
                        self.logger.warning(
                            f"指定的 Provider '{self.provider_id}' 不存在，使用默认 Provider"
                        )
                except Exception as e:
                    self.logger.warning(
                        f"获取 Provider '{self.provider_id}' 失败: {e}，使用默认 Provider"
                    )

            self.logger.debug("调用 LLM generate...")
            resp = await self.context.llm_generate(**llm_kwargs)

            if resp is None:
                self.logger.warning("LLM 返回 None")
                return None

            # 从响应中提取文本
            if hasattr(resp, "completion_text"):
                text = resp.completion_text
            elif hasattr(resp, "text"):
                text = resp.text
            elif isinstance(resp, str):
                text = resp
            else:
                text = str(resp)

            text = text.strip()
            if text:
                return text

            self.logger.warning("LLM 返回文本为空")
            return None

        except Exception as e:
            self.logger.error(f"LLM 调用异常: {e}")
            raise

    def _parse_titles(
        self,
        llm_response: str,
        sorted_users: List[UserData],
    ) -> Dict[str, str]:
        """解析 LLM 返回的 JSON，提取头衔

        支持多种 JSON 格式：
        - {"titles": {"user_id": "头衔", ...}}
        - {"用户ID": "头衔", ...}

        Args:
            llm_response (str): LLM 返回的文本
            sorted_users (List[UserData]): 排序后的用户列表

        Returns:
            Dict[str, str]: 用户 ID 到头衔的映射
        """
        json_str = llm_response
        json_pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
        json_match = re.search(json_pattern, llm_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
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

        titles_raw = data.get("titles", data)
        if not isinstance(titles_raw, dict):
            self.logger.error(f"titles 字段格式错误: 期望 dict, 得到 {type(titles_raw)}")
            return {}

        result = {}
        for user_id, title in titles_raw.items():
            if not isinstance(title, str) or not title.strip():
                continue
            clean_title = title.strip().strip('"').strip("'").strip("【】").strip("「」")
            if clean_title:
                result[str(user_id)] = clean_title

        # 尝试用排名匹配（如果 LLM 返回的是按排名顺序）
        if not result and titles_raw:
            keys = list(titles_raw.keys())
            all_numeric = all(k.lstrip('-').isdigit() for k in keys if k)
            if all_numeric and sorted_users:
                for i, user in enumerate(sorted_users):
                    rank_key = str(i + 1)
                    if rank_key in titles_raw:
                        title = titles_raw[rank_key]
                        if isinstance(title, str) and title.strip():
                            result[user.user_id] = title.strip().strip('"')

        return result
