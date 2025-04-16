import re
import csv
from PyPDF2 import PdfReader
import os
from typing import List, Dict, Union, Optional
import pandas as pd


def extract_references(text: str) -> List[str]:
    """
    从参考文献文本中提取并分割单条参考文献
    
    参数:
        text: 包含参考文献的完整文本
    
    返回:
        分割后的参考文献列表（已清洗）
    """
    # 1.确定参考文献的格式
    REF_PATTERNS = [
        #APA格式: Author (Year). Title. Journal, Pages
        {
            'name': 'APA',
            'regex': r'(?P<authors>.+?) \((?P<year>\d{4})\)\. (?P<title>[^\.]+)\. (?P<source>[^,]+), (?P<pages>\d+-\d+)',
        },

        {
            'name': 'MLA',
            'regex': r'^(?P<authors>.+?)\. "(?P<title>[^"]+)"\. (?P<source>.+?) (?P<year>\d{4}): (?P<pages>\d+-\d+)',
        },

        {
            'name': 'Chicago',
            'regex': r'^(?P<authors>.+?)\. (?P<year>\d{4})\. "(?P<title>[^"]+)"\. (?P<source>.+?) no\.?(?P<issue>\d+): (?P<pages>\d+-\d+)',
        },

        {
            'name': 'Conference',
            'regex': r'^(?P<authors>.+?)\. (?P<title>[^\.]+)\. In: (?P<source>.+?), (?P<year>\d{4}), pp?\.?(?P<pages>\d+-\d+)',
        },

        {
            'name': 'Book',
            'regex': r'^(?P<authors>.+?)\. (?P<title>[^\.]+)\. (?P<publisher>.+?), (?P<year>\d{4})',
        }
    ]
    # 2. 从前向后尝试匹配REF_PATTERNS中的每个模式,直到找到一个匹配的模式
    for pattern in REF_PATTERNS:
        match = re.search(pattern['regex'], text, re.IGNORECASE)
        if match:
            print(f"找到参考文献格式: {pattern['name']}")
        else:
            print("未找到参考文献格式")
            return []

    # 3. 多模式分割（支持6种常见编号格式）
    split_patterns = [
        r'\n\d+\.',        # 1. 
        r'\n\[\d+\]',      # [1]
        r'\n\([A-Za-z]?\d+\)',  # (1) 或 (A1)
        r'\n•\s+',         # • 项目符号
        r'\n-\s+',         # - 项目符号
        r'\n\*?\d+\*?\s+'  # 1 或 *1* 
    ]
    
    # 尝试不同分割模式直到成功
    for pattern in split_patterns:
        references_list = re.split(pattern, references_text)
        if len(references_list) > 1:  # 如果成功分割
            break
    
    # 4. 后处理
    cleaned_references = []
    for ref in references_list:
        ref = ref.strip()
        # 移除行首的符号和空白
        ref = re.sub(r'^[•\-*]\s*', '', ref)
        # 合并跨行引用（保留必要的换行）
        ref = re.sub(r'\n(?![A-Za-z]\.\s)', ' ', ref)  # 保留如"J. Smith"中的换行
        if ref and len(ref) > 10:  # 过滤过短文本
            cleaned_references.append(ref)
    
    return cleaned_references

def parse_reference(ref_text: str) -> Optional[Dict[str, Union[str, List[str]]]]:
    """解析单条参考文献为结构化字典"""
    # 预定义格式模式（按优先级排序）
    patterns = [
        # APA格式: Author (Year). Title. Journal, Pages
        {
            'name': 'APA',
            'regex': r'^(?P<authors>.+?) \((?P<year>\d{4})\)\. (?P<title>[^\.]+)\. (?P<source>[^,]+), (?P<pages>\d+-\d+)',
            'examples': [
                "Smith, J. (2020). Deep Learning for NLP. Journal of AI, 123-130",
                "Lee, S. et al. (2019). Transformer Models. arXiv preprint"
            ]
        },
        # MLA格式: Author. "Title". Journal Year: Pages
        {
            'name': 'MLA',
            'regex': r'^(?P<authors>.+?)\. "(?P<title>[^"]+)"\. (?P<source>.+?) (?P<year>\d{4}): (?P<pages>\d+-\d+)',
            'examples': [
                'Johnson, B. "Attention Mechanisms". Neural Computing 2021: 45-50'
            ]
        },
        # Chicago格式: Author. Year. "Title". Journal no: Pages
        {
            'name': 'Chicago',
            'regex': r'^(?P<authors>.+?)\. (?P<year>\d{4})\. "(?P<title>[^"]+)"\. (?P<source>.+?) no\.?(?P<issue>\d+): (?P<pages>\d+-\d+)',
            'examples': [
                'Wang, L. 2018. "BERT Pretraining". AI Research 3: 1120-1135'
            ]
        },
        # 会议论文格式: Author. Title. In: Conference, Year, Pages
        {
            'name': 'Conference',
            'regex': r'^(?P<authors>.+?)\. (?P<title>[^\.]+)\. In: (?P<source>.+?), (?P<year>\d{4}), pp?\.?(?P<pages>\d+-\d+)',
            'examples': [
                'Chen, H. Neural Architectures. In: ACL 2022, pp.100-110'
            ]
        },
        # 书籍格式: Author. Title. Publisher, Year
        {
            'name': 'Book',
            'regex': r'^(?P<authors>.+?)\. (?P<title>[^\.]+)\. (?P<publisher>.+?), (?P<year>\d{4})',
            'examples': [
                'Goodfellow, I. Deep Learning. MIT Press, 2016'
            ]
        }
    ]

    # 尝试匹配每种格式
    for pattern in patterns:
        match = re.search(pattern['regex'], ref_text, re.IGNORECASE)
        if match:
            result = match.groupdict()
            result['type'] = pattern['name']
            
            # 处理作者字段（分割多作者）
            if 'authors' in result:
                result['authors'] = [a.strip() for a in re.split(r', | and | et al\.?', result['authors']) if a.strip()]
            
            # 添加原始文本用于校验
            result['raw_text'] = ref_text 
            return result

    # 未匹配的格式返回基础信息
    return {
        'raw_text': ref_text,
        'type': 'unknown',
        'title': re.sub(r'\.$', '', ref_text[:100]) + ('...' if len(ref_text)>100 else '')
    }

def references_to_dataframe(references: List[str]) -> pd.DataFrame:
    """将参考文献列表转换为结构化DataFrame"""
    parsed_data = []
    
    for ref in references:
        parsed = parse_reference(ref)
        if parsed:
            # 展开作者列表为分号分隔字符串（方便CSV存储）
            if 'authors' in parsed and isinstance(parsed['authors'], list):
                parsed['authors'] = '; '.join(parsed['authors'])
            
            parsed_data.append(parsed)
    
    # 创建DataFrame并标准化列顺序
    df = pd.DataFrame(parsed_data)
    if not df.empty:
        # 确保必备字段存在
        for col in ['type', 'authors', 'year', 'title', 'source']:
            if col not in df.columns:
                df[col] = None
                
        # 列排序
        base_columns = ['type', 'authors', 'year', 'title', 'source', 'publisher', 'pages', 'issue', 'raw_text']
        present_columns = [col for col in base_columns if col in df.columns]
        df = df[present_columns + [c for c in df.columns if c not in base_columns]]
    
    return df


def extract_references_from_pdf(pdf_path):
    """
    提取PDF文件中的参考文献部分
    :param pdf_path: PDF文件路径
    :return: 参考文献文本，去除空行和换行符
    """
    try:
        reader = PdfReader(pdf_path)
        full_text = ""

        # 遍历PDF的每一页，合并文本
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"

        # 查找REFERENCES部分
        match = re.search(r'\bREFERENCES\b(.*)', full_text, re.IGNORECASE | re.DOTALL)
        if not match:
            print("未找到REFERENCES部分。")
            return []

        # 提取REFERENCES部分的文本
        references_text = match.group(1)
        #删除多余的空行和换行符
        references_text = re.sub(r'\n+', '', references_text).strip()
        # 使用正则表达式分割每条参考文献
        references_list = re.split(r'\n\d+\.|\n\[\d+\]', references_text)  # 按编号分割
        references_list = [ref.strip() for ref in references_list if ref.strip()]  # 去除空白
        print(f'references_text: {references_text}')

        return references_list

    except Exception as e:
        print(f"提取参考文献时出错: {e}")
        return []

    except Exception as e:
        print(f"提取参考文献时出错: {e}")
        return []

def save_references_to_csv(references, csv_path):
    """
    将参考文献保存到CSV文件
    :param references: 参考文献列表
    :param csv_path: CSV文件路径
    """
    try:
        if os.path.exists(csv_path):
            print(f"-文件已存在: {csv_path}")
            overwirte = input("是否覆盖文件? (y/n): ").strip().lower()
            if overwirte != 'y':
                print("操作已取消。")
                return
        else:
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            print(f"正在创建文件: {csv_path}")
        with open(csv_path, mode='w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Reference"])  # 写入表头
            for ref in references:
                writer.writerow([ref])
        print(f"参考文献已保存到: {csv_path}")
    except Exception as e:
        print(f"保存参考文献时出错: {e}")

def main():
    # 用户输入PDF文件路径和CSV保存路径
    source_pdf_path = input("请输入PDF文件路径: ").strip()
    output_csv_path = input("请输入保存参考文献的CSV文件路径: ").strip()

    # 提取参考文献
    print("正在提取参考文献...")
    references = extract_references_from_pdf(source_pdf_path)

    if references:
        clean_references = []
        for ref in references:
            parsed_ref = extract_references(ref)
            if parsed_ref:
                clean_references.append(parsed_ref['raw_text'])
        print(f"成功提取到 {len(clean_references)} 条参考文献。")
        print("参考文献列表:")
        # for i, ref in enumerate(clean_references, 1):
        #     print(f"{i}. {ref}")
        # # 保存到CSV文件
        save_references_to_csv(clean_references, output_csv_path)
    else:
        print("未能提取到参考文献。")

if __name__ == "__main__":
    main()