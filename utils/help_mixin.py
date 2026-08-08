"""帮助菜单渲染：图片缓存与文字回退。

帮助内容基本不变，所以图片按 HTML 内容哈希缓存在数据目录下，
只要指令列表、主题、字体、版本号都没变化就直接复用已有图片，
渲染不可用时回退为文字。
"""

import asyncio
import hashlib
import os
import re
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from astrbot.api.event import AstrMessageEvent

from .help_content import (
    HELP_SUBTITLE,
    HELP_TIPS,
    HELP_TITLE,
    build_help_sections,
    build_help_text,
)


_PLUGIN_VERSION_CACHE: Optional[str] = None


def _read_plugin_version() -> str:
    """从 metadata.yaml 读取插件版本号，失败时返回空字符串"""
    global _PLUGIN_VERSION_CACHE
    if _PLUGIN_VERSION_CACHE is not None:
        return _PLUGIN_VERSION_CACHE

    version = ""
    try:
        metadata_path = Path(__file__).parent.parent / "metadata.yaml"
        match = re.search(
            r'^version:\s*["\']?([^"\'\r\n]+)',
            metadata_path.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        if match:
            version = match.group(1).strip()
    except OSError:
        version = ""

    _PLUGIN_VERSION_CACHE = version
    return version


class HelpMixin:
    """帮助菜单指令的实现（图片优先，失败回退文字）"""

    # 缓存目录保留的帮助图片数量（深浅色主题、不同字体各占一张）
    HELP_CACHE_KEEP = 6

    def _get_help_prefix(self) -> str:
        """取 AstrBot 当前的唤醒前缀，用于展示可直接复制的指令"""
        try:
            prefixes = self._get_wake_prefixes()
        except Exception:
            prefixes = []
        return prefixes[0] if prefixes else "/"

    def _get_help_cache_dir(self) -> Path:
        """帮助图片缓存目录（放在数据目录，重启后仍可复用）"""
        cache_dir = Path(self.data_manager.data_dir) / "cache" / "help_images"
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def _build_help_meta(self) -> Dict[str, Any]:
        """帮助图片的标题、提示与版本号"""
        return {
            "title": HELP_TITLE,
            "subtitle": HELP_SUBTITLE,
            "tips": HELP_TIPS,
            "version": _read_plugin_version(),
        }

    def _prune_help_cache(self, cache_dir: Path, keep: Optional[int] = None):
        """按修改时间保留最近若干张帮助图片，清掉过期版本"""
        keep = self.HELP_CACHE_KEEP if keep is None else keep
        try:
            images = sorted(
                cache_dir.glob("help_*.png"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            for stale in images[keep:]:
                stale.unlink()
                self.logger.debug(f"已清理过期帮助图片缓存: {stale.name}")
        except OSError as e:
            self.logger.warning(f"清理帮助图片缓存失败: {e}")

    async def _render_help_via_playwright(self, html_content: str, cache_path: Path) -> Optional[str]:
        """Playwright 渲染帮助图片，失败返回 None"""
        return await self.image_generator.generate_help_image(html_content, str(cache_path))

    async def _render_help_via_t2i(self, html_content: str, cache_path: Path) -> Optional[str]:
        """官方 t2i 渲染帮助图片，成功后落到缓存目录"""
        try:
            target_width = self._get_t2i_target_width(html_content)
            t2i_html = self._prepare_t2i_html(html_content, target_width)

            for options in self._t2i_render_options():
                try:
                    render_result = await self.html_render(
                        t2i_html,
                        {},
                        return_url=False,
                        options=options,
                    )
                    image_path = self._store_t2i_render_result(render_result, target_width)
                    if not image_path:
                        self.logger.warning(f"t2i 返回了无效图片，尝试下一渲染策略: {options}")
                        continue
                    if str(image_path).startswith(("http://", "https://")):
                        # 远程 URL 无法落盘缓存，直接使用
                        return str(image_path)
                    shutil.move(str(image_path), str(cache_path))
                    return str(cache_path)
                except Exception as e:
                    self.logger.warning(f"帮助菜单 t2i 渲染策略失败: {type(e).__name__}: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"帮助菜单 t2i 渲染失败: {e}")
            return None

    async def _get_help_image(self, prefix: str) -> Optional[str]:
        """获取帮助图片路径，命中缓存时不重新渲染

        缓存键取自渲染用的 HTML 内容哈希：指令列表、主题深浅、
        自定义字体、版本号任一变化都会得到新的哈希并触发重新生成。
        """
        sections: List[Dict[str, Any]] = build_help_sections(prefix)
        html_content = await self.image_generator.build_help_html(sections, self._build_help_meta())
        if not html_content:
            return None

        cache_key = hashlib.md5(html_content.encode("utf-8")).hexdigest()[:16]
        cache_dir = self._get_help_cache_dir()
        cache_path = cache_dir / f"help_{cache_key}.png"

        if cache_path.exists() and cache_path.stat().st_size > 0:
            self.logger.debug(f"帮助图片命中缓存: {cache_path.name}")
            return str(cache_path)

        # 并发请求时只渲染一次
        lock = getattr(self, "_help_render_lock", None)
        if lock is None:
            lock = asyncio.Lock()
            self._help_render_lock = lock

        async with lock:
            if cache_path.exists() and cache_path.stat().st_size > 0:
                return str(cache_path)

            render_mode = getattr(self.plugin_config, "render_mode", "playwright")
            if render_mode == "t2i":
                image_path = await self._render_help_via_t2i(html_content, cache_path)
                if not image_path:
                    image_path = await self._render_help_via_playwright(html_content, cache_path)
            else:
                image_path = await self._render_help_via_playwright(html_content, cache_path)
                if not image_path:
                    image_path = await self._render_help_via_t2i(html_content, cache_path)

            if image_path:
                self.logger.info(f"帮助图片已生成并缓存: {cache_key}")
                self._prune_help_cache(cache_dir)
            return image_path

    async def _show_help(self, event: AstrMessageEvent):
        """输出帮助菜单：优先图片，渲染不可用时回退文字"""
        prefix = self._get_help_prefix()
        text_msg = build_help_text(prefix)

        render_mode = getattr(self.plugin_config, "render_mode", "playwright")
        if render_mode == "text" or not self.image_generator:
            yield event.plain_result(text_msg)
            return

        image_path = None
        try:
            image_path = await self._get_help_image(prefix)
        except Exception as e:
            self.logger.error(f"生成帮助图片失败，回退文字模式: {e}", exc_info=True)

        if image_path and (str(image_path).startswith("http") or os.path.exists(image_path)):
            # 缓存文件需要长期保留，不做定时清理
            yield event.image_result(str(image_path))
        else:
            yield event.plain_result(text_msg)
