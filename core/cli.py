import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
import argparse
import sys

from zope.interface.ro import is_consistent

#获取项目根目录
#project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#sys.path.append(project_root)

#进行绝对导入
#from D.Project.FileManager.core.file_consistency_checker import check_file_cons istency, scan_directory
#from .file_consistency_checker import check_file_consistency, scan_directory
#from zope.interface.ro import is_consistent

# 导入功能模块
from file_consistency_checker import check_file_consistency, scan_directory
from file_attributes_manager import FileAttributesManager
from file_compression_tool import compress_files, extract_zip
from file_encryption_decryption import FileEncryptor
from file_packing import zip_folder
from file_renaming_deletion import rename_file, delete_file
from file_hijacking import view_file
from customized_packaging_unpacking import pack_files, unpack_file
from poortext import BadTextManager, TextFilter, PredicateCalculus
from telephone_analysis import analyze_incoming_call

class FileManagerGUI:
    def __init__(self, root):
        self.root = root  
        self.root.title("文件管理软件")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")

        # 创建标签页
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建各个功能页面
        self.create_file_management_page()
        self.create_encryption_page()
        self.create_text_processing_page()
        self.create_call_analysis_page()

    def create_file_management_page(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="文件管理")

        # 文件一致性检查
        ttk.Label(frame, text="文件一致性检查").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Button(frame, text="选择文件", command=self.check_file_consistency).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="扫描目录", command=self.scan_directory).grid(row=0, column=2, padx=5, pady=5)

        # 文件属性管理
        ttk.Label(frame, text="文件属性管理").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Button(frame, text="显示属性", command=self.display_file_attributes).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(frame, text="设置隐藏属性", command=lambda: self.modify_file_attribute("hidden", True)).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(frame, text="取消隐藏属性", command=lambda: self.modify_file_attribute("hidden", False)).grid(row=1, column=3, padx=5, pady=5)
        ttk.Button(frame, text="设置只读属性", command=lambda: self.modify_file_attribute("readonly", True)).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(frame, text="取消只读属性", command=lambda: self.modify_file_attribute("readonly", False)).grid(row=2, column=2, padx=5, pady=5)

        # 文件压缩与解压缩
        ttk.Label(frame, text="文件压缩与解压缩").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Button(frame, text="压缩文件", command=self.compress_files).grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(frame, text="解压缩文件", command=self.extract_zip).grid(row=3, column=2, padx=5, pady=5)

        # 文件夹打包
        ttk.Label(frame, text="文件夹打包").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Button(frame, text="打包文件夹", command=self.pack_folder).grid(row=4, column=1, padx=5, pady=5)

        # 文件重命名与删除
        ttk.Label(frame, text="文件重命名与删除").grid(row=5, column=0, sticky=tk.W, pady=5)
        ttk.Button(frame, text="重命名文件", command=self.rename_file).grid(row=5, column=1, padx=5, pady=5)
        ttk.Button(frame, text="删除文件", command=self.delete_file).grid(row=5, column=2, padx=5, pady=5)

        # 文件外挂显示
        ttk.Label(frame, text="文件外挂显示").grid(row=6, column=0, sticky=tk.W, pady=5)
        ttk.Button(frame, text="显示文件", command=self.view_file).grid(row=6, column=1, padx=5, pady=5)

    def create_encryption_page(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="加密解密")

        # 文件加密
        ttk.Label(frame, text="文件加密").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Button(frame, text="选择文件", command=self.encrypt_file).grid(row=0, column=1, padx=5, pady=5)

        # 文件解密
        ttk.Label(frame, text="文件解密").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Button(frame, text="选择文件", command=self.decrypt_file).grid(row=1, column=1, padx=5, pady=5)

        # 自定义打包与解包
        ttk.Label(frame, text="自定义打包").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Button(frame, text="打包文件", command=self.custom_pack_files).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(frame, text="解包文件", command=self.custom_unpack_files).grid(row=2, column=2, padx=5, pady=5)

    def create_text_processing_page(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="文本处理")
        # 不良文本过滤
        ttk.Label(frame, text="不良文本过滤").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Button(frame, text="选择文本文件", command=self.filter_text).grid(row=0, column=1, padx=5, pady=5)

    def create_call_analysis_page(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="骚扰电话分析")

        # 骚扰电话分析
        ttk.Label(frame, text="骚扰电话分析").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Button(frame, text="分析来电", command=self.analyze_incoming_call).grid(row=0, column=1, padx=5, pady=5)

    # 文件一致性检查
    def check_file_consistency(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                is_consistent, result_msg = check_file_consistency(file_path)
                if is_consistent:
                    messagebox.showinfo("成功",result_msg)
                else:
                    messagebox.showwarning("警告",result_msg)
            except Exception as e:
                messagebox.showerror("错误", f"检查失败: {e}")

    def scan_directory(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            try:
                inconsistent_files = scan_directory(dir_path)
                print(f"不一致文件数量:{len(inconsistent_files)}")
                print(f"不一致文件列表:{inconsistent_files}")
                if inconsistent_files:
                    result_text = "发现以下文件后缀与内容不一致：\n"
                    for file_path, actual_type in inconsistent_files:
                        result_text += f"文件:{file_path}\n实际类型：:{actual_type}\n{'-'*50}\n"
                    messagebox.showinfo("结果",result_text)
                else:
                    messagebox.showinfo("成功","所有文件后缀与内容一致，没有发现问题")
            except Exception as e:
                messagebox.showerror("错误",f"扫描失败:{e}")

    # 文件属性管理
    def display_file_attributes(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            manager = FileAttributesManager(file_path)
            attributes = manager.display_attributes()
            messagebox.showinfo("文件属性", attributes)

    def modify_file_attribute(self, attribute, enable):
        file_path = filedialog.askopenfilename()
        if file_path:
            if not os.path.exists(file_path):
                messagebox.showerror("错误", f"文件 {file_path} 不存在")
                return
            manager = FileAttributesManager(file_path)
            success = manager.modify_attribute(attribute, enable)
            if success:
                messagebox.showinfo("成功", f"{attribute} 属性已{'启用' if enable else '禁用'}")
            else:
                messagebox.showerror("错误", f"修改 {attribute} 属性失败")

    # 文件压缩与解压缩
    def compress_files(self):
        files = filedialog.askopenfilenames()
        if files:
            output_path = filedialog.asksaveasfilename(defaultextension=".zip")
            if output_path:
                try:
                    compress_files(output_path, *files)
                    messagebox.showinfo("成功", "文件压缩完成")
                except Exception as e:
                    messagebox.showerror("错误", f"压缩失败: {e}")

    def extract_zip(self):
        zip_path = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
        if zip_path:
            extract_to = filedialog.askdirectory()
            if extract_to:
                try:
                    extract_zip(zip_path, extract_to)
                    messagebox.showinfo("成功", "文件解压缩完成")
                except Exception as e:
                    messagebox.showerror("错误", f"解压缩失败: {e}")

    # 文件夹打包
    def pack_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            output_path = filedialog.asksaveasfilename(defaultextension=".zip")
            if output_path:
                try:
                    zip_folder(folder_path, output_path)
                    messagebox.showinfo("成功", "文件夹打包完成")
                except Exception as e:
                    messagebox.showerror("错误", f"打包失败: {e}")

    # 文件重命名与删除
    def rename_file(self):
        old_path = filedialog.askopenfilename()
        if old_path:
            new_name = simpledialog.askstring("输入", "请输入新文件名:")
            if new_name:
                try:
                    rename_file(old_path, new_name)
                    messagebox.showinfo("成功", "文件重命名完成")
                except Exception as e:
                    messagebox.showerror("错误", f"重命名失败: {e}")

    def delete_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            if messagebox.askyesno("确认", "确定要删除此文件吗?"):
                try:
                    delete_file(file_path)
                    messagebox.showinfo("成功", "文件删除成功")
                except Exception as e:
                    messagebox.showerror("错误", f"删除失败: {e}")

    # 文件外挂显示
    def view_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            try:
                view_file(file_path)
                messagebox.showinfo("成功", "文件已打开")
            except Exception as e:
                messagebox.showerror("错误", f"打开文件失败: {e}")

    # 文件加密与解密
    def encrypt_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            output_path = filedialog.asksaveasfilename()
            if output_path:
                key = simpledialog.askstring("输入", "请输入加密秘钥 (16、24 或 32 字节):")
                if key:
                    try:
                        encryptor = FileEncryptor()
                        encryptor.encrypt_file(file_path, output_path, key.encode('utf-8'))
                        messagebox.showinfo("成功", "文件加密完成")
                    except Exception as e:
                        messagebox.showerror("错误", f"加密失败: {e}")

    def decrypt_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            output_path = filedialog.asksaveasfilename()
            if output_path:
                key = simpledialog.askstring("输入", "请输入解密秘钥 (必须与加密时相同):")
                if key:
                    try:
                        encryptor = FileEncryptor()
                        encryptor.decrypt_file(file_path, output_path, key.encode('utf-8'))
                        messagebox.showinfo("成功", "文件解密完成")
                    except Exception as e:
                        messagebox.showerror("错误", f"解密失败: {e}")

    # 自定义打包与解包
    def custom_pack_files(self):
        files = filedialog.askopenfilenames()
        if files:
            output_path = filedialog.asksaveasfilename(defaultextension=".mycfg")
            if output_path:
                try:
                    from core.customized_packaging_unpacking import pack_files
                    key = simpledialog.askstring("输入", "请输入加密秘钥 :")
                    if key:
                        pack_files(list(files), output_path,key.encode('utf-8'))
                        messagebox.showinfo("成功", "文件打包完成")
                except Exception as e:
                    messagebox.showerror("错误", f"打包失败: {e}")

    def custom_unpack_files(self):
        file_path = filedialog.askopenfilename(filetypes=[("Custom files", "*.mycfg")])
        if file_path:
            output_dir = filedialog.askdirectory()
            if output_dir:
                try:
                    from core.customized_packaging_unpacking import unpack_file
                    key = simpledialog.askstring("输入", "请输入解密秘钥 :")
                    if key:
                        unpack_file(file_path, output_dir, key.encode('utf-8'))
                        messagebox.showinfo("成功", "文件解包完成")
                except Exception as e:
                    messagebox.showerror("错误", f"解包失败: {e}")

    # 不良文本过滤
    def filter_text(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            threshold = simpledialog.askfloat("输入", "请输入匹配概率阈值 (0.0-1.0):", minvalue=0.0, maxvalue=1.0)
            if threshold is not None:
                try:
                    bad_text_manager = BadTextManager()
                    text_filter = TextFilter(bad_text_manager)
                    predicate_calculus = PredicateCalculus()
                    predicate_calculus.add_rule({
                        "condition": "result['match_prob'] > 0.5 and len(result['matched_bad_texts']) >= 2",
                        "action": "deny"
                    })
                    predicate_calculus.add_rule({
                        "condition": f"result['match_prob'] < {threshold}",
                        "action": "allow"
                    })
                    # 尝试不同的编码
                    encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'ascii']
                    text = None
                    for encoding in encodings:
                        try:
                            with open(file_path,"r",encoding=encoding) as f:
                                text = f.read()
                            break
                        except UnicodeDecodeError:
                            continue

                    if text is None:
                        raise UnicodeDecodeError("无法使用支持的编码解码文件")

                    filter_result = text_filter.filter_text(text, threshold)
                    final_decision = predicate_calculus.evaluate(filter_result)

                    result_text = f"过滤结果:\n匹配概率:{filter_result['match_prob']}\n"
                    if filter_result['matched_bad_texts']:
                        result_text += "匹配的不良文本:\n"
                        for item in filter_result['matched_bad_texts']:
                            result_text += f"- {item['bad_text']} (出现{item['count']}次)\n"
                    result_text += f"最终放行结果：{'放行' if final_decision else '拦截'}"
                    messagebox.showinfo("不良文本过滤结果", result_text)

                except Exception as e:
                    messagebox.showerror("错误", f"过滤失败: {e}")

    # 骚扰电话分析
    def analyze_incoming_call(self):
        number = simpledialog.askstring("输入", "请输入来电号码:")
        if number:
            try:
                is_harassment, analysis_result = analyze_incoming_call(number)
                result_text = f"分析结果: {analysis_result}"
                if is_harassment:
                    result_text += "\n\n警告：可能是骚扰电话！"
                    if messagebox.askyesno("警告", f"{result_text}\n\n是否接听此电话?"):
                        messagebox.showinfo("提示", "正在接听电话...")
                    else:
                        messagebox.showinfo("提示", "已自动挂断骚扰电话。")
                else:
                    messagebox.showinfo("提示", result_text)
            except Exception as e:
                messagebox.showerror("错误", f"分析失败: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileManagerGUI(root)
    root.mainloop()