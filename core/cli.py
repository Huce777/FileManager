import os
import sys
import argparse
from file_consistency_checker import check_file_consistency, scan_directory
from file_attributes_manager import FileAttributesManager
from file_compression_tool import compress_files, extract_zip
from file_encryption_decryption import FileEncryptor
from customized_packaging_unpacking import pack_files, unpack_file
from file_packing import zip_folder
from file_renaming_deletion import rename_file, delete_file
from file_hijacking import FileManager, view_file
from poortext import BadTextManager, TextFilter, PredicateCalculus
from telephone_analysis import PhoneBook, HarassmentPhoneBook, CallAnalyzer, HarassmentCallInterceptor, analyze_incoming_call
from tkinter import Tk


def main():
    # 创建一个ArgumentParser对象，用于解析命令行参数
    parser = argparse.ArgumentParser(description='文件管理系统', formatter_class=argparse.RawTextHelpFormatter)
    # 添加一个命令行参数，用于指定要执行的命令
    parser.add_argument('command', nargs='?', help='''命令:
    check-consistency <file_or_dir>    检查文件后缀与内容一致性
    show-attributes <file>            显示文件属性
    modify-attribute <file> <attribute> <enable>  修改文件属性
    compress <output_zip> <files_or_dirs>  压缩文件或文件夹
    extract <zip_file> <output_dir>   解压缩文件
    encrypt <input_file> <output_file> <key>  加密文件
    decrypt <input_file> <output_file> <key>  解密文件
    pack-custom <output_file> <files>  自定义格式打包
    unpack-custom <input_file> <output_dir>  自定义格式解包
    zip-folder <folder> <output_zip>   打包文件夹
    rename <old_path> <new_name>      重命名文件
    delete <file_path>                删除文件
    view-file <file_path>             查看文件
    filter-text <text>                过滤文本
    analyze-call <number>             分析来电''')

    # 解析命令行参数
    args, unknown_args = parser.parse_known_args()

    # 如果没有指定命令，则打印帮助信息
    if not args.command:
        print("请输入命令，可用命令如下：")
        parser.print_help()
        return

    # 根据命令执行相应的操作
    if args.command == 'check-consistency':
        # 检查文件后缀与内容一致性
        if len(unknown_args) < 1:
            print("请指定要检查的文件或目录")
            return
        path = unknown_args[0]
        if os.path.isfile(path):
            _, actual_type = check_file_consistency(path)
            print(f"文件: {path}, 实际类型: {actual_type}")
        elif os.path.isdir(path):
            inconsistent_files = scan_directory(path)
            if inconsistent_files:
                print("发现以下文件后缀与内容不一致:")
                for file_path, actual_type in inconsistent_files:
                    print(f"文件: {file_path}, 实际类型: {actual_type}")
            else:
                print("所有文件后缀与内容一致")
        else:
            print(f"路径 {path} 不存在")

    elif args.command == 'show-attributes':
        # 显示文件属性
        if len(unknown_args) < 1:
            print("请指定要查看属性的文件")
            return
        file_path = unknown_args[0]
        manager = FileAttributesManager(file_path)
        attributes = manager.display_attributes()
        print(f"文件: {file_path}, 属性: {attributes}")

    elif args.command == 'modify-attribute':
        # 修改文件属性
        if len(unknown_args) < 3:
            print("请指定文件、属性和是否启用")
            return
        file_path = unknown_args[0]
        attribute = unknown_args[1]
        enable = unknown_args[2].lower() == 'true'
        manager = FileAttributesManager(file_path)
        success = manager.modify_attribute(attribute, enable)
        if success:
            print(f"文件 {file_path} 的 {attribute} 属性已修改")
        else:
            print(f"修改文件 {file_path} 的 {attribute} 属性失败")

    elif args.command == 'compress':
        # 压缩文件或文件夹
        if len(unknown_args) < 2:
            print("请指定输出ZIP文件和要压缩的文件或文件夹")
            return
        output_zip = unknown_args[0]
        files_or_dirs = unknown_args[1:]
        compress_files(output_zip, *files_or_dirs)

    elif args.command == 'extract':
        # 解压缩文件
        if len(unknown_args) < 2:
            print("请指定ZIP文件和解压缩的目标目录")
            return
        zip_file = unknown_args[0]
        output_dir = unknown_args[1]
        extract_zip(zip_file, output_dir)

    elif args.command == 'encrypt':
        # 加密文件
        if len(unknown_args) < 3:
            print("请指定输入文件、输出文件和加密秘钥")
            return
        input_file = unknown_args[0]
        output_file = unknown_args[1]
        key = unknown_args[2].encode('utf-8')
        encryptor = FileEncryptor()
        encryptor.encrypt_file(input_file, output_file, key)

    elif args.command == 'decrypt':
        # 解密文件
        if len(unknown_args) < 3:
            print("请指定输入文件、输出文件和解密秘钥")
            return
        input_file = unknown_args[0]
        output_file = unknown_args[1]
        key = unknown_args[2].encode('utf-8')
        encryptor = FileEncryptor()
        encryptor.decrypt_file(input_file, output_file, key)

    elif args.command == 'pack-custom':
        # 自定义格式打包
        if len(unknown_args) < 2:
            print("请指定输出文件和要打包的文件")
            return
        output_file = unknown_args[0]
        files = unknown_args[1:]
        pack_files(files, output_file)

    elif args.command == 'unpack-custom':
        # 自定义格式解包
        if len(unknown_args) < 2:
            print("请指定输入文件和解包的目标目录")
            return
        input_file = unknown_args[0]
        output_dir = unknown_args[1]
        unpack_file(input_file, output_dir)

    elif args.command == 'zip-folder':
        # 打包文件夹
        if len(unknown_args) < 2:
            print("请指定要打包的文件夹和输出ZIP文件")
            return
        folder = unknown_args[0]
        output_zip = unknown_args[1]
        zip_folder(folder, output_zip)

    elif args.command == 'rename':
        # 重命名文件
        if len(unknown_args) < 2:
            print("请指定原文件路径和新文件名")
            return
        old_path = unknown_args[0]
        new_name = unknown_args[1]
        rename_file(old_path, new_name)

    elif args.command == 'delete':
        # 删除文件
        if len(unknown_args) < 1:
            print("请指定要删除的文件路径")
            return
        file_path = unknown_args[0]
        delete_file(file_path)

    elif args.command == 'view-file':
        # 查看文件
        if len(unknown_args) < 1:
            print("请指定要查看的文件路径")
            return
        file_path = unknown_args[0]
        root = Tk()
        file_manager = FileManager(root)
        file_manager.selected_file = file_path
        file_manager.show_file()
        root.mainloop()
        view_file(file_path)

    elif args.command == 'filter-text':
        # 过滤文本
        if len(unknown_args) < 1:
            print("请指定要过滤的文本")
            return
        text = ' '.join(unknown_args)
        bad_text_manager = BadTextManager()
        text_filter = TextFilter(bad_text_manager)
        predicate_calculus = PredicateCalculus()
        predicate_calculus.add_rule({
            "condition": "result['match_prob'] > 0.5 and len(result['matched_bad_texts']) >= 2",
            "action": "deny"
        })
        predicate_calculus.add_rule({
            "condition": "result['match_prob'] < 0.2",
            "action": "allow"
        })
        filter_result = text_filter.filter_text(text)
        final_decision = predicate_calculus.evaluate(filter_result)
        print("原始过滤结果:", filter_result)
        print("最终放行结果:", final_decision)

    elif args.command == 'analyze-call':
        # 分析来电
        if len(unknown_args) < 1:
            print("请指定来电号码")
            return
        number = unknown_args[0]
        phone_book = PhoneBook()
        harassment_phone_book = HarassmentPhoneBook()
        call_analyzer = CallAnalyzer(phone_book, harassment_phone_book)
        call_interceptor = HarassmentCallInterceptor(call_analyzer)
        call_interceptor.intercept_call(number)
        is_harassment, analysis_result = analyze_incoming_call(number)
        print(f"分析结果：{analysis_result}")
        if is_harassment:
            print("建议：可能是骚扰电话，谨慎接听")
        else:
            print("建议：正常来电，可以接听")

    else:
        # 未知命令
        print(f"未知命令: {args.command}")
        parser.print_help()

if __name__ == "__main__":
    main()