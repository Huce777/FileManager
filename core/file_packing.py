import os
import zipfile

# 6.软件支持文件夹及子文件夹打包操作

def zip_folder(folder_path, output_path):
    """
    将文件夹及其子文件夹打包成ZIP文件

    参数:
        folder_path (str): 要打包的文件夹路径
        output_path (str): 输出的ZIP文件路径
    """
    # 创建一个ZIP文件对象
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # 遍历文件夹中的所有文件和子文件夹
        for root, dirs, files in os.walk(folder_path):
            # 计算当前文件或文件夹相对于要打包的文件夹的相对路径
            relative_path = os.path.relpath(root, folder_path)
            # 如果是根文件夹，直接添加空目录项
            if relative_path == '.':
                zipf.write(root, arcname=os.path.basename(folder_path))
            else:
                # 添加子文件夹的目录项
                zipf.write(root, arcname=os.path.join(os.path.basename(folder_path), relative_path))
            # 添加文件
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.join(relative_path, file)
                zipf.write(file_path, arcname=os.path.join(os.path.basename(folder_path), arcname))
    print(f"文件夹 {folder_path} 已成功打包为 {output_path}")

"""
zip_folder函数:
接收两个参数：folder_path（要打包的文件夹路径）和output_path（输出的ZIP文件路径）
使用zipfile.ZipFile创建一个ZIP文件对象，压缩方法为ZIP_DEFLATED（压缩）
使用os.walk遍历文件夹及其子文件夹
对于每个文件和文件夹，计算其相对于要打包文件夹的相对路径，并将其添加到ZIP文件中
测试代码:
提示用户输入要打包的文件夹路径和输出的ZIP文件路径
调用zip_folder函数进行打包操作
"""
"""
# 测试代码
if __name__ == "__main__":
    folder_to_zip = input("请输入要打包的文件夹路径: ")
    output_zip = input("请输入输出的ZIP文件路径: ")
    zip_folder(folder_to_zip, output_zip)
"""