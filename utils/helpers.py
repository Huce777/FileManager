#辅助函数
"""
实用工具函数集合
版本: 1.2
"""

import os
import sys
import shutil
import hashlib
import tempfile
import platform
from pathlib import Path
from typing import List, Optional, Tuple, Generator
from datetime import datetime

# 跨平台文件属性支持
if platform.system() == 'Windows':
    import win32api
    import win32con
else:
    from stat import (
        S_IWRITE, S_IREAD,
        ST_MODE, ST_CTIME, ST_ATIME, ST_MTIME
    )


class FileSystemError(Exception):
    """自定义文件系统异常"""

    def __init__(self, message: str, path: Optional[Path] = None):
        self.message = message
        self.path = path
        super().__init__(f"{message} [路径: {path}]" if path else message)


def validate_paths(*paths: Path) -> List[Path]:
    """
    验证路径是否存在并返回Path对象列表
    :param paths: 可变数量路径参数
    :return: 验证通过的Path对象列表
    :raises FileSystemError: 路径不存在时抛出
    """
    valid_paths = []
    for p in paths:
        path = Path(p) if not isinstance(p, Path) else p
        if not path.exists():
            raise FileSystemError("路径不存在", path)
        valid_paths.append(path)
    return valid_paths


def get_file_metadata(path: Path) -> dict:
    """
    获取文件元数据
    :param path: 文件路径
    :return: 包含元数据的字典
    """
    stat = path.stat()
    return {
        'size': path.stat().st_size,
        'created': datetime.fromtimestamp(stat.st_ctime),
        'modified': datetime.fromtimestamp(stat.st_mtime),
        'accessed': datetime.fromtimestamp(stat.st_atime),
        'is_dir': path.is_dir(),
        'is_file': path.is_file(),
        'is_symlink': path.is_symlink()
    }


def clean_temp_files(temp_dir: Optional[Path] = None) -> int:
    """
    清理临时文件
    :param temp_dir: 指定临时目录（默认使用系统临时目录）
    :return: 删除的文件数量
    """
    count = 0
    temp_dir = temp_dir or Path(tempfile.gettempdir())

    for temp_file in temp_dir.glob('fm_temp_*'):
        try:
            if temp_file.is_file():
                temp_file.unlink()
                count += 1
        except Exception as e:
            sys.stderr.write(f"删除临时文件失败 {temp_file}: {str(e)}\n")
    return count


def safe_delete(path: Path, retries: int = 3) -> None:
    """
    安全删除文件/目录（带重试机制）
    :param path: 要删除的路径
    :param retries: 重试次数
    """
    for attempt in range(retries):
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            return
        except Exception as e:
            if attempt == retries - 1:
                raise FileSystemError(f"无法删除 {path}", path) from e
            sleep(0.5 * (attempt + 1))


def calculate_checksum(path: Path, algorithm: str = 'sha256') -> str:
    """
    计算文件校验和
    :param path: 文件路径
    :param algorithm: 哈希算法（支持md5/sha1/sha256）
    :return: 校验和十六进制字符串
    """
    hash_func = getattr(hashlib, algorithm)()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def convert_size(size_bytes: int) -> str:
    """
    将字节数转换为易读格式
    :param size_bytes: 字节数
    :return: 格式化字符串（如 1.23 MB）
    """
    units = ("B", "KB", "MB", "GB", "TB")
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    return f"{size:.2f} {units[unit_index]}"


def get_hidden_attribute(path: Path) -> bool:
    """
    获取文件隐藏属性（跨平台）
    :param path: 文件路径
    :return: 是否隐藏
    """
    if platform.system() == 'Windows':
        attrs = win32api.GetFileAttributes(str(path))
        return bool(attrs & win32con.FILE_ATTRIBUTE_HIDDEN)
    else:
        return path.name.startswith('.')


def set_hidden_attribute(path: Path, hidden: bool) -> None:
    """
    设置文件隐藏属性（跨平台）
    :param path: 文件路径
    :param hidden: 是否隐藏
    """
    if platform.system() == 'Windows':
        attrs = win32api.GetFileAttributes(str(path))
        if hidden:
            attrs |= win32con.FILE_ATTRIBUTE_HIDDEN
        else:
            attrs &= ~win32con.FILE_ATTRIBUTE_HIDDEN
        win32api.SetFileAttributes(str(path), attrs)
    else:
        if hidden and not path.name.startswith('.'):
            new_path = path.parent / f".{path.name}"
            path.rename(new_path)
        elif not hidden and path.name.startswith('.'):
            new_path = path.parent / path.name[1:]
            path.rename(new_path)


def split_file(path: Path, chunk_size: int) -> Generator[Path, None, None]:
    """
    文件分块生成器
    :param path: 原文件路径
    :param chunk_size: 分块大小（字节）
    :yield: 临时分块文件路径
    """
    with path.open('rb') as src_file:
        index = 0
        while True:
            chunk = src_file.read(chunk_size)
            if not chunk:
                break
            temp_file = create_temp_file(prefix=f"chunk_{index}_")
            with temp_file.open('wb') as dest_file:
                dest_file.write(chunk)
            yield temp_file
            index += 1


def create_temp_file(prefix: str = "fm_temp_", suffix: str = "") -> Path:
    """
    创建临时文件
    :param prefix: 文件名前缀
    :param suffix: 文件名后缀
    :return: 临时文件路径
    """
    temp_dir = Path(tempfile.gettempdir())
    temp_file = temp_dir / f"{prefix}{os.urandom(4).hex()}{suffix}"
    temp_file.touch()
    return temp_file


def execute_command(cmd: List[str], timeout: int = 30) -> Tuple[int, str, str]:
    """
    执行系统命令（跨平台）
    :param cmd: 命令参数列表
    :param timeout: 超时时间（秒）
    :return: (返回码, 标准输出, 标准错误)
    """
    import subprocess
    from subprocess import TimeoutExpired

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            text=True
        )
        return (
            result.returncode,
            result.stdout.strip(),
            result.stderr.strip()
        )
    except TimeoutExpired:
        raise FileSystemError(f"命令执行超时: {' '.join(cmd)}")


def is_binary_file(path: Path) -> bool:
    """
    检测文件是否为二进制格式
    :param path: 文件路径
    :return: 是否为二进制文件
    """
    try:
        with path.open('rb') as f:
            chunk = f.read(1024)
            return b'\x00' in chunk  # 简单检测null字节
    except:
        return False


def split_by_lines(path: Path, lines_per_chunk: int):
    """按行数分块文件"""
    with path.open('r') as f:
        chunk = []
        for line in f:
            chunk.append(line)
            if len(chunk) >= lines_per_chunk:
                yield create_temp_file(content=''.join(chunk))
                chunk = []
        if chunk:
            yield create_temp_file(content=''.join(chunk))


def compress_chunks(chunks: List[Path], algorithm: str = 'gzip'):
    """压缩多个文件块"""
    # 实现具体的压缩逻辑


def secure_wipe(path: Path, passes: int = 3):
    """安全擦除文件内容"""
    # 实现多次覆写的安全删除


if __name__ == "__main__":
    # 示例用法
    test_file = Path(__file__)

    print("文件元数据:")
    print(get_file_metadata(test_file))

    print("\n文件校验和 (SHA256):")
    print(calculate_checksum(test_file))

    print("\n文件大小转换:")
    print(convert_size(1500000))

    print("\n执行命令测试:")
    code, out, err = execute_command(['echo', 'Hello World'])
    print(f"返回码: {code}, 输出: {out}")