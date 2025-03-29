import zipfile
import os

# 4.软件支持对文件的压缩与解压缩（可直接使用 python的库）

def compress_files(zip_filename, *files_or_folders):
    """
    压缩文件或文件夹到指定的 ZIP 文件中

    :param zip_filename: 压缩后的 ZIP 文件名
    :param files_or_folders: 需要压缩的文件或文件夹路径
    """
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for item in files_or_folders:
            if os.path.isfile(item):
                zipf.write(item, arcname=os.path.basename(item))
                print(f"Added file: {item}")
            elif os.path.isdir(item):
                for root, dirs, files in os.walk(item):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, item)
                        zipf.write(file_path, arcname=os.path.join(os.path.basename(item), arcname))
                        print(f"Added file: {file_path}")
            else:
                print(f"Warning: {item} does not exist, skipped.")


def extract_zip(zip_filename, extract_to):
    """
    解压缩 ZIP 文件到指定目录

    :param zip_filename: ZIP 文件名
    :param extract_to: 解压缩的目标目录
    """
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)

    with zipfile.ZipFile(zip_filename, 'r') as zipf:
        zipf.extractall(extract_to)
        print(f"Extracted all files to {extract_to}")

"""
def main():
    print("文件压缩与解压缩工具")
    print("1. 压缩文件或文件夹")
    print("2. 解压缩文件")

    choice = input("请选择操作 (1 或 2): ")

    if choice == '1':
        zip_filename = input("请输入压缩后的 ZIP 文件名: ")
        items = []
        while True:
            item = input("请输入要压缩的文件或文件夹路径 (输入 'done' 结束): ")
            if item.lower() == 'done':
                break
            items.append(item)
        if items:
            compress_files(zip_filename, *items)
            print(f"压缩完成，生成文件: {zip_filename}")
        else:
            print("没有指定任何文件或文件夹，压缩操作取消。")

    elif choice == '2':
        zip_filename = input("请输入要解压缩的 ZIP 文件名: ")
        extract_to = input("请输入解压缩的目标目录: ")
        if os.path.exists(zip_filename):
            extract_zip(zip_filename, extract_to)
        else:
            print(f"ZIP 文件 {zip_filename} 不存在，解压缩操作取消。")

    else:
        print("无效的选择，操作取消。")


if __name__ == "__main__":
    main()
"""