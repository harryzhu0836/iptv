import os
import re
import requests

def parse_and_classify():
    # 数据源：兼顾中文频道与中国/港澳台区域
    files = ["streams/zho.m3u", "streams/cn.m3u", "streams/hk.m3u", "streams/tw.m3u"]
    raw_content = ""
    
    # 优先读取本地文件，无本地文件则在线拉取
    for filepath in files:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                raw_content += f.read() + "\n"
        else:
            url = f"https://raw.githubusercontent.com/iptv-org/iptv/master/{filepath}"
            try:
                res = requests.get(url, timeout=10)
                if res.status_code == 200 and len(res.text) > 100:
                    raw_content += res.text + "\n"
            except Exception as e:
                print(f"请求失败: {url}, 错误: {e}")

    if not raw_content.strip():
        print("未获取到有效的播放列表内容！")
        return

    # 正则提取每个频道（支持跨行/多属性的 #EXTINF 块）
    pattern = re.compile(r'(#EXTINF:-1[^\n]+\n[^\n]+)', re.MULTILINE)
    items = pattern.findall(raw_content)
    
    cctv_list = []       # 中央电视台
    weishee_list = []   # 各省卫视
    local_list = []     # 地方电视台
    gangaotai_list = []  # 港澳台频道
    
    seen_urls = set()

    for item in items:
        lines = item.strip().split("\n")
        if len(lines) < 2:
            continue
            
        extinf_line, stream_url = lines[0], lines[1].strip()
        
        # URL 去重
        if stream_url in seen_urls:
            continue
        seen_urls.add(stream_url)
        
        # 提取频道显示名称（位于逗号后的部分）
        channel_name = extinf_line.split(",")[-1] if "," in extinf_line else extinf_line
        
        # 分类判断
        if any(keyword in channel_name.upper() for keyword in ["CCTV", "CGTN"]):
            group_name = "中央电视台"
            target_list = cctv_list
        elif "卫视" in channel_name:
            group_name = "各省卫视"
            target_list = weishee_list
        elif any(keyword in channel_name for keyword in ["Phoenix", "TVB", "CTi", "中天", "三立", "翡翠", "明珠", "凤凰", "NEWS"]):
            group_name = "港澳台频道"
            target_list = gangaotai_list
        else:
            group_name = "地方电视台"
            target_list = local_list

        # 精确处理 group-title：如果不包含则插入，如果包含则更新
        if 'group-title="' in extinf_line:
            new_extinf = re.sub(r'group-title="[^"]*"', f'group-title="{group_name}"', extinf_line)
        else:
            # 插入到 #EXTINF:-1 后面，确保不破坏后续属性与逗号
            new_extinf = extinf_line.replace('#EXTINF:-1', f'#EXTINF:-1 group-title="{group_name}"', 1)
            
        target_list.append((new_extinf, stream_url))

    # 按规范组装输出
    categories = [
        ("中央电视台", cctv_list),
        ("各省卫视", weishee_list),
        ("地方电视台", local_list),
        ("港澳台频道", gangaotai_list)
    ]

    output_lines = ["#EXTM3U"]
    for _, channel_list in categories:
        for extinf, stream_url in channel_list:
            output_lines.append(extinf)
            output_lines.append(stream_url)

    with open("cn_custom.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")

    print(f"生成成功：央视({len(cctv_list)})、卫视({len(weishee_list)})、地方台({len(local_list)})、港澳台({len(gangaotai_list)})")

if __name__ == "__main__":
    parse_and_classify()
