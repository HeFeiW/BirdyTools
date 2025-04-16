import requests
from bs4 import BeautifulSoup

# 配置
# BASE_URL = "https://scholar.google.com"  # 基础URL
# SEARCH_URL = "https://scholar.google.com/scholar?q=machine+learning"  # 示例搜索链接
BASE_URL = "https://arxiv.org"  # 基础URL
SEARCH_URL = "https://arxiv.org/search/?query=machine+learning&searchtype=all&source=header"  # 示例搜索链接
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

# 指定要查找的特征
TARGET_KEYWORD = "arxiv"  # 关键字，例如查找PDF链接

def find_target_link(url, keyword):
    """在网页中查找包含指定关键字的链接"""
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers=headers)

    # 检查请求是否成功
    if response.status_code != 200:
        print(f"无法访问页面: {url} (状态码: {response.status_code})")
        return None

    # 解析HTML内容
    soup = BeautifulSoup(response.text, 'html.parser')
    # 保存html文件
    with open('html.html', 'w', encoding='utf-8') as file:
        file.write(response.text)

    # 遍历所有链接
    for link in soup.find_all('a', href=True):
        href = link['href']
        text = link.get_text(strip=True)
        if keyword.lower() in text.lower() or keyword.lower() in href.lower():
            print(f"找到链接: {text} -> {href}")
            # 补全相对链接
            if not href.startswith("http"):
                href = BASE_URL + href
            return href

    print(f"未找到包含关键字 '{keyword}' 的链接")
    return None

def jump_to_link(link):
    """跳转到指定链接并显示页面内容"""
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(link, headers=headers)

    # 检查请求是否成功
    if response.status_code == 200:
        print(f"成功跳转到链接: {link}")
        print(response.text[:500])  # 打印部分HTML内容
    else:
        print(f"跳转失败: {link} (状态码: {response.status_code})")

def main():
    """主程序"""
    SEARCH_URL = input("请输入要搜索的链接: ") or SEARCH_URL
    TARGET_KEYWORD = input("请输入要查找的关键字: ") or TARGET_KEYWORD
    print(f"正在搜索链接: {SEARCH_URL}")
    print(f"正在搜索链接中包含关键字 '{TARGET_KEYWORD}' 的链接...")
    target_link = find_target_link(SEARCH_URL, TARGET_KEYWORD)
    if target_link:
        print(f"跳转到找到的链接: {target_link}")
        jump_to_link(target_link)

if __name__ == "__main__":
    main()
