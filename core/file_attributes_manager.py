import os
import stat
import sys
import ctypes
# 3.软件支持文件属性的文字显示，修改。如隐藏属性、系统文件属性、只读文件属性。
# def is_admin():
#     try:
#         return ctypes.windll.shell32.IsUserAnAdmin()
#     except:
#         return False
#
# if is_admin():
#     import tkinter as tk
#     from tkinter import ttk, messagebox, filedialog,simpledialog
#     import os
#     import stat

class FileAttributesManager:
    """
    文件属性管理类，用于显示和修改文件的属性。
    支持的属性包括：隐藏、系统文件、只读。
    """

    def __init__(self, file_path):
        """
        初始化文件属性管理器

        Args:
            file_path (str): 文件路径
        """
        self.file_path = file_path

    def display_attributes(self):
        """
        显示文件的属性文字描述

        Returns:
            str: 文件属性的文字描述
        """
        try:
            # 获取文件状态
            file_stats = os.stat(self.file_path)

            # 获取文件的属性标志
            file_mode = file_stats.st_mode

            # 分析文件属性
            attributes = []

            # 检查隐藏属性（Windows 平台）
            if os.name == 'nt':
                # 使用 os.stat 的 st_file_attributes 字段（Windows 特有）
                file_attributes = file_stats.st_file_attributes

                if file_attributes & stat.FILE_ATTRIBUTE_HIDDEN:
                    attributes.append("隐藏")
                if file_attributes & stat.FILE_ATTRIBUTE_SYSTEM:
                    attributes.append("系统文件")
                if file_attributes & stat.FILE_ATTRIBUTE_READONLY:
                    attributes.append("只读")
            else:
                # 对于非 Windows 平台，使用权限位判断只读属性
                if not (file_mode & stat.S_IWUSR):
                    attributes.append("只读")

                # 隐藏属性在类 Unix 系统中通常由文件名前的 '.' 表示
                if os.path.basename(self.file_path).startswith('.'):
                    attributes.append("隐藏")

            # 如果没有特殊属性，添加默认描述
            if not attributes:
                attributes.append("普通文件")

            return ", ".join(attributes)

        except FileNotFoundError:
            return "文件未找到"
        except PermissionError:
            return "权限不足，无法获取文件属性"
        except Exception as e:
            return f"获取文件属性时出错: {str(e)}"

    def modify_attribute(self, attribute_name, enable):
        """
        修改文件的指定属性

        Args:
            attribute_name (str): 属性名称（"hidden", "system", "readonly"）
            enable (bool): 是否启用该属性

        Returns:
            bool: 修改是否成功
        """
        try:
            if not os.path.exists(self.file_path):
                print(f"文件未找到: {self.file_path}")
                return False

            if os.name == 'nt':
                # Windows 平台处理
                if attribute_name.lower() == "hidden":
                    attribute_flag = stat.FILE_ATTRIBUTE_HIDDEN
                elif attribute_name.lower() == "system":
                    attribute_flag = stat.FILE_ATTRIBUTE_SYSTEM
                elif attribute_name.lower() == "readonly":
                    attribute_flag = stat.FILE_ATTRIBUTE_READONLY
                else:
                    return False

                # 获取当前文件属性
                file_stats = os.stat(self.file_path)
                current_attributes = file_stats.st_file_attributes

                # 修改属性
                if enable:
                    new_attributes = current_attributes | attribute_flag
                else:
                    new_attributes = current_attributes & ~attribute_flag

                # 应用新属性
                os.set_file_attributes(self.file_path, new_attributes)
                return True
            else:
                # 非 Windows 平台处理（主要处理只读属性）
                if attribute_name.lower() == "readonly":
                    # 设置只读属性
                    current_mode = os.stat(self.file_path).st_mode
                    if enable:
                        # 去掉写权限
                        new_mode = current_mode & ~stat.S_IWUSR
                    else:
                        # 添加写权限
                        new_mode = current_mode | stat.S_IWUSR
                    os.chmod(self.file_path, new_mode)
                    return True
                elif attribute_name.lower() == "hidden":
                    # 类 Unix 系统中隐藏文件通常由文件名前的 '.' 表示
                    base_name = os.path.basename(self.file_path)
                    dir_name = os.path.dirname(self.file_path)
                    new_name = f".{base_name}" if enable and not base_name.startswith('.') else base_name.replace('.',
                                                                                                                  '', 1)
                    new_path = os.path.join(dir_name, new_name)
                    os.rename(self.file_path, new_path)
                    return True
                else:
                    # 系统属性在类 Unix 系统中通常无法直接修改
                    return False

        except FileNotFoundError:
            print(f"文件未找到: {self.file_path}")
            return False
        except PermissionError:
            print(f"权限不足，无法修改文件属性: {self.file_path}")
            return False
        except Exception as e:
            print(f"修改文件{self.file_path}属性时出错: {str(e)}")
            return False

"""
# 测试代码
if __name__ == "__main__":
    # 测试文件路径
    test_file = "test.txt"

    # 创建测试文件
    with open(test_file, "w") as f:
        f.write("这是一个测试文件")

    # 创建文件属性管理器
    manager = FileAttributesManager(test_file)

    # 测试显示文件属性
    print("当前文件属性:", manager.display_attributes())

    # 测试修改只读属性
    if manager.modify_attribute("readonly", True):
        print("已成功设置只读属性")
        print("当前文件属性:", manager.display_attributes())
    else:
        print("设置只读属性失败")

    # 测试修改隐藏属性（Windows 平台）
    if os.name == 'nt':
        if manager.modify_attribute("hidden", True):
            print("已成功设置隐藏属性")
            print("当前文件属性:", manager.display_attributes())
        else:
            print("设置隐藏属性失败")

    # 测试修改系统文件属性（Windows 平台）
    if os.name == 'nt':
        if manager.modify_attribute("system", True):
            print("已成功设置系统文件属性")
            print("当前文件属性:", manager.display_attributes())
        else:
            print("设置系统文件属性失败")

    # 清理测试文件
    try:
        os.remove(test_file)
        print("测试文件已删除")
    except Exception as e:
        print(f"删除测试文件时出错: {str(e)}")
"""