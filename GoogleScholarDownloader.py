import csv
import os
import time
import requests
from urllib.parse import urlencode

# 配置
SLEEP_TIME = 1  # 下载PDF之间的延时(秒)
ARXIV_SEARCH_URL = "https://export.arxiv.org/api/query?search_query=all:"  # arXiv搜索链接
OUTPUT_FOLDER = "arxiv_pdfs"  # 保存PDF的文件夹
CSV_FILE = "reading_list.csv"  # 包含文献标题的CSV文件
REPLACE_SPACE = True  # 是否替换标题中的空格
SETTINGS_FILE = "settings.txt"  # 保存配置的文件
LEGAL_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.\'()_-+=[], ")
MAX_FILE_NAME_LENGTH = 200  # 文件名最大长度


def read_settings(file_path):
    """读取设置文件, 返回字典"""
    settings = {}
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                key, value = line.strip().split(" = ")
                settings[key] = value
    settings["SLEEP_TIME"] = int(settings.get("SLEEP_TIME", SLEEP_TIME))
    settings["OUTPUT_FOLDER"] = settings.get("OUTPUT_FOLDER", OUTPUT_FOLDER)
    settings["CSV_FILE"] = settings.get("CSV_FILE", CSV_FILE)
    # 保存为bool类型
    settings["REPLACE_SPACE"] = settings.get("REPLACE_SPACE", "True").lower() == "true"
    settings["MAX_FILE_NAME_LENGTH"] = int(settings.get("MAX_FILE_NAME_LENGTH", MAX_FILE_NAME_LENGTH))
    settings["SAVE_TYPE"] = settings.get("SAVE_TYPE", "pdf").lower()
    return settings
def write_settings(file_path, settings):
    """写入设置文件"""
    settings = {"SLEEP_TIME": SLEEP_TIME, "OUTPUT_FOLDER": OUTPUT_FOLDER, "CSV_FILE": CSV_FILE}
    print(f"没有找到配置文件……正在写入配置文件: {file_path}")
    input("除了以下设置，你还可以在文件中更改其他设置。按回车键继续……")
    settings["OUTPUT_FOLDER"] = input(f"保存PDF的文件夹 [{settings['OUTPUT_FOLDER']}]: ") or settings["OUTPUT_FOLDER"]
    settings["CSV_FILE"] = input(f"包含文献标题的CSV文件 [{settings['CSV_FILE']}]: ") or settings["CSV_FILE"]

    with open(file_path, 'w') as file:
        file.write(f"# 配置\n")
        file.write(f"# 你可以在这里修改相关设置\n")
        for key, value in settings.items():
            file.write(f"{key} = {value}\n")
   


def read_csv(file_path):
    """读取CSV文件，返回文章标题列表"""
    titles = []
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            title = row['Title']  # 假设CSV包含"Title"列
            title = "".join(c if c in LEGAL_CHARS else " " for c in title)
            titles.append(title)
    return titles

def search_arxiv(title):
    """在arXiv上搜索文章"""
    
    try:
        search_url = ARXIV_SEARCH_URL + urlencode({"title": title})
        response = requests.get(search_url)
    except Exception as e:
        print(f"搜索失败: {title} ({e})")
        # 重试一次
        time.sleep(SLEEP_TIME)
        try:
            response = requests.get(search_url)
        except Exception as e:
            print(f"搜索失败: {title} ({e})")
            return None

    
    if response.status_code != 200:
        print(f"搜索失败: {title} (状态码: {response.status_code})")
        return None

    # 简单解析返回的XML，找到PDF链接
    if "pdf" in response.text:
        start = response.text.find('<link title="pdf" href="http://arxiv.org/pdf/')
        if start != -1:
            end = response.text.find('" rel="related" type="application/pdf"/>', start)
            pdf_url = response.text[start + 24:end]  # 截取PDF链接
            return pdf_url
    return None
def file_name_parser(name, settings):
    if settings["REPLACE_SPACE"]:
        name = f"{name}".replace(" ", "_")
    # 如果文件名太长，则截断
    if len(name) > settings["MAX_FILE_NAME_LENGTH"]:
        name = name[:settings["MAX_FILE_NAME_LENGTH"]]
    # 加上后缀
    return f'{name}.{settings["SAVE_TYPE"]}'
def download_pdf(url, title):# 如果下载成功，则返回True
    """下载PDF文件"""
    # 如果文件已存在，则跳过
    file_name = f"{title[:50]}.pdf"
    file_path = os.path.join(OUTPUT_FOLDER, file_name)
    if os.path.exists(file_path):
        print(f"-文件已存在: {file_name}")
        return True
    response = requests.get(url, stream=True)
    if response.status_code == 200 and "application/pdf" in response.headers.get("Content-Type", ""):
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        print(f"成功下载: {file_name}")
        return True
    else:
        print(f"无法下载PDF: {title} (URL: {url})")
        return False
def exists(file_name, settings):
    """检查文件是否已经存在"""
    return os.path.exists(os.path.join(settings["OUTPUT_FOLDER"], file_name))
def main():
    """主程序"""
    
    settings = read_settings(SETTINGS_FILE)
    titles = read_csv(settings["CSV_FILE"])
    nTitles = len(titles)
    nSuccess = 0
    Failed = []
    for i in range(nTitles):
        title = titles[i]
        
        # 如果文献已经下载，则跳过
        if exists(file_name_parser(title, settings), settings):
            print(f"已存在: {title}")
            continue
        print(f"正在搜索 {i}/{nTitles}\n{title}")
        pdf_url = search_arxiv(title)
        if pdf_url:
            print(f"-找到PDF: {pdf_url}")
            # 为了防止ip被封，加入延时
            time.sleep(settings["SLEEP_TIME"])  
            succ = download_pdf(pdf_url, title)
            if succ:
                nSuccess += 1
            else:
                Failed.append(title)
        else:
            print(f"!未找到PDF: {title}")
    print(f"下载完成, 成功下载: {nSuccess}/{nTitles}")
    if Failed:
        print("以下文章下载失败:")
        for title in Failed:
            print(f"- {title}")
if __name__ == "__main__":
    main()
