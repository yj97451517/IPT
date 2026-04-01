from concurrent.futures import ThreadPoolExecutor, as_completed
from bin.utils import read_config, fetch_content, parse_m3u_or_txt, mark_input_invalid, write_file_lines
from bin.filter import check_url_valid, get_resolution, load_alias, match_channel, load_demo_channels

def run():
    cfg = read_config()
    timeout = cfg["timeout"]
    min_res = cfg["min_res"]
    max_num = cfg["max_per_channel"]
    max_workers = cfg["max_workers"]

    # 加载模板、别名
    demo_groups = load_demo_channels()
    alias_map = load_alias()
    all_valid = {}  # {标准频道: [url1, url2...]}
    unused = []     # 有效但未入选的高清源

    # 读取待检测源
    try:
        with open("config/input.txt", "r", encoding="utf-8") as f:
            input_urls = [
                u.strip() for u in f.readlines()
                if u.strip() and not u.strip().startswith("#")
            ]
    except:
        input_urls = []

    print(f"[启动] 并发线程：{max_workers} | 超时：{timeout}s | 最低分辨率：{min_res}P")
    print("-" * 60)

    # 批量检测直播源地址
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {}

        for source_url in input_urls:
            content = fetch_content(source_url, timeout=timeout)
            if not content:
                mark_input_invalid("config/input.txt", source_url)
                continue

            items = parse_m3u_or_txt(content)
            for ch_name, url in items:
                std_name = match_channel(ch_name, alias_map)
                if not std_name:
                    continue
                future_to_url[executor.submit(check_single, url, timeout, min_res)] = (std_name, url)

        # 处理结果
        for future in as_completed(future_to_url):
            std_name, url = future_to_url[future]
            valid, res = future.result()
            if not valid:
                continue
            if std_name not in all_valid:
                all_valid[std_name] = []
            if url not in all_valid[std_name]:
                all_valid[std_name].append(url)

    # 生成输出
    live_lines = []
    for group, channels in demo_groups.items():
        live_lines.append(f"{group},#genre#")
        for ch in channels:
            urls = all_valid.get(ch, [])[:max_num]
            for u in urls:
                live_lines.append(f"{ch},{u}")
        live_lines.append("")

    # 未使用的有效源
    for ch, urls in all_valid.items():
        if len(urls) > max_num:
            unused.extend(urls[max_num:])

    # 写入文件
    write_file_lines("output/lives.txt", live_lines)
    write_file_lines("output/unused.txt", unused)
    print(f"\n[完成] 有效源已保存到 output/lives.txt")
    print(f"[备用源] 已保存到 output/unused.txt（共{len(unused)}条）")

def check_single(url, timeout, min_res):
    """单链接检测：有效性+分辨率"""
    if not check_url_valid(url, timeout):
        return False, 0
    res = get_resolution(url, timeout)
    return res >= min_res, res