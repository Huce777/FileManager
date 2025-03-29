"""
命令行文件管理系统 - 文件重命名与删除功能
支持通过命令行参数执行文件的重命名和删除操作
用法:
    python file_manager.py rename <原文件路径> <新文件名>
    python file_manager.py delete <文件路径>
"""

import sys
import os

# 7.软件支持命令行方式的文件重命名、删除操作

def rename_file(old_path, new_name):
    """重命名文件"""
    if not os.path.exists(old_path):
        print(f"错误: 文件 '{old_path}' 不存在")
        return False

    # 获取原文件的目录路径
    old_dir = os.path.dirname(old_path)
    # 构造新文件的完整路径
    new_path = os.path.join(old_dir, new_name)

    try:
        os.rename(old_path, new_path)
        print(f"文件已成功重命名为: {new_path}")
        return True
    except Exception as e:
        print(f"重命名文件时出错: {e}")
        return False


def delete_file(file_path):
    """删除文件"""
    if not os.path.exists(file_path):
        print(f"错误: 文件 '{file_path}' 不存在")
        return False

    try:
        os.remove(file_path)
        print(f"文件 '{file_path}' 已成功删除")
        return True
    except Exception as e:
        print(f"删除文件时出错: {e}")
        return False

"""
def main():
    # 检查命令行参数数量
    if len(sys.argv) < 2:
        print("错误: 未提供操作命令")
        print(__doc__)
        return

    command = sys.argv[1].lower()

    if command == "rename":
        if len(sys.argv) != 4:
            print("错误: rename 操作需要两个参数: 原文件路径和新文件名")
            print(__doc__)
            return
        old_path = sys.argv[2]
        new_name = sys.argv[3]
        rename_file(old_path, new_name)

    elif command == "delete":
        if len(sys.argv) != 3:
            print("错误: delete 操作需要一个参数: 文件路径")
            print(__doc__)
            return
        file_path = sys.argv[2]
        delete_file(file_path)

    else:
        print(f"错误: 未知命令 '{command}'")
        print(__doc__)
"""
"""
功能说明
    命令解析: 程序通过 sys.argv 获取命令行参数，并根据第一个参数判断用户想要执行的操作（重命名或删除）。
    文件重命名:
    检查原文件是否存在
    构造新文件的完整路径
    使用 os.rename() 执行重命名操作
    捕获并处理可能的异常
    文件删除:
    检查文件是否存在
    使用 os.remove() 执行删除操作
    捕获并处理可能的异常
    错误处理: 程序对各种可能的错误情况进行了处理，包括文件不存在、参数数量不足、操作失败等，并提供了相应的错误提示信息。
"""
"""
if __name__ == "__main__":
    main()
"""