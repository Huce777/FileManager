import os  # os库用于处理文件和目录路径
import argparse  # argparse库用于解析命令行参数

# 2.软件支持文件后缀与文件内容的一致性识别。（主要通过文件头识别文件类型）

# 定义常见文件类型的文件头字典
FILE_SIGNATURES = {
    # 文本文件
    'TXT': (b'\x00\x00\x00\x00\x00\x00\x00\x00',),  # 简单文本可能没有固定文件头
    'DOC': (b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1',),
    'DOCX': (b'PK\x03\x04',),
    'PDF': (b'%PDF-',),
    'RTF': (b'{\\rtf',),
    'ODT': (b'PK\x03\x04',),
    'MD': (b'# ',),  # Markdown文件通常以#开头

    # 图片文件
    'JPEG': (b'\xff\xd8\xff',),
    'PNG': (b'\x89PNG\r\n\x1a\n',),
    'GIF': (b'GIF87a', b'GIF89a'),
    'BMP': (b'BM',),
    'SVG': (b'<?xml',),  # SVG是XML格式
    'TIFF': (b'II*\x00', b'MM\x00*'),

    # 音频文件
    'MP3': (b'ID3',),
    'WAV': (b'RIFF',),
    'AAC': (b'\xff\xf1',),
    'FLAC': (b'fLaC',),
    'OGG': (b'OggS',),

    # 视频文件
    'MP4': (b'\x00\x00\x00\x18ftyp',),
    'AVI': (b'RIFF',),
    'MKV': (b'\x1A\x45\xDF\xA3',),
    'MOV': (b'\x00\x00\x00\x00moov',),
    'WMV': (b'\x30\x26\xB2\x75\x8E\x66\xCF\x11\xA6\xD9\x00\xAA\x00\x62\xCE\x6C',),

    # 压缩文件
    'ZIP': (b'PK\x03\x04',),
    'RAR': (b'RAR\x1a\x07\x00',),
    '7Z': (b'7z\xBC\xAF\x27\x1C',),
    'TAR': (b'ustar',),
    'GZ': (b'\x1F\x8B\x08',),

    # 可执行文件
    'EXE': (b'MZ',),
    'BAT': (b'@echo',),  # 批处理文件通常以@echo开头
    'SH': (b'#!/bin/bash',),  # Shell脚本通常以#!/bin/bash开头
    'MSI': (b'MSI',),

    # 表格文件
    'XLS': (b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1',),
    'XLSX': (b'PK\x03\x04',),
    'ODS': (b'PK\x03\x04',),

    # 演示文稿文件
    'PPT': (b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1',),
    'PPTX': (b'PK\x03\x04',),
    'ODP': (b'PK\x03\x04',),

    # 数据库文件
    'SQL': (b'SQL',),
    'DB': (b'SQLite',),

    # 网页文件
    'HTML': (b'<!DOCTYPE HTML',),
    'HTM': (b'<!DOCTYPE HTML',),
    'CSS': (b'/* CSS',),
    'JS': (b'// JavaScript',),

    # 代码文件
    'C': (b'#include',),
    'CPP': (b'#include',),
    'JAVA': (b'public class',),
    'PY': (b'python',),
    'PHP': (b'<?php',),

    # 配置文件
    'INI': (b'[',),  # INI文件通常以[开头
    'JSON': (b'{', b'['),  # JSON文件通常以{或[开头
    'XML': (b'<?xml',),
    'YAML': (b'---',),
}


def get_file_type(file_path):
    # 通过文件头获取文件的实际类型
    try:
        with open(file_path, 'rb') as f:
            # 读取文件头的前几个字节
            file_header = f.read(32)  # 读取前32字节

            # 遍历文件签名字典，查找匹配的文件类型
            for file_type, signatures in FILE_SIGNATURES.items():
                for signature in signatures:
                    # 检查文件头是否包含该签名
                    if file_header.startswith(signature):
                        #print(f"文件类型：{file_type}")  # 输出文件类型
                        return file_type

            # 如果没有匹配到任何签名，返回未知类型
            #print("文件类型:UNKNOWN")
            return 'UNKNOWN'
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return 'ERROR'


def check_file_consistency(file_path):
    # 检查文件后缀与内容是否一致
    # 获取文件的实际类型
    actual_type = get_file_type(file_path)

    # 获取文件的后缀名
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension[1:].upper()  # 转为大写并去除点

    # 判断是否一致
    if actual_type == file_extension:
        result_msg = f"文件{file_path}的后缀与内容一致,\n该文件是{actual_type}文件"
        return True, result_msg
    else:
        result_msg = f"文件{file_path}的后缀与内容不一致，\n实际类型为{actual_type}"
        return False, result_msg


def scan_directory(directory_path):
    # 扫描目录下的所有文件，检查后缀与内容一致性

    inconsistent_files = []

    # 遍历目录下的所有文件
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                is_consistent, actual_type = check_file_consistency(file_path)
                if not is_consistent:
                    inconsistent_files.append((file_path, actual_type))
                    #print(f"文件{file_path}的后缀与内容不一致。实际类型{actual_type}")
            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {e}")

    return inconsistent_files


"""
"""


def main():
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description='文件后缀与内容一致性检查工具')
    parser.add_argument('directory', help='要扫描的目录路径')
    args = parser.parse_args()

    # 检查目录是否存在
    if not os.path.isdir(args.directory):
        print(f"错误: 目录 {args.directory} 不存在")
        return

    # 扫描目录
    print(f"正在扫描目录: {args.directory}")
    inconsistent_files = scan_directory(args.directory)

    # 输出结果
    if inconsistent_files:
        print("\n发现以下文件后缀与内容不一致:")
        for file_path, actual_type in inconsistent_files:
            print(f"文件: {file_path}")
            print(f"实际类型: {actual_type}")
            print("-" * 50)
    else:
        print("\n所有文件后缀与内容一致，没有发现问题")
