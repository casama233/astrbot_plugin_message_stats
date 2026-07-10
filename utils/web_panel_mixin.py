"""Web 面板、字体管理和相关数据查询能力。"""

import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List

import aiofiles
import orjson

from astrbot.api.star import StarTools

from .models import PluginConfig, RankType


class WebPanelMixin:
    """Web 面板、字体管理和相关数据查询能力。"""

    def _parse_rank_type_value(self, rank_type: str) -> RankType:
        rank_type_str = str(rank_type or 'total').strip().lower()
        mapping = {
            'total': RankType.TOTAL,
            '总榜': RankType.TOTAL,
            'daily': RankType.DAILY,
            '今日榜': RankType.DAILY,
            '日榜': RankType.DAILY,
            'week': RankType.WEEKLY,
            'weekly': RankType.WEEKLY,
            '本周榜': RankType.WEEKLY,
            '周榜': RankType.WEEKLY,
            'month': RankType.MONTHLY,
            'monthly': RankType.MONTHLY,
            '本月榜': RankType.MONTHLY,
            '月榜': RankType.MONTHLY,
            'year': RankType.YEARLY,
            'yearly': RankType.YEARLY,
            '本年榜': RankType.YEARLY,
            '年榜': RankType.YEARLY,
            'lastyear': RankType.LAST_YEAR,
            'last_year': RankType.LAST_YEAR,
            '去年榜': RankType.LAST_YEAR,
            '去年': RankType.LAST_YEAR,
            'yesterday': RankType.YESTERDAY,
            '昨日榜': RankType.YESTERDAY,
            '昨日': RankType.YESTERDAY,
            '昨天': RankType.YESTERDAY
        }
        return mapping.get(rank_type_str, RankType.TOTAL)

    def _is_valid_group_id(self, group_id: str) -> bool:
        return bool(re.fullmatch(r"-?\d{5,32}", str(group_id or "")))

    async def _is_existing_group_id(self, group_id: str) -> bool:
        return str(group_id) in {str(gid) for gid in await self.data_manager.get_all_groups()}

    def _is_same_origin_request(self, request) -> bool:
        host = request.headers.get('Host', '') if request else ''
        origin = request.headers.get('Origin', '') if request else ''
        referer = request.headers.get('Referer', '') if request else ''
        sec_fetch_site = request.headers.get('Sec-Fetch-Site', '') if request else ''
        if sec_fetch_site and sec_fetch_site not in {'same-origin', 'same-site', 'none'}:
            return False
        if origin:
            return host and origin.split('://', 1)[-1].split('/', 1)[0] == host
        if referer:
            return host and referer.split('://', 1)[-1].split('/', 1)[0] == host
        return bool(sec_fetch_site == 'none')

    def _get_fonts_dir(self) -> Path:
        return Path(StarTools.get_data_dir('message_stats')) / "resources" / "fonts"

    def _get_legacy_fonts_dir(self) -> Path:
        return Path(StarTools.get_data_dir("astrbot_plugin_message_stats")) / "resources" / "fonts"

    def _sanitize_font_filename(self, filename: str) -> str:
        name = Path(str(filename or "")).name.strip()
        stem = Path(name).stem
        suffix = Path(name).suffix.lower()
        safe_stem = re.sub(r"[^0-9A-Za-z._\-一-鿿]+", "_", stem).strip("._-")
        if not safe_stem:
            safe_stem = "font"
        return f"{safe_stem[:80]}{suffix}"

    def _is_allowed_font_file(self, filename: str) -> bool:
        return Path(str(filename or "")).suffix.lower() in {'.ttf', '.otf', '.woff', '.woff2', '.ttc'}

    def _format_file_size(self, size: int) -> str:
        if size < 1024 * 1024:
            return f"{size / 1024:.1f}KB"
        return f"{size / 1024 / 1024:.1f}MB"

    def _get_font_config_path(self, filename: str) -> str:
        return f"resources/fonts/{filename}"

    def _attach_font_dirs(self, config: PluginConfig) -> PluginConfig:
        config.font_base_dirs = [str(self._get_fonts_dir()), str(self._get_legacy_fonts_dir())]
        return config

    def _normalize_selected_font_name(self, font_path: str) -> str:
        font_path = str(font_path or "").replace("\\", "/").strip()
        if not font_path:
            return ""
        return Path(font_path).name

    def _list_uploaded_fonts(self) -> List[Dict[str, Any]]:
        current_font = self._normalize_selected_font_name(getattr(self.plugin_config, 'font_path', ''))
        fonts = []
        seen = set()
        for fonts_dir in (self._get_fonts_dir(), self._get_legacy_fonts_dir()):
            if not fonts_dir.exists():
                continue
            for font_file in sorted(fonts_dir.iterdir(), key=lambda p: p.name.lower()):
                if font_file.name in seen or not font_file.is_file() or not self._is_allowed_font_file(font_file.name):
                    continue
                seen.add(font_file.name)
                stat = font_file.stat()
                fonts.append({
                    "name": font_file.name,
                    "path": self._get_font_config_path(font_file.name),
                    "size": stat.st_size,
                    "size_text": self._format_file_size(stat.st_size),
                    "is_current": font_file.name == current_font
                })
        return fonts

    async def _save_font_path_config(self, font_path: str):
        font_path = str(font_path or "").strip()
        if font_path:
            font_name = self._sanitize_font_filename(self._normalize_selected_font_name(font_path))
            if font_name:
                font_path = self._get_font_config_path(font_name)
        config = self._attach_font_dirs(self.plugin_config)
        config.font_path = font_path
        self.plugin_config = config
        self.data_manager.set_plugin_config(config)
        await self.data_manager.save_config(config)
        if self.config is not None:
            try:
                if hasattr(self.config, '__setitem__'):
                    self.config['font_path'] = font_path
                if hasattr(self.config, 'save_config'):
                    result = self.config.save_config()
                    if hasattr(result, '__await__'):
                        await result
            except Exception as e:
                self.logger.warning(f"保存AstrBot字体配置失败: {e}")
        if self.image_generator:
            self.image_generator.config = config
            self.image_generator._font_css_cache_key = None
            self.image_generator._font_css_cache_value = ""

    def _get_web_rank_period(self, rank_type: RankType):
        today = date.today()
        if rank_type == RankType.DAILY:
            return today, today
        if rank_type == RankType.YESTERDAY:
            yesterday = today - timedelta(days=1)
            return yesterday, yesterday
        if rank_type == RankType.WEEKLY:
            return today - timedelta(days=today.weekday()), today
        if rank_type == RankType.MONTHLY:
            return today.replace(day=1), today
        if rank_type == RankType.YEARLY:
            return today.replace(month=1, day=1), today
        if rank_type == RankType.LAST_YEAR:
            return date(today.year - 1, 1, 1), date(today.year - 1, 12, 31)
        return None, None

    async def page_stats(self):
        try:
            from quart import request
            import os
            gid = request.args.get('group_id') if request else None
            rank_type = self._parse_rank_type_value(request.args.get('rank_type', 'total') if request else 'total')
            if gid:
                if not self._is_valid_group_id(gid):
                    return self._jsonify({"status":"error","message":"group_id参数无效"})
                users = await self.data_manager.get_group_data(gid)
                if not users:
                    return self._jsonify({"status":"ok","data":{"group":None}})
                act = [u for u in users if u.message_count>0]
                # 根据 rank_type 计算时间段内数据
                start, end = self._get_web_rank_period(rank_type)

                if start is not None:
                    # 按时段排序
                    act_with_period = []
                    for u in act:
                        pc = u.get_message_count_in_period(start, end)
                        if pc > 0:
                            act_with_period.append((u, pc))
                    act_with_period.sort(key=lambda x: x[1], reverse=True)
                    tm = sum(c for _, c in act_with_period)
                    tu = []
                    for u, pc in act_with_period[:self.plugin_config.rand]:
                        pct = (pc/tm*100) if tm>0 else 0
                        tu.append({"nickname":u.nickname,"message_count":pc,"title":u.llm_title or u.display_title or "","title_color":u.llm_title_color or u.display_title_color or "","last_date":u.last_date or "","percentage":round(pct,1)})
                else:
                    act.sort(key=lambda x:x.message_count,reverse=True)
                    tm = sum(u.message_count for u in act)
                    tu = []
                    for u in act[:self.plugin_config.rand]:
                        pct = (u.message_count/tm*100) if tm>0 else 0
                        tu.append({"nickname":u.nickname,"message_count":u.message_count,"title":u.llm_title or u.display_title or "","title_color":u.llm_title_color or u.display_title_color or "","last_date":u.last_date or "","percentage":round(pct,1)})

                fp2 = self.data_manager.groups_dir / f"{gid}.json"
                fs2 = ""
                if fp2.exists():
                    s2 = os.path.getsize(str(fp2))
                    fs2 = f"{s2/1024:.1f}KB" if s2<1024*1024 else f"{s2/1024/1024:.1f}MB"
                gn = self._web_group_name_cache.get(str(gid), f"群{gid}")
                return self._jsonify({"status":"ok","data":{"group":{"group_id":gid,"group_name":gn,"display_name":f"{gn} - {gid}","file_size":fs2,"total_messages":tm,"user_count":len(act),"top_users":tu}}})
            gd = []
            ag = await self.data_manager.get_all_groups()
            for g2 in ag[:50]:
                us = await self.data_manager.get_group_data(g2)
                if not us: continue
                ac = [u for u in us if u.message_count>0]
                ac.sort(key=lambda x:x.message_count,reverse=True)
                fp = self.data_manager.groups_dir / f"{g2}.json"
                fs = ""
                if fp.exists():
                    s = os.path.getsize(str(fp))
                    fs = f"{s/1024:.1f}KB" if s<1024*1024 else f"{s/1024/1024:.1f}MB"
                gn = self._web_group_name_cache.get(str(g2), f"群{g2}")
                tm = sum(u.message_count for u in ac)
                gd.append({"group_id":g2,"group_name":gn,"display_name":f"{gn} - {g2}","file_size":fs,"total_messages":tm,"user_count":len(ac)})
            # 按总发言数降序排序
            gd.sort(key=lambda x: x["total_messages"], reverse=True)
            ts = None

            if self.timer_manager:
                s = await self.timer_manager.get_status()
                ts = {"running":s["status"]=="running","next_push":str(s.get("next_push_time","") or "")}
            c = self.plugin_config
            return self._jsonify({"status":"ok","data":{"groups":gd,"config":{"rand":c.rand,"if_send_pic":c.if_send_pic},"timer":ts}})
        except Exception as e:
            self.logger.error(f"Web统计接口失败: {e}", exc_info=True)
            return self._jsonify({"status":"error","message":"获取统计数据失败"})

    async def page_delete(self):
        """Web API: 删除群组数据"""
        try:
            from quart import request
            if not self._is_same_origin_request(request):
                return self._jsonify({"status":"error","message":"请求来源无效"})

            form = await request.form
            gid = form.get('group_id') if form else None
            if not gid:
                payload = await request.get_json(silent=True)
                gid = payload.get('group_id') if isinstance(payload, dict) else None
            if not gid:
                return self._jsonify({"status":"error","message":"缺少group_id参数"})
            if not self._is_valid_group_id(gid):
                return self._jsonify({"status":"error","message":"group_id参数无效"})
            if not await self._is_existing_group_id(gid):
                return self._jsonify({"status":"error","message":"群组数据不存在"})
            ok = await self.data_manager.clear_group_data(str(gid))
            if ok:
                self.logger.info(f"Web面板删除群组数据: {gid}")
                return self._jsonify({"status":"ok","message":"已删除"})
            return self._jsonify({"status":"error","message":"删除失败"})
        except Exception as e:
            self.logger.error(f"Web删除接口失败: {e}", exc_info=True)
            return self._jsonify({"status":"error","message":"删除失败"})

    async def page_chart(self):
        """Web API: 获取群组近7天发言趋势"""
        try:
            from quart import request
            from datetime import date, timedelta
            gid = request.args.get('group_id') if request else None
            if gid and not self._is_valid_group_id(gid):
                return self._jsonify({"status":"error","message":"group_id参数无效"})
            if not gid:
                return self._jsonify({"status":"ok","data":{"days":[],"counts":[]}})

            users = await self.data_manager.get_group_data(gid)
            if not users:
                return self._jsonify({"status":"ok","data":{"days":[],"counts":[]}})

            # 聚合所有用户每天的总发言数
            daily_totals = {}
            for u in users:
                if hasattr(u, '_message_dates') and u._message_dates:
                    for date_str, count in u._message_dates.items():
                        daily_totals[date_str] = daily_totals.get(date_str, 0) + count

            # 取最近7天
            today = date.today()
            days, counts = [], []
            for i in range(6, -1, -1):
                d = today - timedelta(days=i)
                ds = str(d)
                days.append(f"{d.month}/{d.day}")
                counts.append(daily_totals.get(ds, 0))

            return self._jsonify({"status":"ok","data":{"days":days,"counts":counts}})
        except Exception as e:
            self.logger.error(f"Web图表接口失败: {e}", exc_info=True)
            return self._jsonify({"status":"error","message":"获取图表数据失败"})

    async def page_fonts(self):
        try:
            current_path = str(getattr(self.plugin_config, 'font_path', '') or '')
            current_name = self._normalize_selected_font_name(current_path)
            return self._jsonify({"status":"ok","data":{
                "fonts": self._list_uploaded_fonts(),
                "current_path": current_path,
                "current_name": current_name
            }})
        except Exception as e:
            self.logger.error(f"Web字体列表接口失败: {e}", exc_info=True)
            return self._jsonify({"status":"error","message":"获取字体列表失败"})

    async def page_font_upload(self):
        try:
            from quart import request
            if not self._is_same_origin_request(request):
                return self._jsonify({"status":"error","message":"请求来源无效"})

            files = await request.files
            file = files.get('font') if files else None
            data = None
            filename = ""
            if file and getattr(file, 'filename', ''):
                filename = file.filename
                data = file.read()
                if hasattr(data, '__await__'):
                    data = await data
            else:
                payload = await request.get_json(silent=True)
                if isinstance(payload, dict):
                    import base64
                    filename = str(payload.get('filename') or '')
                    content = str(payload.get('content') or '')
                    if ',' in content:
                        content = content.split(',', 1)[1]
                    try:
                        data = base64.b64decode(content, validate=True)
                    except Exception:
                        return self._jsonify({"status":"error","message":"字体文件内容无效"})

            if not filename:
                return self._jsonify({"status":"error","message":"请选择字体文件"})
            if not self._is_allowed_font_file(filename):
                return self._jsonify({"status":"error","message":"仅支持 .ttf/.otf/.woff/.woff2/.ttc 字体文件"})
            if not data:
                return self._jsonify({"status":"error","message":"字体文件为空"})
            max_size = 50 * 1024 * 1024
            if len(data) > max_size:
                return self._jsonify({"status":"error","message":"字体文件不能超过50MB"})

            fonts_dir = self._get_fonts_dir()
            fonts_dir.mkdir(parents=True, exist_ok=True)
            safe_name = self._sanitize_font_filename(filename)
            target = fonts_dir / safe_name
            if target.exists():
                digest = orjson.dumps({"name": safe_name, "size": len(data)}).hex()[:8]
                target = fonts_dir / f"{Path(safe_name).stem}_{digest}{Path(safe_name).suffix}"

            async with aiofiles.open(str(target), 'wb') as f:
                await f.write(data)

            font_path = self._get_font_config_path(target.name)
            await self._save_font_path_config(font_path)
            saved_path = str(getattr(self.plugin_config, 'font_path', '') or '')
            self.logger.info(f"Web面板上传并启用自定义字体: {target.name}")
            return self._jsonify({"status":"ok","message":"字体已上传并启用","data":{"font_path":saved_path,"name":target.name,"fonts":self._list_uploaded_fonts()}})
        except Exception as e:
            self.logger.error(f"Web字体上传接口失败: {e}", exc_info=True)
            return self._jsonify({"status":"error","message":"上传字体失败"})

    async def page_font_select(self):
        try:
            from quart import request
            if not self._is_same_origin_request(request):
                return self._jsonify({"status":"error","message":"请求来源无效"})

            form = await request.form
            font_path = form.get('font_path') if form else None
            if font_path is None:
                payload = await request.get_json(silent=True)
                font_path = payload.get('font_path') if isinstance(payload, dict) else ''
            font_path = str(font_path or '').strip()
            if font_path:
                font_name = self._sanitize_font_filename(self._normalize_selected_font_name(font_path))
                if not self._is_allowed_font_file(font_name):
                    return self._jsonify({"status":"error","message":"字体文件类型不支持"})
                target = self._get_fonts_dir() / font_name
                legacy_target = self._get_legacy_fonts_dir() / font_name
                if not target.exists() and legacy_target.exists() and legacy_target.is_file():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(legacy_target.read_bytes())
                if not target.exists() or not target.is_file():
                    return self._jsonify({"status":"error","message":"字体文件不存在"})
                font_path = self._get_font_config_path(font_name)

            await self._save_font_path_config(font_path)
            saved_path = str(getattr(self.plugin_config, 'font_path', '') or '')
            self.logger.info(f"Web面板切换自定义字体: {saved_path or '默认字体'}")
            return self._jsonify({"status":"ok","message":"字体设置已保存","data":{"font_path":saved_path,"fonts":self._list_uploaded_fonts()}})
        except Exception as e:
            self.logger.error(f"Web字体选择接口失败: {e}", exc_info=True)
            return self._jsonify({"status":"error","message":"保存字体设置失败"})

    async def page_font_delete(self):
        try:
            from quart import request
            if not self._is_same_origin_request(request):
                return self._jsonify({"status":"error","message":"请求来源无效"})

            form = await request.form
            font_path = form.get('font_path') if form else None
            if font_path is None:
                payload = await request.get_json(silent=True)
                font_path = payload.get('font_path') if isinstance(payload, dict) else ''
            font_name = self._sanitize_font_filename(self._normalize_selected_font_name(font_path))
            if not font_name or not self._is_allowed_font_file(font_name):
                return self._jsonify({"status":"error","message":"字体文件参数无效"})
            target = self._get_fonts_dir() / font_name
            legacy_target = self._get_legacy_fonts_dir() / font_name
            if not target.exists() and legacy_target.exists() and legacy_target.is_file():
                target = legacy_target
            if not target.exists() or not target.is_file():
                return self._jsonify({"status":"error","message":"字体文件不存在"})

            target.unlink()
            current_name = self._normalize_selected_font_name(getattr(self.plugin_config, 'font_path', ''))
            if current_name == font_name:
                await self._save_font_path_config("")
            self.logger.info(f"Web面板删除自定义字体: {font_name}")
            return self._jsonify({"status":"ok","message":"字体已删除","data":{"fonts":self._list_uploaded_fonts(),"current_path":getattr(self.plugin_config, 'font_path', '')}})
        except Exception as e:
            self.logger.error(f"Web字体删除接口失败: {e}", exc_info=True)
            return self._jsonify({"status":"error","message":"删除字体失败"})
