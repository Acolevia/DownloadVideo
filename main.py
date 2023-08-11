import time
import requests
from json import JSONDecodeError
import subprocess
import concurrent.futures
import os
import glob

# up主的id
user_id = 37961599
# up主视频的页数
total_page = 7

# 获取当前目录路径
current_directory = os.getcwd()
author = 'default'


def create_folder(folder_path):
    if not os.path.exists(folder_path):
        # 文件夹不存在，创建它
        os.makedirs(folder_path)
        print(f"创建文件夹: {folder_path}")


# 获取视频列表, max_retries=100 代表如果获取失败重试的次数
def get_video_lists(page, max_retries=100):
    global author
    url = 'https://api.bilibili.com/x/space/arc/search?mid={}&ps=30&tid=0&pn={}&keyword=&order=pubdate&jsonp=jsonp'.format(
        user_id, page)
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh,en;q=0.9,en-US;q=0.8,zh-CN;q=0.7,zh-TW;q=0.6",
        "cookie": "buvid3=52EE1424-8352-DE0D-C2F9-8CEFBD6D7D2024853infoc; i-wanna-go-back=-1; _uuid=D7F4D7102-F510C-9EFD-B44C-5A15BB3D2B9825216infoc; buvid4=79C7023E-28E0-B231-6510-54E406718DAA25965-022021913-c0D4n8mIkOPQS7cPZ5EOlQ%3D%3D; CURRENT_BLACKGAP=0; LIVE_BUVID=AUTO7016452474409017; rpdid=|(Rlllkm)mY0J'uYRlkRmRum; buvid_fp_plain=undefined; blackside_state=0; fingerprint=6c8532a24d1ddc22356289c4c2d1958f; buvid_fp=34e58163f7b4e31c1736ba5b8416e000; SESSDATA=c35a2a31%2C1662290982%2Ca3c0d%2A31; bili_jct=de750fd4e484b47f40b8bb42a5a72869; DedeUserID=73827743; DedeUserID__ckMd5=9d571d9b5b827b73; sid=c3w73yp7; b_ut=5; hit-dyn-v2=1; nostalgia_conf=-1; PVID=2; innersign=0; b_lsid=B710CBE88_180E5C4ABA4; bp_video_offset_73827743=662643097963855900; CURRENT_FNVAL=80; b_timer=%7B%22ffp%22%3A%7B%22333.1007.fp.risk_52EE1424%22%3A%22180E5C4B0BF%22%2C%22333.337.fp.risk_52EE1424%22%3A%22180E5C521EF%22%2C%22333.999.fp.risk_52EE1424%22%3A%22180E5C5494B%22%7D%7D",
        "origin": "https://space.bilibili.com",
        "referer": "https://space.bilibili.com/518973111/video?tid=0&page=2&keyword=&order=pubdate",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
    }

    for _ in range(max_retries):
        resp = requests.get(
            url=url,
            headers=headers
        )

        if resp.status_code != 200:
            print(f"Error: HTTP status code {resp.status_code}")
            time.sleep(1)  # wait for a while before retrying
            continue

        if not resp.text:
            print("Error: Response is empty")
            time.sleep(1)  # wait for a while before retrying
            continue

        try:
            js = resp.json()
        except JSONDecodeError:
            print("Error: Unable to parse JSON, trying again")
            time.sleep(1)  # wait for a while before retrying
            continue

        if 'code' in js and js['code'] == -799:
            print(f"Error: {js['message']}")
            time.sleep(1)  # wait for a while before retrying
            continue

        if 'data' not in js or 'list' not in js['data'] or 'vlist' not in js['data']['list']:
            print("Error: Unexpected response")
            time.sleep(1)  # wait for a while before retrying
            continue

        vlist = js['data']['list']['vlist']
        author = vlist[0]['author']
        bvid_list = [x.get('bvid') for x in vlist]
        return bvid_list

    print(f"Error: Failed to get data after {max_retries} attempts")
    return []


def download_videos(bv):
    url = 'https://www.bilibili.com/video/{}'.format(bv)
    print("download link", url, flush=True)
    command = ['you-get', '-o', folder_path, url]
    result = subprocess.run(command)
    if result.returncode != 0:
        raise RuntimeError(f'Failed to download video {bv}')
    print(f'Video {bv} downloaded successfully', flush=True)
    time.sleep(5)
    return bv


# 获取当前up主账号下全部视频的bv号
bv_lists = []
for i in range(1, total_page + 1):
    bv_lists.extend(get_video_lists(i))
    print(len(bv_lists), bv_lists)
    time.sleep(1)  # add a delay to avoid being blocked by the server

print(len(bv_lists), bv_lists)

# 在当前目录下创建up主名字的目录
folder_path = os.path.join(current_directory, author)
create_folder(folder_path)

# 多线程下载, max_workers=5 代表最多5个线程
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = {executor.submit(download_videos, bv): bv for bv in bv_lists}

for future in concurrent.futures.as_completed(futures):
    bv = futures[future]
    try:
        future.result()
    except Exception as e:
        print(f'Error downloading video {bv}: {e}', flush=True)

# 删除所有的 .xml 文件
xml_files = glob.glob(os.path.join(folder_path, '*.xml'))
for xml_file in xml_files:
    try:
        os.remove(xml_file)
        print(f'Successfully deleted {xml_file}')
    except Exception as e:
        print(f'Error deleting {xml_file}: {e}')
