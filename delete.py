import os

def delete_files(directory, match_type="suffix", match_value="(1)"):
    for root, dirs, files in os.walk(directory, topdown=False):
        for file in files:
            name, ext = os.path.splitext(file)
            file_path = os.path.join(root, file)
            try:
                if match_type == "suffix" and name.endswith(match_value):
                    os.remove(file_path)
                    print(f"Deleted: {file}")
                elif match_type == "prefix" and name.startswith(match_value):
                    os.remove(file_path)
                    print(f"Deleted: {file}")
                elif match_type == "contains" and match_value in name:
                    os.remove(file_path)
                    print(f"Deleted: {file}")
                elif match_type == "extension" and ext == match_value:
                    os.remove(file_path)
                    print(f"Deleted: {file}")
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
        # 检查并删除空文件夹
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            try:
                os.rmdir(dir_path)
                print(f"Deleted empty directory: {dir_path}")
            except OSError as e:
                # 如果目录不为空，忽略错误
                pass

if __name__ == "__main__":
    directory_to_search = "/home/HwHiAiUser/MasterPi/"  # 替换为你的目标目录
    match_type = "suffix"  # 替换为 "prefix", "contains", 或 "extension"
    match_value = "(1)"  # 替换为你的匹配值
    delete_files(directory_to_search, match_type, match_value)