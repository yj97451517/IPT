import subprocess
import re
import requests
from bin.utils import HEADERS

def check_url_valid(url, timeout=8):
    """检测链接是否有效（超时=无效）"""
    try:
        resp = requests.head(
            url, headers=HEADERS, timeout=timeout, allow_redirects=True
        )
        return resp.status_code in (200, 301, 302)
    except:
        try:
            resp = requests.get(
                url, headers=HEADERS, timeout=timeout, stream=True
            )
            return resp.status_code in (200, 301, 302)
        except:
            return False

def get_resolution(url, timeout=8):
    """使用ffprobe获取分辨率，返回高度（720/1080等）"""
    command = [
        "bin/ffprobe.exe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=height",
        "-of", "csv=p=0",
        "-timeout", str(timeout * 1000000),
        url
    ]
    try:
        res = subprocess.check_output(command, timeout=timeout, text=True)
        return int(res.strip()) if res.strip().isdigit() else 0
    except:
        return 0

def load_alias(path="config/alias.txt"):
    """加载频道别名映射表，大小写不敏感"""
    mapping = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except:
        return mapping

    for line in lines:
        line = line.strip()
        if not line or "," not in line:
            continue
        key_part, alias_part = line.split(",", 1)
        std_name = key_part.strip()
        alias_str = alias_part.strip().strip("[]").replace("'", "").replace(" ", "")
        alias_list = alias_str.split(",")

        # 统一小写存储
        for a in alias_list:
            a_clean = a.strip().lower()
            mapping[a_clean] = std_name
    return mapping

def match_channel(name, alias_map):
    """按小写匹配，不区分大小写"""
    if not name:
        return None
    name_clean = name.strip().lower()
    return alias_map.get(name_clean, None)

def load_demo_channels(path="config/demo.txt"):
    """加载模板频道+分组"""
    groups = {}
    current_group = None
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except:
        return groups

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "#genre#" in line:
            current_group = line.split(",")[0].strip()
            groups[current_group] = []
        elif current_group is not None:
            groups[current_group].append(line)
    return groups