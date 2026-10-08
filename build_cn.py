import os
import re
import requests

def parse_and_classify():
    # iptv-org 最新结构的路径是在 streams/ 下
    files = ["streams/cn.m3u", "streams/hk.m3u", "streams/tw.m3u"]
    raw_content = ""
    
    # 1. 优先读取本地 Fork 仓库中的 streams/ 目录文件
    for filepath in files:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                raw_content += f.read() + "\n"
        else:
            # 2. 本地若没有则尝试去旧路径 countries/ 找
            old_path = filepath.replace("streams/", "countries/")
            if os.path.exists(old_path):
                with open(old_path, "r", encoding="utf-8") as f:
                    raw_content += f.read() + "\n"
            else:
                # 3. 在线兜底下载
                urls = [
                    f"https://raw.githubusercontent.com/iptv-org/iptv/master/{filepath}",
                    f"https://iptv-org.github.io/iptv/{filepath}"
                ]
                for url in urls:
                    try:
                        res = requests.get(url, timeout=10)
                        if res.status_code == 200 and len(res.text) > 100:
                            raw_content += res.text + "\n"
                            break
                    except Exception as e:
                        print(f"请求失败: {url}, 错误: {e}")

    if not raw_content.strip():
        print("未获取到有效的播放列表内容！")
        return

    # 解析所有的播放节点
    items = re.findall(r"(#EXTINF:[^\n]+\n[^\n]+)", raw_content)
    
    cctv_list = []       # 中央电视台
    weishee_list = []   # 各省卫视
    local_list = []     # 地方电视台
    gangaotai_list = []  # 港澳台频道
    
    seen_urls = set()

    for item in items:
        lines = item.strip().split("\n")
        if len(lines) < 2:
            continue
            
        info, stream_url = lines[0], lines[1].strip()
        
        # 简单去重
        if stream_url in seen_urls:
            continue
        seen_urls.add(stream_url)
        
        # 匹配归类规则
        if any(keyword in info for keyword in ["CCTV", "CGTN"]):
            group = "中央电视台"
            cctv_list.append((info, stream_url, group))
        elif "卫视" in info:
            group = "各省卫视"
            weishee_list.append((info, stream_url, group))
        elif any(keyword in info for keyword in ["Phoenix", "TVB", "CTi", "中天", "三立", "翡翠", "明珠", "凤凰"]):
            group = "港澳台频道"
            gangaotai_list.append((info, stream_url, group))
        else:
            group = "地方电视台"
            local_list.append((info, stream_url, group))

    categories = [
        ("中央电视台", cctv_list),
        ("各省卫视", weishee_list),
        ("地方电视台", local_list),
        ("港澳台频道", gangaotai_list)
    ]

    output_lines = ["#EXTM3U"]
    for group_name, channel_list in categories:
        for info, stream_url, _ in channel_list:
            if 'group-title="' in info:
                info = re.sub(r'group-title="[^"]*"', f'group-title="{group_name}"', info)
            else:
                info = info.replace('#EXTINF:-1', f'#EXTINF:-1 group-title="{group_name}"')
            output_lines.append(info)
            output_lines.append(stream_url)

    # 写入文件
    with open("cn_custom.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")

    print(f"处理完成：央视({len(cctv_list)})、卫视({len(weishee_list)})、地方台({len(local_list)})、港澳台({len(gangaotai_list)})")

if __name__ == "__main__":
    parse_and_classify()
