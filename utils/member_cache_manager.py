"""
成员缓存管理器
管理群成员列表缓存和用户昵称缓存，提供跨平台兼容的缓存访问。
使用分层缓存策略（昵称缓存 → 字典缓存 → API获取），
并在API请求外层添加异步锁防止缓存击穿。
"""

import asyncio
from typing import List, Optional, Dict, Any
from cachetools import TTLCache

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent

from .platform_helper import PlatformHelper


class MemberCacheManager:
    """成员缓存管理器
    管理群成员列表缓存和用户昵称缓存，提供跨平台兼容的缓存访问。
    
    分层缓存策略：
    1. 昵称缓存（user_nickname_cache）：TTLCache，最高效
    2. 群成员字典缓存（group_members_dict_cache）：普通dict，中等效率
    3. 群成员列表缓存（group_members_cache）：TTLCache，用于批量操作
    4. API获取：仅在以上缓存均失效时调用
    
    使用异步锁防止缓存击穿：同一时间对同一用户ID只会发起一次API请求。
    """

    def __init__(self, context, cache_ttl: int = 300, nickname_cache_ttl: int = 600):
        """初始化缓存管理器
        
        Args:
            context: AstrBot上下文对象
            cache_ttl: 群成员缓存TTL（秒），默认300秒（5分钟）
            nickname_cache_ttl: 昵称缓存TTL（秒），默认600秒（10分钟）
        """
        self.context = context
        
        # 群成员列表缓存（TTLCache，用于批量操作）
        self.group_members_cache = TTLCache(maxsize=100, ttl=cache_ttl)
        
        # 群成员字典缓存（普通dict，用于快速查找）
        self.group_members_dict_cache: Dict[str, Dict[str, Any]] = {}
        
        # 用户昵称缓存（TTLCache，最高效）
        self.user_nickname_cache = TTLCache(maxsize=500, ttl=nickname_cache_ttl)
        
        # 异步锁字典：防止同一用户ID的并发API请求（缓存击穿防护）
        self._fetch_locks: Dict[str, asyncio.Lock] = {}
        # 群成员列表获取锁
        self._members_locks: Dict[str, asyncio.Lock] = {}
    
    def _get_fetch_lock(self, user_id: str) -> asyncio.Lock:
        """获取或创建用户ID对应的异步锁"""
        if user_id not in self._fetch_locks:
            self._fetch_locks[user_id] = asyncio.Lock()
        return self._fetch_locks[user_id]
    
    def _get_members_lock(self, group_id: str) -> asyncio.Lock:
        """获取或创建群组ID对应的异步锁"""
        if group_id not in self._members_locks:
            self._members_locks[group_id] = asyncio.Lock()
        return self._members_locks[group_id]
    
    # ========== 公开方法 ==========
    
    async def get_user_display_name(self, event: AstrMessageEvent, group_id: str, user_id: str) -> str:
        """获取用户的群昵称（统一入口）
        
        采用分层缓存策略：
        1. 从昵称缓存获取（最高效）
        2. 从群成员字典缓存获取（中等效率）
        3. 从API获取（带异步锁防止缓存击穿）
        4. 返回默认昵称
        
        Args:
            event: 消息事件对象
            group_id: 群组ID
            user_id: 用户ID
            
        Returns:
            用户的显示昵称，如果都失败则返回 "用户{user_id}"
        """
        # 步骤1: 从昵称缓存获取
        nickname = self._get_from_nickname_cache(user_id)
        if nickname:
            return nickname
        
        # 步骤2: 从群成员字典缓存获取
        nickname = self._get_from_dict_cache(group_id, user_id)
        if nickname:
            return nickname
        
        # 步骤3: 从API获取（带异步锁防止缓存击穿）
        nickname = await self._fetch_and_cache_from_api(event, group_id, user_id)
        if nickname:
            return nickname
        
        # 步骤4: 返回默认昵称
        return f"用户{user_id}"
    
    async def get_fallback_nickname(self, event: AstrMessageEvent, user_id: str) -> str:
        """获取备用昵称（从事件对象获取发送者名称）"""
        try:
            nickname = event.get_sender_name()
            if not nickname or not nickname.strip():
                nickname = f"用户{user_id}"
                logger.warning(f"事件中获取的昵称为空，使用默认昵称: {nickname}")
            return nickname
        except (AttributeError, KeyError, TypeError) as e:
            logger.error(f"获取备用昵称失败: {e}")
            return f"用户{user_id}"
    
    def get_display_name_from_member(self, member: Dict[str, Any]) -> Optional[str]:
        """从群成员信息中提取显示昵称（跨平台通用）"""
        return PlatformHelper.get_display_name_from_member(member)
    
    def clear_user_cache(self, user_id: Optional[str] = None):
        """清理用户昵称缓存
        
        Args:
            user_id: 指定用户ID，为None时清理所有
        """
        if user_id:
            nickname_cache_key = f"nickname_{user_id}"
            if nickname_cache_key in self.user_nickname_cache:
                del self.user_nickname_cache[nickname_cache_key]
        else:
            self.user_nickname_cache.clear()
        
        logger.info(f"清理用户缓存: {user_id or '全部'}")
    
    async def refresh_group_cache(self, event: AstrMessageEvent, group_id: str) -> bool:
        """刷新指定群的成员缓存
        
        清除缓存后重新从API获取最新数据。
        
        Args:
            event: 消息事件对象
            group_id: 群组ID
            
        Returns:
            bool: 是否成功刷新
        """
        try:
            # 清除特定群的成员缓存
            cache_key = f"group_members_{group_id}"
            if cache_key in self.group_members_cache:
                del self.group_members_cache[cache_key]
            
            # 清除群成员字典缓存
            dict_cache_key = f"group_members_dict_{group_id}"
            if dict_cache_key in self.group_members_dict_cache:
                del self.group_members_dict_cache[dict_cache_key]
            
            # 清除昵称缓存
            self.clear_user_cache()
            
            # 重新从API获取
            members_info = await self._fetch_group_members_from_api(event, group_id)
            return members_info is not None
        except Exception as e:
            logger.error(f"刷新群成员缓存失败: {e}")
            return False
    
    async def get_group_members(self, event: AstrMessageEvent, group_id: str) -> Optional[List[Dict[str, Any]]]:
        """获取群成员列表（带缓存）"""
        cache_key = f"group_members_{group_id}"
        
        if cache_key in self.group_members_cache:
            return self.group_members_cache[cache_key]
        
        return await self._fetch_group_members_from_api(event, group_id)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "members_cache_size": len(self.group_members_cache),
            "members_cache_maxsize": self.group_members_cache.maxsize,
            "dict_cache_size": len(self.group_members_dict_cache),
            "nickname_cache_size": len(self.user_nickname_cache),
            "nickname_cache_maxsize": self.user_nickname_cache.maxsize,
        }
    
    def update_nickname_cache(self, user_id: str, nickname: str):
        """更新昵称缓存
        
        Args:
            user_id: 用户ID
            nickname: 昵称
        """
        nickname_cache_key = f"nickname_{user_id}"
        self.user_nickname_cache[nickname_cache_key] = nickname
    
    def get_nickname_from_cache(self, user_id: str) -> Optional[str]:
        """从昵称缓存获取昵称"""
        nickname_cache_key = f"nickname_{user_id}"
        return self.user_nickname_cache.get(nickname_cache_key)
    
    def is_milestone_cached(self, group_id: str, user_id: str, count: int) -> bool:
        """检查里程碑是否已缓存（防止重复推送）"""
        milestone_cache_key = f"milestone_{group_id}_{user_id}_{count}"
        return milestone_cache_key in self.user_nickname_cache
    
    def mark_milestone_cached(self, group_id: str, user_id: str, count: int):
        """标记里程碑已推送"""
        milestone_cache_key = f"milestone_{group_id}_{user_id}_{count}"
        self.user_nickname_cache[milestone_cache_key] = True
    
    def clear_all(self):
        """清理所有缓存"""
        self.group_members_cache.clear()
        self.group_members_dict_cache.clear()
        self.user_nickname_cache.clear()
        self._fetch_locks.clear()
        self._members_locks.clear()
        logger.info("所有缓存已清理")
    
    # ========== 私有方法 ==========
    
    def _get_from_nickname_cache(self, user_id: str) -> Optional[str]:
        """从昵称缓存获取昵称"""
        nickname_cache_key = f"nickname_{user_id}"
        return self.user_nickname_cache.get(nickname_cache_key)
    
    def _get_from_dict_cache(self, group_id: str, user_id: str) -> Optional[str]:
        """从群成员字典缓存获取昵称"""
        dict_cache_key = f"group_members_dict_{group_id}"
        if dict_cache_key in self.group_members_dict_cache:
            members_dict = self.group_members_dict_cache[dict_cache_key]
            if user_id in members_dict:
                member = members_dict[user_id]
                display_name = self.get_display_name_from_member(member)
                if display_name:
                    # 回填到昵称缓存
                    self.update_nickname_cache(user_id, display_name)
                    return display_name
        return None
    
    async def _fetch_and_cache_from_api(self, event: AstrMessageEvent, group_id: str, user_id: str) -> Optional[str]:
        """从API获取群成员信息并缓存（带异步锁防止缓存击穿）"""
        lock = self._get_fetch_lock(user_id)
        async with lock:
            # 双重检查：获取锁后再次检查缓存
            cached = self._get_from_nickname_cache(user_id)
            if cached:
                return cached
            
            cached = self._get_from_dict_cache(group_id, user_id)
            if cached:
                return cached
            
            # 真正执行API请求
            try:
                members_info = await self._fetch_group_members_from_api(event, group_id)
                if members_info:
                    # 重建字典缓存
                    dict_cache_key = f"group_members_dict_{group_id}"
                    members_dict = {}
                    for m in members_info:
                        uid = PlatformHelper.get_user_id_from_member(m)
                        if uid:
                            members_dict[uid] = m
                    self.group_members_dict_cache[dict_cache_key] = members_dict
                    
                    # 查找用户
                    if user_id in members_dict:
                        member = members_dict[user_id]
                        display_name = self.get_display_name_from_member(member)
                        if display_name:
                            self.update_nickname_cache(user_id, display_name)
                            return display_name
            except (AttributeError, KeyError, TypeError) as e:
                logger.warning(f"获取群成员信息失败(数据格式错误): {e}")
            except (ConnectionError, TimeoutError, OSError) as e:
                logger.warning(f"获取群成员信息失败(网络错误): {e}")
            except (ImportError, RuntimeError) as e:
                logger.warning(f"获取群成员信息失败(系统错误): {e}")
            
            return None
    
    async def _fetch_group_members_from_api(self, event: AstrMessageEvent, group_id: str) -> Optional[List[Dict[str, Any]]]:
        """从API获取群成员（跨平台通用，带群级别异步锁）"""
        lock = self._get_members_lock(group_id)
        async with lock:
            # 双重检查缓存
            cache_key = f"group_members_{group_id}"
            if cache_key in self.group_members_cache:
                return self.group_members_cache[cache_key]
            
            try:
                helper = PlatformHelper(event, self.context)
                members_info = await helper.get_group_members(group_id)
                
                if members_info:
                    self.group_members_cache[cache_key] = members_info
                    
                    if len(members_info) > 500:
                        logger.warning(f"群 {group_id} 成员数较多({len(members_info)}),建议调整缓存策略")
                    
                    return members_info
            except (AttributeError, KeyError, TypeError) as e:
                logger.warning(f"获取群成员列表失败(数据格式错误): {e}")
            except (ConnectionError, TimeoutError, OSError) as e:
                logger.warning(f"获取群成员列表失败(网络错误): {e}")
            except (ImportError, RuntimeError) as e:
                logger.warning(f"获取群成员列表失败(系统错误): {e}")
            
            return None
