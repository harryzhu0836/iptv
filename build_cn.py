import os
import re

def parse_and_classify():
    # 优先使用本地拉取到的最新 m3u 文件（保证数据跟上游同步）
    files = ["countries/cn.m3u", "countries/hk.m3u", "countries/tw.m3u"]
    raw_content = ""
    
    for filepath in files:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                raw_content += f.read() + "\n"

    if not raw_content:
        print("未找到源 M3U 文件！")
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
        
        # 去重
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

    # 按类别组织顺序
    categories = [
        ("中央电视台", cctv_list),
        ("各省卫视", weishee_list),
        ("地方电视台", local_list),
        ("港澳台频道", gangaotai_list)
    ]

    output_lines = ["#EXTM3U"]
    
    for group_name, channel_list in categories:
        for info, stream_url, _ in channel_list:
            # 注入 group-title 属性供 MoonTVPlus 解析分类
            if 'group-title="' in info:
                info = re.sub(r'group-title="[^"]*"', f'group-title="{group_name}"', info)
            else:
                info = info.replace('#EXTINF:-1', f'#EXTINF:-1 group-title="{group_name}"')
            
            output_lines.append(info)
            output_lines.append(stream_url)

    # 在根目录生成专属分类文件 cn_custom.m3u
    with open("cn_custom.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines) + "\n")

    print(f"提取完成：央视 {len(cctv_list)} 个、卫视 {len(weishee_list)} 个、地方台 {len(local_list)} 个、港澳台 {len(gangaotai_list)} 个。")

if __name__ == "__main__":
    parse_and_classify()
