import os
import zipfile

def batch_unzip(directory):
    # 遍历指定目录下的所有文件
    for filename in os.listdir(directory):
        # 检查文件是否为ZIP文件
        if filename.endswith(".zip"):
            # 构建完整的文件路径
            file_path = os.path.join(directory, filename)
            # 创建解压目录，目录名与ZIP文件名相同（去掉.zip后缀）
            extract_dir = os.path.join(directory, filename[:-4])
            os.makedirs(extract_dir, exist_ok=True)
            
            # 打开ZIP文件并解压
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            print(f"解压完成: {filename} -> {extract_dir}")

if __name__ == "__main__":
    # 指定要解压的目录
    target_directory = "D:\\thu\\courses_sem4"
    
    # 调用批量解压函数
    batch_unzip(target_directory)