"""
数据模型定义
定义插件中使用的所有数据结构

此模块仅包含数据模型的定义，不包含业务逻辑或工具函数。
工具函数已拆分到独立的模块中：
- file_utils: 文件操作工具
- date_utils: 日期时间处理工具
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from enum import Enum

# 使用框架的日志记录器
from astrbot.api import logger



class RankType(Enum):
    """排行榜类型枚举
    
    定义了插件支持的排行榜类型，包括总榜、日榜、周榜、月榜、年榜和去年榜。
    
    Attributes:
        TOTAL (str): 总排行榜，包含历史所有发言统计
        DAILY (str): 日排行榜，仅包含当日发言统计
        WEEKLY (str): 周排行榜，仅包含本周发言统计
        MONTHLY (str): 月排行榜，仅包含本月发言统计
        YEARLY (str): 年排行榜，仅包含本年发言统计
        LAST_YEAR (str): 去年排行榜，仅包含去年全年发言统计
        
    Example:
        >>> rank_type = RankType.TOTAL
        >>> print(rank_type.value)
        'total'
    """
    TOTAL = "total"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    LAST_YEAR = "lastyear"


@dataclass
class MessageDate:
    """消息日期记录
    
    用于记录消息的日期信息，支持与标准date对象的相互转换。
    提供完整的比较和格式化功能。
    
    Attributes:
        year (int): 年份
        month (int): 月份
        day (int): 日期
        
    Methods:
        to_date(): 转换为标准date对象
        to_datetime(): 转换为标准datetime对象
        from_date(): 从date对象创建实例
        from_datetime(): 从datetime对象创建实例
        
    Example:
        >>> msg_date = MessageDate(2024, 1, 15)
        >>> print(msg_date.to_date())
        datetime.date(2024, 1, 15)
    """
    year: int
    month: int
    day: int
    
    def to_date(self) -> date:
        """转换为date对象
        
        将MessageDate实例转换为Python标准库中的date对象。
        
        Returns:
            date: 标准date对象，年月日信息相同
            
        Example:
            >>> msg_date = MessageDate(2024, 1, 15)
            >>> date_obj = msg_date.to_date()
            >>> print(type(date_obj))
            <class 'datetime.date'>
        """
        return date(self.year, self.month, self.day)
    
    def to_datetime(self) -> datetime:
        """转换为datetime对象
        
        将MessageDate实例转换为Python标准库中的datetime对象。
        时间部分将设置为00:00:00。
        
        Returns:
            datetime: 标准datetime对象，时间部分为00:00:00
            
        Example:
            >>> msg_date = MessageDate(2024, 1, 15)
            >>> dt = msg_date.to_datetime()
            >>> print(dt.time())
            00:00:00
        """
        return datetime.combine(self.to_date(), datetime.min.time())
    
    @classmethod
    def from_date(cls, date_obj: date):
        """从date对象创建
        
        从Python标准库中的date对象创建MessageDate实例。
        
        Args:
            date_obj (date): 标准date对象
            
        Returns:
            MessageDate: 对应的MessageDate实例
            
        Example:
            >>> from datetime import date
            >>> d = date(2024, 1, 15)
            >>> msg_date = MessageDate.from_date(d)
            >>> print(msg_date.year)
            2024
        """
        return cls(date_obj.year, date_obj.month, date_obj.day)
    
    @classmethod
    def from_datetime(cls, datetime_obj: datetime):
        """从datetime对象创建
        
        从Python标准库中的datetime对象创建MessageDate实例。
        只使用日期部分，忽略时间部分。
        
        Args:
            datetime_obj (datetime): 标准datetime对象
            
        Returns:
            MessageDate: 对应的MessageDate实例
            
        Example:
            >>> from datetime import datetime
            >>> dt = datetime(2024, 1, 15, 14, 30, 0)
            >>> msg_date = MessageDate.from_datetime(dt)
            >>> print(msg_date)
            2024-01-15
        """
        return cls.from_date(datetime_obj.date())
    
    def __str__(self) -> str:
        return f"{self.year}-{self.month:02d}-{self.day:02d}"
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, MessageDate):
            return NotImplemented
        return (self.year == other.year and 
                self.month == other.month and 
                self.day == other.day)
    
    def __lt__(self, other) -> bool:
        if not isinstance(other, MessageDate):
            return NotImplemented
        return (self.year, self.month, self.day) < (other.year, other.month, other.day)


@dataclass
class UserData:
    """用户数据
    
    存储用户在群组中的发言统计数据，包括用户信息、发言总数和历史记录。
    支持数据序列化和反序列化，便于JSON存储。
    
    Attributes:
        user_id (str): 用户唯一标识符
        nickname (str): 用户昵称
        message_count (int): 总发言次数，默认为0
        history (List[MessageDate]): 发言日期历史记录列表
        last_date (Optional[str]): 最后发言日期的字符串表示
        first_message_time (Optional[int]): 首次发言时间戳
        last_message_time (Optional[int]): 最后发言时间戳
        
    Methods:
        add_message(): 添加新的消息记录
        get_last_message_date(): 获取最后发言日期
        get_message_count_in_period(): 获取指定时间段内的发言数量
        to_dict(): 转换为字典格式
        from_dict(): 从字典创建实例
        
    Example:
        >>> user = UserData("123456", "用户昵称")
        >>> user.add_message(MessageDate(2024, 1, 15))
        >>> print(user.message_count)
        1
    """
    user_id: str
    nickname: str
    message_count: int = 0
    history: List[MessageDate] = field(default_factory=list)
    last_date: Optional[str] = None
    first_message_time: Optional[int] = None
    last_message_time: Optional[int] = None
    # 按天聚合的字典 {date_str: count}，替代 history 列表存储
    # 10万条消息最多365个键值对，内存占用从O(n)降到O(365)
    _message_dates: Dict[str, int] = field(default_factory=dict)
    # LLM 生成的头衔文本（持久化到文件）
    display_title: Optional[str] = None
    # LLM 生成的头衔颜色（运行时属性），如 "#EF4444"
    display_title_color: Optional[str] = None
    # 时间段内的发言数（运行时属性，仅用于图片生成）
    display_total: Optional[int] = None


    
    def add_message(self, message_date: MessageDate):
        """添加消息记录
        
        增加用户的发言计数并记录发言日期。使用按天聚合的字典存储，
        避免 history 列表无限增长导致内存泄漏。
        
        Args:
            message_date (MessageDate): 消息日期对象
            
        Returns:
            None: 无返回值，直接修改对象状态
        """
        self.message_count += 1
        
        # 使用按天聚合的字典存储，每天只存一个 {date_str: count}
        # 10万条消息最多365个键值对，内存占用从O(n)降到O(365)
        date_str = str(message_date)
        if date_str not in self._message_dates:
            self._message_dates[date_str] = 0
        self._message_dates[date_str] += 1
        
        # 更新最后发言日期
        self.last_date = date_str
    
    def get_last_message_date(self) -> Optional[MessageDate]:
        """获取最后消息日期
        
        返回用户最后一次发言的日期，如果无发言记录则返回None。
        
        Returns:
            Optional[MessageDate]: 最后发言日期，如果无记录则返回None
        """
        if not self._message_dates:
            return None
        # 取最后一条记录的日期
        last_date_str = max(self._message_dates.keys())
        year, month, day = map(int, last_date_str.split('-'))
        return MessageDate(year, month, day)
    
    def _ensure_message_dates(self):
        """确保 _message_dates 数据完整
        
        兜底保护：如果 _message_dates 为空但 message_count > 0，
        说明数据可能有问题，尝试从 history 列表重建。
        这通常只会在旧数据升级后第一次加载时触发。
        """
        if not self._message_dates and self.message_count > 0 and self.history:
            try:
                for h in self.history:
                    date_str = str(h)
                    self._message_dates[date_str] = self._message_dates.get(date_str, 0) + 1
            except Exception:
                pass  # 重建失败不影响主功能
    
    def get_message_count_in_period(self, start_date: date, end_date: date) -> int:
        """获取指定时间段内的消息数量
        
        使用按天聚合的字典 O(1) 查询，比遍历 history 列表 O(n) 快得多。
        内置兜底保护：如果字典为空但 message_count > 0，自动从 history 重建。
        
        Args:
            start_date (date): 开始日期（包含）
            end_date (date): 结束日期（包含）
            
        Returns:
            int: 指定时间段内的发言次数
        """
        # 兜底保护：确保 _message_dates 数据完整
        self._ensure_message_dates()
        
        count = 0
        start_str = str(start_date)
        end_str = str(end_date)
        for date_str, day_count in self._message_dates.items():
            if start_str <= date_str <= end_str:
                count += day_count
        return count
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        将UserData实例转换为字典格式，便于JSON序列化。
        使用按天聚合的字典存储，大幅减少JSON文件体积。
        
        Returns:
            Dict[str, Any]: 包含用户数据的字典
        """
        result = {
            "user_id": self.user_id,
            "nickname": self.nickname,
            "message_count": self.message_count,
            "history": [f"{date_str}:{count}" for date_str, count in sorted(self._message_dates.items())],
            "last_date": self.last_date,
            "first_message_time": self.first_message_time,
            "last_message_time": self.last_message_time
        }
        if self.display_title:
            result["display_title"] = self.display_title
            if self.display_title_color:
                result["display_title_color"] = self.display_title_color
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserData':
        """从字典创建
        
        从字典数据创建UserData实例，自动重建发言历史记录。
        兼容新旧两种格式：
        - 新格式: ["2024-01-15:3", "2024-01-16:5"] (按天聚合)
        - 旧格式: ["2024-01-15", "2024-01-15", "2024-01-15"] (逐条记录)
        
        Args:
            data (Dict[str, Any]): 用户数据字典
            
        Returns:
            UserData: 对应的UserData实例
        """
        user_data = cls(
            user_id=data["user_id"],
            nickname=data["nickname"],
            message_count=data.get("message_count", 0),
            last_date=data.get("last_date"),
            first_message_time=data.get("first_message_time"),
            last_message_time=data.get("last_message_time")
        )
        
        # 恢复持久化的头衔
        if "display_title" in data:
            user_data.display_title = data["display_title"]
            if "display_title_color" in data:
                user_data.display_title_color = data["display_title_color"]
        
        # 重建 _message_dates（兼容新旧格式）
        if "history" in data:
            try:
                for hist_str in data["history"]:
                    try:
                        # 新格式: "2024-01-15:3"
                        if ':' in hist_str:
                            date_part, count_part = hist_str.rsplit(':', 1)
                            year, month, day = map(int, date_part.split('-'))
                            count = int(count_part)
                            user_data._message_dates[date_part] = count
                        else:
                            # 旧格式: "2024-01-15" (逐条)
                            year, month, day = map(int, hist_str.split('-'))
                            date_str = hist_str
                            if date_str not in user_data._message_dates:
                                user_data._message_dates[date_str] = 0
                            user_data._message_dates[date_str] += 1
                    except (ValueError, IndexError) as e:
                        logger.warning(f"跳过格式错误的日期记录 '{hist_str}': {e}")
                        continue
            except TypeError as e:
                logger.warning(f"history字段类型错误: {type(data.get('history'))}, 错误: {e}")
        
        return user_data
    
    def __lt__(self, other) -> bool:
        """按总消息数排序"""
        if not isinstance(other, UserData):
            return NotImplemented
        return self.message_count < other.message_count  # 升序排列，用于sorted()函数


class PluginConfig:
    """插件基本配置
    
    存储插件的基本配置参数，包括显示设置、权限控制和日志管理。
    支持数据序列化和反序列化，便于配置文件的读写。
    
    Attributes:
        theme (str): 排行榜主题风格，支持 'default'（经典浅色）、'liquid_glass'（液态玻璃）、'liquid_glass_dark'（液态玻璃暗色）
        auto_theme_switch (bool): 是否根据时间自动切换主题
        theme_switch_times (dict): 自动切换主题的时间配置，如 {"light": "06:00", "dark": "18:00"}
        is_admin_restricted (int): 是否限制管理员操作，0为不限制，1为限制
        rand (int): 排行榜显示人数，默认为20人
        if_send_pic (int): 是否发送图片，0为文字模式，1为图片模式（与Web Schema一致）
        detailed_logging_enabled (bool): 是否开启详细日志记录，关闭后隐藏"记录消息统计"等详细日志
        timer_enabled (bool): 是否启用定时推送功能
        timer_push_time (str): 定时推送时间（支持HH:MM或cron格式，如"09:00"或"0 9 * * *"）
        timer_target_groups (List[str]): 定时推送目标群组ID列表
        timer_rank_type (str): 定时推送的排行榜类型
        
    Methods:
        to_dict(): 转换为字典格式
        from_dict(): 从字典创建实例
        
    Example:
        >>> config = PluginConfig()
        >>> config.rand = 15
        >>> config.detailed_logging_enabled = False  # 隐藏详细日志
    """
    def __init__(self):
        self.theme = "default"  # 排行榜主题风格: default, liquid_glass, liquid_glass_dark
        self.auto_theme_switch = False  # 是否根据时间自动切换主题
        self.theme_switch_times = {"light": "06:00", "dark": "18:00"}  # 浅色/深色主题切换时间
        self.is_admin_restricted = 0
        self.rand = 20
        self.if_send_pic = 1
        self.detailed_logging_enabled = True  # 默认开启详细日志，便于调试
        
        # 定时功能配置
        self.timer_enabled = False
        self.timer_push_time = "09:00"
        self.timer_target_groups = []
        self.timer_rank_type = "daily"  # 默认推送今日排行榜
        
        # 屏蔽用户列表
        self.blocked_users = []
        
        # 屏蔽群聊列表
        self.blocked_groups = []
        
        # 发言里程碑推送配置
        self.milestone_enabled = False
        self.milestone_targets = [666, 1000, 2333, 5000, 6666, 10000, 23333]
        
        # LLM 头衔分析配置
        self.llm_enabled = False
        self.llm_provider_id = ""
        self.llm_system_prompt = ""
        self.llm_max_retries = 2
        self.llm_min_daily_messages = 0
        self.llm_enable_on_manual = False
        # 提示词版本号，版本升级时自动覆写
        self.llm_prompt_version = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        将PluginConfig实例转换为字典格式，便于JSON序列化。
        与Web Schema保持一致的字段名，确保配置能够正确加载。
        
        Returns:
            Dict[str, Any]: 包含所有配置数据的字典，包括：
                - is_admin_restricted: 管理员限制设置
                - rand: 排行榜显示人数
                - if_send_pic: 图片模式设置（与Schema一致）
                - timer_enabled: 定时功能开关
                - timer_push_time: 定时推送时间
                - timer_target_groups: 定时推送群组
                - timer_rank_type: 定时推送排行榜类型
                
        Example:
            >>> config = PluginConfig()
            >>> data = config.to_dict()
            >>> print(data['rand'])
            20
        """
        return {
            "theme": self.theme,
            "auto_theme_switch": self.auto_theme_switch,
            "theme_switch_light_time": self.theme_switch_times.get("light", "06:00"),
            "theme_switch_dark_time": self.theme_switch_times.get("dark", "18:00"),
            "is_admin_restricted": self.is_admin_restricted,
            "rand": self.rand,
            "if_send_pic": self.if_send_pic,
            "detailed_logging_enabled": self.detailed_logging_enabled,
            "timer_enabled": self.timer_enabled,
            "timer_push_time": self.timer_push_time,
            "timer_target_groups": self.timer_target_groups,
            "timer_rank_type": self.timer_rank_type,
            "blocked_users": self.blocked_users,
            "blocked_groups": self.blocked_groups,
            "milestone_enabled": self.milestone_enabled,
            "milestone_targets": self.milestone_targets,
            "llm_enabled": self.llm_enabled,
            "llm_provider_id": self.llm_provider_id,
            "llm_system_prompt": self.llm_system_prompt,
            "llm_max_retries": self.llm_max_retries,
            "llm_min_daily_messages": self.llm_min_daily_messages,
            "llm_enable_on_manual": self.llm_enable_on_manual,
            "llm_prompt_version": self.llm_prompt_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginConfig':
        """从字典创建基本配置
        
        从字典数据创建PluginConfig实例，使用默认值填充缺失字段。
        支持字段名映射，兼容旧版本配置格式。
        
        Args:
            data (Dict[str, Any]): 配置数据字典，可能包含：
                - is_admin_restricted: 管理员限制设置
                - rand: 排行榜显示人数
                - if_send_pic: 图片模式设置（标准字段）
                - send_pic: 图片模式设置（旧版本字段，兼容）
                - timer_enabled: 定时功能开关
                - timer_push_time: 定时推送时间
                - timer_target_groups: 定时推送群组
                - timer_rank_type: 定时推送排行榜类型
            
        Returns:
            PluginConfig: 对应的PluginConfig实例
            
        Example:
            >>> data = {"rand": 15, "if_send_pic": 0}
            >>> config = PluginConfig.from_dict(data)
            >>> print(config.rand)
            15
        """
        # 创建默认实例
        config = cls()
        
        # 支持字段名映射 - if_send_pic是标准字段，send_pic是兼容字段
        if_send_pic_raw = data.get("if_send_pic", data.get("send_pic", "图片"))
        # 兼容新旧配置：字符串 "图片"/"文字" 或 int 1/0
        if isinstance(if_send_pic_raw, str):
            if_send_pic = 0 if if_send_pic_raw == "文字" else 1
        else:
            if_send_pic = int(if_send_pic_raw)
        
        # 设置配置值
        config.theme = data.get("theme", "default")
        config.auto_theme_switch = data.get("auto_theme_switch", False)
        
        # 兼容处理：从 theme_switch_times 字典或独立的 theme_switch_light_time/theme_switch_dark_time 字段读取
        light_time = data.get("theme_switch_light_time", "")
        dark_time = data.get("theme_switch_dark_time", "")
        theme_times = data.get("theme_switch_times", {})
        if isinstance(theme_times, dict):
            light_time = theme_times.get("light") or light_time
            dark_time = theme_times.get("dark") or dark_time
        config.theme_switch_times = {
            "light": light_time if light_time else "06:00",
            "dark": dark_time if dark_time else "18:00"
        }
        config.is_admin_restricted = data.get("is_admin_restricted", 0)
        config.rand = data.get("rand", 20)
        config.if_send_pic = if_send_pic
        config.detailed_logging_enabled = data.get("detailed_logging_enabled", True)
        config.timer_enabled = data.get("timer_enabled", False)
        config.timer_push_time = data.get("timer_push_time", "09:00")
        config.timer_target_groups = data.get("timer_target_groups", [])
        config.timer_rank_type = data.get("timer_rank_type", "daily")
        config.blocked_users = data.get("blocked_users", [])
        config.blocked_groups = data.get("blocked_groups", [])
        config.milestone_enabled = data.get("milestone_enabled", False)
        config.milestone_targets = data.get("milestone_targets", [666, 1000, 2333, 5000, 6666, 10000, 23333])
        
        # LLM 头衔分析配置
        config.llm_enabled = data.get("llm_enabled", False)
        config.llm_provider_id = data.get("llm_provider_id", "")
        config.llm_system_prompt = data.get("llm_system_prompt", "")
        config.llm_max_retries = data.get("llm_max_retries", 2)
        config.llm_min_daily_messages = data.get("llm_min_daily_messages", 0)
        config.llm_enable_on_manual = data.get("llm_enable_on_manual", False)
        config.llm_prompt_version = data.get("llm_prompt_version", "")
        
        return config


@dataclass
class GroupInfo:
    """群组信息
    
    存储群组的基本信息，包括群ID、群名称和成员数量。
    用于排行榜显示和群组识别。
    
    Attributes:
        group_id (str): 群组唯一标识符
        group_name (str): 群组名称，默认为空字符串
        member_count (int): 群组成员数量，默认为0
        
    Methods:
        to_dict(): 转换为字典格式
        
    Example:
        >>> group = GroupInfo("123456789", "测试群", 50)
        >>> print(group.group_name)
        '测试群'
    """
    group_id: str
    group_name: str = ""
    member_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        将GroupInfo实例转换为字典格式，便于JSON序列化。
        
        Returns:
            Dict[str, Any]: 包含群组信息的字典，包括：
                - group_id: 群组ID
                - group_name: 群组名称
                - member_count: 成员数量
                
        Example:
            >>> group = GroupInfo("123", "测试群")
            >>> data = group.to_dict()
            >>> print(data['group_name'])
            '测试群'
        """
        return {
            "group_id": self.group_id,
            "group_name": self.group_name,
            "member_count": self.member_count
        }


@dataclass
class RankData:
    """排行榜数据
    
    存储完整的排行榜信息，包括群组信息、标题、用户数据和统计信息。
    用于排行榜的生成和显示。
    
    Attributes:
        group_info (GroupInfo): 群组信息对象
        title (str): 排行榜标题
        users (List[UserData]): 用户数据列表
        total_messages (int): 总消息数
        generated_at (datetime): 生成时间，默认为当前时间
        
    Methods:
        to_dict(): 转换为字典格式
        
    Example:
        >>> group_info = GroupInfo("123", "测试群")
        >>> rank_data = RankData(group_info, "排行榜", [], 100)
        >>> print(rank_data.title)
        '排行榜'
    """
    group_info: GroupInfo
    title: str
    users: List[UserData]
    total_messages: int
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        将RankData实例转换为字典格式，便于JSON序列化。
        
        Returns:
            Dict[str, Any]: 包含排行榜数据的字典，包括：
                - group_info: 群组信息字典
                - title: 排行榜标题
                - users: 用户数据字典列表
                - total_messages: 总消息数
                - generated_at: 生成时间（ISO格式字符串）
                
        Example:
            >>> rank_data = RankData(group_info, "排行榜", [], 100)
            >>> data = rank_data.to_dict()
            >>> print(data['title'])
            '排行榜'
        """
        return {
            "group_info": self.group_info.to_dict(),
            "title": self.title,
            "users": [user.to_dict() for user in self.users],
            "total_messages": self.total_messages,
            "generated_at": self.generated_at.isoformat()
        }
