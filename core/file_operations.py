#文件基础操作
"""
文件操作核心模块
版本: 2.1
功能：文件属性管理、元数据操作、安全删除、类型验证等
"""

import os
import sys
import shutil
import logging
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from enum import IntFlag
import hashlib

# 跨平台属性支持
if platform.system() == 'Windows':
    import win32api
    import win32con
else:
    from stat import (
        S_IWRITE, S_IREAD,
        ST_MODE, ST_CTIME, ST_ATIME, ST_MTIME
    )

# 日志配置
logger = logging.getLogger(__name__)


class FileAttribute(IntFlag):
    """文件属性标志位 (Windows专用)"""
    NORMAL = 0
    READONLY = 1
    HIDDEN = 2
    SYSTEM = 4
    ARCHIVE = 32


class FileOperatorError(Exception):
    """文件操作异常基类"""
    pass


class FileOperator:
    """文件操作核心类"""

    CHUNK_SIZE = 16 * 1024  # 16KB 块大小
    HASH_BLOCK_SIZE = 65536  # 64KB 哈希计算块

    def __init__(self, enable_logging: bool = True):
        self.os_type = platform.system()
        self.enable_logging = enable_logging

    def _log(self, message: str, level: str = 'info'):
        """日志记录"""
        if self.enable_logging:
            log_func = getattr(logger, level, logger.info)
            log_func(message)

    def set_attributes(self, path: Path,
                       hidden: Optional[bool] = None,
                       readonly: Optional[bool] = None,
                       system: Optional[bool] = None) -> None:
        """
        设置文件属性（跨平台）
        :param path: 文件路径
        :param hidden: 是否隐藏
        :param readonly: 是否只读
        :param system: 是否系统文件（仅Windows）
        """
        path = Path(path)
        if not path.exists():
            raise FileOperatorError(f"文件不存在: {path}")

        try:
            # Windows系统属性设置
            if self.os_type == 'Windows':
                attrs = win32api.GetFileAttributes(str(path))

                # 处理隐藏属性
                if hidden is not None:
                    if hidden:
                        attrs |= win32con.FILE_ATTRIBUTE_HIDDEN
                    else:
                        attrs &= ~win32con.FILE_ATTRIBUTE_HIDDEN

                # 处理只读属性
                if readonly is not None:
                    if readonly:
                        attrs |= win32con.FILE_ATTRIBUTE_READONLY
                    else:
                        attrs &= ~win32con.FILE_ATTRIBUTE_READONLY

                # 处理系统文件属性
                if system is not None and system:
                    attrs |= win32con.FILE_ATTRIBUTE_SYSTEM

                win32api.SetFileAttributes(str(path), attrs)

            # Linux/Mac系统属性设置
            else:
                # 处理隐藏属性（通过文件名）
                if hidden is not None:
                    new_name = path.name
                    if hidden and not new_name.startswith('.'):
                        new_path = path.parent / f".{new_name}"
                        path.rename(new_path)
                        path = new_path
                    elif not hidden and new_name.startswith('.'):
                        new_path = path.parent / new_name[1:]
                        path.rename(new_path)
                        path = new_path

                # 处理只读属性
                if readonly is not None:
                    mode = path.stat().st_mode
                    if readonly:
                        mode &= ~S_IWRITE
                    else:
                        mode |= S_IWRITE
                    path.chmod(mode)

            self._log(f"属性设置成功: {path}")
        except Exception as e:
            raise FileOperatorError(f"属性设置失败: {str(e)}") from e

    def safe_rename(self, src: Path, dst: Path, overwrite: bool = False) -> Path:
        """
        安全重命名文件
        :param src: 源文件路径
        :param dst: 目标文件路径
        :param overwrite: 是否覆盖已存在文件
        :return: 新路径
        """
        src = Path(src)
        dst = Path(dst)

        if not src.exists():
            raise FileOperatorError(f"源文件不存在: {src}")
        if dst.exists() and not overwrite:
            raise FileOperatorError(f"目标文件已存在: {dst}")

        try:
            # Windows需要特殊处理覆盖
            if self.os_type == 'Windows' and dst.exists():
                self.set_attributes(dst, readonly=False)

            src.rename(dst)
            self._log(f"重命名成功: {src} -> {dst}")
            return dst
        except Exception as e:
            raise FileOperatorError(f"重命名失败: {str(e)}") from e

    def secure_delete(self, path: Path, passes: int = 3) -> None:
        """
        安全删除文件（多次覆写）
        :param path: 文件路径
        :param passes: 覆写次数
        """
        path = Path(path)
        if not path.exists():
            return

        try:
            # 获取文件大小
            file_size = path.stat().st_size

            # 多次覆写
            for _ in range(passes):
                with path.open('rb+') as f:
                    f.seek(0)
                    f.write(os.urandom(file_size))

            # 重命名后删除
            temp_name = path.with_name(f"._{path.name}")
            path.rename(temp_name)
            temp_name.unlink()

            self._log(f"安全删除完成: {path}")
        except Exception as e:
            raise FileOperatorError(f"安全删除失败: {str(e)}") from e

    def get_metadata(self, path: Path) -> Dict:
        """
        获取完整文件元数据
        :param path: 文件路径
        :return: 元数据字典
        """
        path = Path(path)
        if not path.exists():
            raise FileOperatorError(f"路径不存在: {path}")

        stat = path.stat()
        metadata = {
            'path': str(path.resolve()),
            'size': path.stat().st_size,
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'accessed': datetime.fromtimestamp(stat.st_atime),
            'is_dir': path.is_dir(),
            'is_file': path.is_file(),
            'is_symlink': path.is_symlink(),
            'hash_md5': self.calculate_hash(path, 'md5'),
            'hash_sha256': self.calculate_hash(path, 'sha256')
        }

        # Windows特有属性
        if self.os_type == 'Windows':
            attrs = win32api.GetFileAttributes(str(path))
            metadata.update({
                'readonly': bool(attrs & win32con.FILE_ATTRIBUTE_READONLY),
                'hidden': bool(attrs & win32con.FILE_ATTRIBUTE_HIDDEN),
                'system': bool(attrs & win32con.FILE_ATTRIBUTE_SYSTEM)
            })
        else:
            metadata.update({
                'readonly': not os.access(path, os.W_OK),
                'hidden': path.name.startswith('.'),
                'mode': oct(stat.st_mode)
            })

        return metadata

    def calculate_hash(self, path: Path, algorithm: str = 'sha256') -> str:
        """
        计算文件哈希值
        :param path: 文件路径
        :param algorithm: 哈希算法（md5/sha1/sha256）
        :return: 哈希值十六进制字符串
        """
        hash_func = hashlib.new(algorithm)
        with path.open('rb') as f:
            for chunk in iter(lambda: f.read(self.HASH_BLOCK_SIZE), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()

    def verify_file_type(self, path: Path) -> Tuple[bool, str]:
        """
        验证文件真实类型（通过文件头）
        :param path: 文件路径
        :return: (是否匹配声明类型, 检测到的MIME类型)
        """
        try:
            import magic
            mime = magic.Magic(mime=True)
            detected_type = mime.from_file(str(path))
        except ImportError:
            # 回退到简单实现
            detected_type = self._simple_file_type_detection(path)

        ext = path.suffix.lower()[1:]  # 去掉点
        common_types = {
            'jpg': 'image/jpeg',
            'png': 'image/png',
            'pdf': 'application/pdf',
            # 添加更多类型...
        }
        return (common_types.get(ext, '') == detected_type, detected_type)

    def _simple_file_type_detection(self, path: Path) -> str:
        """简单文件类型检测"""
        signatures = {
            b'\xFF\xD8\xFF': 'image/jpeg',
            b'\x89PNG\r\n\x1a\n': 'image/png',
            b'%PDF-': 'application/pdf',
        }
        with path.open('rb') as f:
            header = f.read(32)
            for sig, mime in signatures.items():
                if header.startswith(sig):
                    return mime
        return 'application/octet-stream'

    def open_with_default_app(self, path: Path) -> None:
        """
        用默认应用程序打开文件
        :param path: 文件路径
        """
        try:
            if self.os_type == 'Windows':
                os.startfile(str(path))
            elif self.os_type == 'Darwin':
                subprocess.run(['open', str(path)], check=True)
            else:  # Linux
                subprocess.run(['xdg-open', str(path)], check=True)
            self._log(f"已打开文件: {path}")
        except Exception as e:
            raise FileOperatorError(f"打开文件失败: {str(e)}") from e

    def bulk_operation(self,
                       operation: str,
                       paths: List[Path],
                       **kwargs) -> Dict[Path, bool]:
        """
        批量文件操作
        :param operation: 操作类型（delete/rename/copy）
        :param paths: 文件路径列表
        :return: 操作结果字典
        """
        results = {}
        for path in paths:
            try:
                if operation == 'delete':
                    self.secure_delete(path, **kwargs)
                    results[path] = True
                elif operation == 'rename':
                    new_path = self.safe_rename(path, **kwargs)
                    results[path] = new_path
                # 可扩展其他操作...
                else:
                    results[path] = False
            except Exception as e:
                results[path] = False
                self._log(f"操作失败 {path}: {str(e)}", 'error')
        return results


class FileWatcher(FileOperator):
    def watch_directory(self, path: Path, handler: callable):
        """监视目录变化"""
        from watchdog.observers import Observer
        # 实现文件系统事件监控



# 示例用法
if __name__ == "__main__":
    # 初始化文件操作器
    operator = FileOperator()

    # 示例文件操作
    test_file = Path("test.txt")

    # 设置文件属性
    operator.set_attributes(test_file, hidden=True, readonly=True)

    # 获取元数据
    meta = operator.get_metadata(test_file)
    print("文件元数据:")
    for k, v in meta.items():
        print(f"{k}: {v}")

    # 验证文件类型
    is_valid, mime = operator.verify_file_type(test_file)
    print(f"文件类型验证: {is_valid}, MIME类型: {mime}")

    # 安全删除文件
    operator.secure_delete(test_file)