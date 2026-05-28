"""
基金经理信息获取模块
数据来源: 天天基金网 (fund.eastmoney.com)
"""
import requests
import re
import json
from typing import List, Dict, Optional


def fetch_fund_manager(fund_code: str) -> Optional[Dict]:
    """
    获取单只基金的基金经理信息
    返回: {
        "fund_code": str,
        "managers": [
            {
                "name": str,
                "work_time": str,
                "fund_size": str,
                "star": int,
                "power": dict,
            }
        ]
    }
    """
    try:
        url = f"http://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        # 尝试多种编码
        text = None
        for enc in ["utf-8-sig", "gbk", "gb2312", "gb18030"]:
            try:
                text = resp.content.decode(enc)
                if "Data_currentFundManager" in text:
                    break
            except Exception:
                continue
        if text is None:
            return None

        idx = text.find("var Data_currentFundManager =")
        if idx < 0:
            return None

        start = idx + len("var Data_currentFundManager =")
        bracket_count = 0
        end_idx = start
        for i, c in enumerate(text[start:]):
            if c == "[":
                bracket_count += 1
            elif c == "]":
                bracket_count -= 1
                if bracket_count == 0:
                    end_idx = start + i + 1
                    break

        json_str = text[start:end_idx]
        managers_raw = json.loads(json_str)

        managers = []
        for m in managers_raw:
            power = m.get("power", {}) or {}
            managers.append({
                "name": m.get("name", "未知"),
                "work_time": m.get("workTime", ""),
                "fund_size": m.get("fundSize", ""),
                "star": m.get("star", 0),
                "power": {
                    "average": power.get("avr", ""),
                    "categories": power.get("categories", []),
                    "descriptions": power.get("dsc", []),
                },
            })

        return {
            "fund_code": fund_code,
            "managers": managers,
        }
    except Exception:
        return None


def format_manager_report(data: Optional[Dict]) -> str:
    """格式化基金经理报告"""
    if not data or not data.get("managers"):
        return ""

    lines = [
        "",
        "=" * 50,
        "👤 基金经理信息",
        "=" * 50,
    ]

    for mgr in data["managers"]:
        lines.append(f"\n  姓名: {mgr['name']}")
        lines.append(f"  任职时间: {mgr['work_time']}")
        lines.append(f"  管理规模: {mgr['fund_size']}")
        if mgr["star"]:
            lines.append(f"  评级: {'⭐' * mgr['star']}")
        if mgr["power"].get("average"):
            lines.append(f"  综合能力: {mgr['power']['average']}")

    lines.append("=" * 50)
    return "\n".join(lines)
