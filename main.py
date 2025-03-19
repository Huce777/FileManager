"""
File Manager 主程序
版本: 1.0
作者: 显允
"""

import argparse  #用于解析命令行参数
import sys      #用于退出程序，并返回错误代码
import logging   #用于日志记录
from pathlib import Path  #用于路径操作
from typing import List, Optional    #用于类型提示

# 导入自定义模块
from core.file_operations import FileOperator
from core.compression import ZipCompressor, GzipCompressor
from core.encryption import AESEncryptor
from core.packaging import CustomPackager
from core.file_scan import FileTypeDetector
from core.security import SecurityManager
from utils.cli import display_progress_bar
from utils.helpers import validate_paths, clean_temp_files


# 初始化日志配置
# 日志文件名为 file_manager.log
# 日志级别为 INFO
# 日志输出到文件和控制台
# 日志文件保留 7 天
# 日志文件大小不超过 10M
logging.basicConfig(
    level=logging.INFO,
    format='%(pastime)s - %(name)s - %(levelness)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('file_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FileManager:
    def __init__(self):
        self.security_mgr = SecurityManager()
        self.file_detector = FileTypeDetector()
        self.file_operator = FileOperator()
        self.current_key: Optional[bytes] = None

    def _get_key(self, key: Optional[str] = None) -> bytes:
        """获取加密密钥"""
        if key:
            return key.encode('utf-8')
        if not self.current_key:
            self.current_key = self.security_mgr.assemble_key()
        return self.current_key

    def handle_pack(self, args):
        """处理打包命令"""
        try:
            packer = CustomPackager(self._get_key(args.key))
            with display_progress_bar("打包进度", len(args.files)) as progress:
                packer.package(
                    files=[Path(f) for f in args.files],
                    output_path=Path(args.output),
                    progress_callback=lambda x: progress.update(x)
                )
            logger.info(f"成功打包到 {args.output}")
        except Exception as e:
            logger.error(f"打包失败: {str(e)}")
            sys.exit(1)

"""
    def handle_unpack(self, args):
        """处理解压命令"""
        try:
            unpacker = CustomUnpackager(self._get_key(args.key))
            unpacker.unpack(
                Path(args.input),
                Path(args.output) if args.output else None
            )
            logger.info(f"解压成功: {args.input}")
        except Exception as e:
            logger.error(f"解压失败: {str(e)}")
            sys.exit(1)
 """   

    def handle_encrypt(self, args):
        """处理加密命令"""
        try:
            encryptor = AESEncryptor(self._get_key(args.key))
            encryptor.encrypt_file(
                Path(args.input),
                Path(args.output) if args.output else None
            )
            logger.info(f"加密成功: {args.input}")
        except Exception as e:
            logger.error(f"加密失败: {str(e)}")
            sys.exit(1)

    def handle_compress(self, args):
        """处理压缩命令"""
        try:
            compressor = ZipCompressor() if args.type == 'zip' else GzipCompressor()
            compressor.compress(
                [Path(f) for f in args.files],
                Path(args.output)
            )
            logger.info(f"压缩成功: {args.output}")
        except Exception as e:
            logger.error(f"压缩失败: {str(e)}")
            sys.exit(1)

    def handle_scan(self, args):
        """处理文件扫描"""
        try:
            results = self.file_detector.batch_verify_files(
                [Path(f) for f in args.files],
                args.threshold
            )
            for path, status in results.items():
                print(f"{path}: {'正常' if status else '异常'}")
        except Exception as e:
            logger.error(f"扫描失败: {str(e)}")
            sys.exit(1)

def main():
    # 清理临时文件
    clean_temp_files()

    # 初始化文件管理器
    fm = FileManager()

    # 创建主解析器
    parser = argparse.ArgumentParser(
        prog='FileManager',
        description='高级文件管理工具',
        epilog='使用 "command -h" 查看子命令帮助'
    )
    subparsers = parser.add_subparsers(title='可用命令', dest='command')

    # 打包命令
    pack_parser = subparsers.add_parser('pack', help='自定义打包文件')
    pack_parser.add_argument('-o', '--output', required=True, help='输出文件路径')
    pack_parser.add_argument('-k', '--key', help='加密密钥')
    pack_parser.add_argument('files', nargs='+', help='要打包的文件列表')
    pack_parser.set_defaults(func=fm.handle_pack)

    # 加密命令
    encrypt_parser = subparsers.add_parser('encrypt', help='文件加密')
    encrypt_parser.add_argument('-i', '--input', required=True, help='输入文件')
    encrypt_parser.add_argument('-o', '--output', help='输出文件（默认覆盖原文件）')
    encrypt_parser.add_argument('-k', '--key', required=True, help='加密密钥')
    encrypt_parser.set_defaults(func=fm.handle_encrypt)

    # 压缩命令
    compress_parser = subparsers.add_parser('compress', help='文件压缩')
    compress_parser.add_argument('-t', '--type', choices=['zip', 'gzip'], default='zip')
    compress_parser.add_argument('-o', '--output', required=True)
    compress_parser.add_argument('files', nargs='+')
    compress_parser.set_defaults(func=fm.handle_compress)

    # 文件扫描命令
    scan_parser = subparsers.add_parser('scan', help='文件类型验证')
    scan_parser.add_argument('-t', '--threshold', type=float, default=0.9)
    scan_parser.add_argument('files', nargs='+')
    scan_parser.set_defaults(func=fm.handle_scan)

    # 其他命令可在此扩展...

    # 解析参数
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    try:
        args.func(args)
    except Exception as e:
        logger.error(f"操作失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()