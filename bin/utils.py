import os
import re
import requests
from configparser import RawConfigParser

# 请求头（伪装浏览器，防拦截）
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Connection": "keep-alive"
}

def read_config(path="config/settings.inf"):
    """读取配置文件"""
    config = RawConfigParser()
    config.read(path, encoding="utf-8")
    return {
        "timeout": int(config.get("DEFAULT", "check_timeout")),
        "min_res": int(config.get("DEFAULT", "min_resolution")),
        "max_per_channel": int(config.get("DEFAULT", "max_output_per_channel")),
        "max_workers": int(config.get("DEFAULT", "max_workers"))
    }

def read_file_lines(path, encoding="utf-8"):
    """按行读取文件，自动处理编码，统一返回UTF-8文本"""
    try:
        with open(path, "r", encoding=encoding) as f:
            return [line.strip() for line in f if line.strip()]
    except:
        with open(path, "r", encoding="gbk") as f:
            return [line.strip() for line in f if line.strip()]

def write_file_lines(path, lines):
    """写入文件（UTF-8）"""
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def fetch_content(url, timeout=10):
    """获取网络/本地文件内容，统一返回UTF-8字符串"""
    if url.startswith("http"):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
            resp.raise_for_status()
            return resp.content.decode("utf-8", errors="ignore")
        except:
            return None
    else:
        if os.path.exists(url):
            try:
                with open(url, "r", encoding="utf-8") as f:
                    return f.read()
            except:
                try:
                    with open(url, "r", encoding="gbk") as f:
                        return f.read()
                except:
                    return None
        return None

def parse_m3u_or_txt(content):
    """解析 txt/m3u 格式，返回 频道名,链接"""
    lines = content.splitlines() if isinstance(content, str) else content
    result = []
    current_name = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # m3u解析
        if line.startswith("#EXTINF"):
            match = re.search(r'[,，](.*?)$', line)
            if match:
                current_name = match.group(1).strip()
        elif line.startswith("http") or line.startswith("rtsp") or line.endswith((".m3u8", ".ts")):
            if current_name:
                result.append((current_name, line))
        # txt解析（频道名,链接）
        elif "," in line and not line.startswith("#"):
            parts = line.split(",", 1)
            name = parts[0].strip()
            url = parts[1].strip()
            if url.startswith(("http", "rtsp")):
                result.append((name, url))
    return result

def mark_input_invalid(input_path, url):
    """给input.txt里无效地址前面加#"""
    lines = read_file_lines(input_path)
    new_lines = []
    for line in lines:
        if line.strip() == url.strip() and not line.strip().startswith("#"):
            new_lines.append(f"# {line}")
        else:
            new_lines.append(line)
    write_file_lines(input_path, new_lines)