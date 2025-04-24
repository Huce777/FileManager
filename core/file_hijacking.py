import os
import subprocess
from tkinter import Tk, Button, filedialog

# 8.软件可以对指定文件格式识别，并调用相应外挂软件进行显示，至少支持两种外挂软件，如：图像显示软件、 word 等文字处理软件。

class FileManager:
    def __init__(self, master):
        self.master = master
        master.title("文件管理系统")

        # 创建按钮
        self.select_button = Button(master, text="选择文件", command=self.select_file)
        self.select_button.pack()

        self.show_button = Button(master, text="显示文件", command=self.show_file)
        self.show_button.pack()

        self.selected_file = None

    # def view_file(file_path):
    #     file_extension = os.path.splitext(file_path)[1].lower()
    #
    #     if file_extension in ['.jpg', '.jpeg', '.png', '.bmp']:
    #         try:
    #             subprocess.Popen(['i_view32.exe', file_path])
    #         except Exception as e:
    #             print(f"打开文件时出错: {e}")
    #     elif file_extension in ['.doc', '.docx']:
    #         try:
    #             subprocess.Popen(['winword.exe', file_path])
    #         except Exception as e:
    #             print(f"打开文件时出错: {e}")
    #     else:
    #         print("不支持的文件格式")

    def select_file(self):
        # 打开文件选择对话框
        self.selected_file = filedialog.askopenfilename()

    def show_file(self):
        if self.selected_file:
            file_extension = os.path.splitext(self.selected_file)[1].lower()

            if file_extension in ['.jpg', '.jpeg', '.png', '.bmp']:
                # 调用图像查看软件（如IrfanView）
                self.open_with_external_app(self.selected_file, 'i_view32.exe')
            elif file_extension in ['.doc', '.docx']:
                # 调用文字处理软件（如Microsoft Word）
                self.open_with_external_app(self.selected_file, 'winword.exe')
            else:
                print("不支持的文件格式")
        else:
            print("请先选择文件")

    def open_with_external_app(self, file_path, app_name):
        try:
            subprocess.Popen([app_name, file_path])
        except Exception as e:
            print(f"打开文件时出错: {e}")

def view_file(file_path):
    file_extension = os.path.splitext(file_path)[1].lower()

    word_path = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\WINWORD.EXE"
    image_path = r"D:\TOOLS\Krita (x64)\bin\krita.exe"

    if file_extension in ['.jpg', '.jpeg', '.png', '.bmp']:
        try:
            subprocess.Popen([image_path, file_path])
        except Exception as e:
            print(f"打开文件时出错: {e}")
    elif file_extension in ['.doc', '.docx']:
        try:
            subprocess.Popen([word_path, file_path])
        except Exception as e:
            print(f"打开文件时出错: {e}")
    else:
        print("不支持的文件格式")

"""
if __name__ == "__main__":
    root = Tk()
    file_manager = FileManager(root)
    root.mainloop()
"""