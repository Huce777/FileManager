#压缩解压
"""
文件压缩解压核心模块
支持格式：ZIP/GZIP/自定义格式
版本: 2.1
"""

import os
import zipfile
import gzip
import tarfile
import shutil
import zlib
from pathlib import Path
from typing import List, Optional, Union, Callable
from io import BytesIO
from datetime import datetime
from compressors import ZipCompressor, CzipCompressor, TarCompressor
from utils.helpers import (
    validate_paths,
    safe_delete,
    create_temp_file,
    convert_size,
    FileSystemError
)


class CompressionError(FileSystemError):
    """压缩相关异常基类"""
    pass


class CompressionFormatError(CompressionError):
    """不支持的压缩格式异常"""
    pass


class BaseCompressor:
    """压缩器抽象基类"""

    SUPPORTED_FORMATS = []
    DEFAULT_COMPRESS_LEVEL = 6

    def __init__(self, compress_level: int = DEFAULT_COMPRESS_LEVEL):
        if compress_level not in range(0, 10):
            raise ValueError("压缩级别必须为0-9之间的整数")
        self.compress_level = compress_level
        self._progress_callback = None

    def set_progress_callback(self, callback: Callable[[float], None]):
        """设置进度回调函数"""
        self._progress_callback = callback

    def _update_progress(self, current: int, total: int):
        """更新进度信息"""
        if self._progress_callback and total > 0:
            progress = min(current / total, 1.0)
            self._progress_callback(progress)

    def compress(
            self,
            sources: List[Path],
            output_path: Path,
            password: Optional[str] = None
    ) -> Path:
        """压缩文件/目录"""
        raise NotImplementedError

    def decompress(
            self,
            source: Path,
            output_dir: Path,
            password: Optional[str] = None
    ) -> List[Path]:
        """解压缩文件"""
        raise NotImplementedError


class ZipCompressor(BaseCompressor):
    """ZIP格式压缩器"""

    SUPPORTED_FORMATS = ['.zip']
    COMPRESSION_METHODS = {
        'store': zipfile.ZIP_STORED,
        'deflate': zipfile.ZIP_DEFLATED,
        'bzip2': zipfile.ZIP_BZIP2,
        'lzma': zipfile.ZIP_LZMA
    }

    def __init__(
            self,
            compress_method: str = 'deflate',
            **kwargs
    ):
        super().__init__(**kwargs)
        self.compression = self.COMPRESSION_METHODS.get(
            compress_method.lower(),
            zipfile.ZIP_DEFLATED
        )

    def _calculate_total_size(self, paths: List[Path]) -> int:
        """计算待压缩文件总大小"""
        total = 0
        for path in paths:
            if path.is_file():
                total += path.stat().st_size
            elif path.is_dir():
                for root, _, files in os.walk(path):
                    for f in files:
                        total += (Path(root) / f).stat().st_size
        return total

    def compress(
            self,
            sources: List[Path],
            output_path: Path,
            password: Optional[str] = None
    ) -> Path:
        # 验证输入路径
        validated = validate_paths(*sources)
        total_size = self._calculate_total_size(validated)
        processed = 0

        try:
            with zipfile.ZipFile(
                    output_path,
                    'w',
                    compression=self.compression,
                    compresslevel=self.compress_level
            ) as zf:
                # 设置加密
                if password:
                    zf.setpassword(password.encode('utf-8'))

                for source in validated:
                    if source.is_file():
                        self._add_file_to_zip(zf, source, processed, total_size)
                    elif source.is_dir():
                        self._add_dir_to_zip(zf, source, processed, total_size)

            return output_path
        except Exception as e:
            safe_delete(output_path)
            raise CompressionError(f"ZIP压缩失败: {str(e)}") from e

    def _add_file_to_zip(self, zf, file_path, processed, total_size):
        """添加单个文件到ZIP"""
        arcname = file_path.name
        with open(file_path, 'rb') as f:
            data = f.read()
            zf.writestr(arcname, data, compress_type=self.compression)

            # 更新进度
            processed += len(data)
            self._update_progress(processed, total_size)

    def _add_dir_to_zip(self, zf, dir_path, processed, total_size):
        """递归添加目录到ZIP"""
        for root, _, files in os.walk(dir_path):
            for file in files:
                full_path = Path(root) / file
                arcname = os.path.relpath(full_path, dir_path.parent)
                self._add_file_to_zip(zf, full_path, arcname, processed, total_size)

    def decompress(self, source: Path, output_dir: Path, password: Optional[str] = None) -> List[Path]:
        validated = validate_paths(source)
        output_dir.mkdir(exist_ok=True, parents=True)
        extracted_files = []

        try:
            with zipfile.ZipFile(source, 'r') as zf:
                if password:
                    zf.setpassword(password.encode('utf-8'))

                total = sum(f.file_size for f in zf.infolist())
                processed = 0

                for member in zf.infolist():
                    target_path = output_dir / member.filename
                    if target_path.exists():
                        raise FileExistsError(f"文件已存在: {target_path}")

                    # 提取文件
                    with zf.open(member, 'r') as src, open(target_path, 'wb') as dest:
                        shutil.copyfileobj(src, dest, length=1024 * 1024)
                        processed += member.file_size
                        self._update_progress(processed, total)

                    extracted_files.append(target_path)

            return extracted_files
        except zipfile.BadZipFile as e:
            raise CompressionError("ZIP文件损坏") from e
        except RuntimeError as e:
            if 'encrypted' in str(e):
                raise CompressionError("密码错误或需要密码") from e
            raise


class GzipCompressor(BaseCompressor):
    """GZIP格式压缩器"""

    SUPPORTED_FORMATS = ['.gz', '.gzip']

    def compress(self, sources: List[Path], output_path: Path, **kwargs) -> Path:
        if len(sources) > 1:
            raise CompressionError("GZIP格式不支持多文件压缩")

        source = validate_paths(sources[0])[0]
        if source.is_dir():
            raise CompressionError("GZIP格式不支持目录压缩")

        try:
            with open(source, 'rb') as f_in:
                with gzip.open(output_path, 'wb', compresslevel=self.compress_level) as f_out:
                    shutil.copyfileobj(f_in, f_out)
                    self._update_progress(source.stat().st_size, source.stat().st_size)
            return output_path
        except Exception as e:
            safe_delete(output_path)
            raise CompressionError(f"GZIP压缩失败: {str(e)}") from e

    def decompress(self, source: Path, output_dir: Path, **kwargs) -> List[Path]:
        validated = validate_paths(source)[0]
        output_dir.mkdir(exist_ok=True, parents=True)
        output_path = output_dir / validated.stem

        try:
            with gzip.open(validated, 'rb') as f_in:
                with open(output_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                    self._update_progress(validated.stat().st_size, validated.stat().st_size)
            return [output_path]
        except gzip.BadGzipFile as e:
            raise CompressionError("GZIP文件损坏") from e


class SmartCompressor:
    """智能压缩器（自动选择最佳压缩方式）"""

    COMPRESSORS = {
        '.zip': ZipCompressor,
        '.gz': GzipCompressor,
        '.tgz': lambda: TarCompressor('gz')
    }

    def __init__(self, format_hint: Optional[str] = None):
        self.format = format_hint.lower() if format_hint else None

    def detect_format(self, path: Path) -> str:
        """自动检测压缩格式"""
        if self.format:
            return self.format
        ext = path.suffix.lower()
        if ext in self.COMPRESSORS:
            return ext
        # 通过文件头检测
        with open(path, 'rb') as f:
            header = f.read(4)
            if header.startswith(b'PK\x03\x04'):
                return '.zip'
            elif header.startswith(b'\x1f\x8b'):
                return '.gz'
        raise CompressionFormatError("无法识别的压缩格式")

    def get_compressor(self, path: Path) -> BaseCompressor:
        """获取合适的压缩器实例"""
        fmt = self.detect_format(path)
        compressor_cls = self.COMPRESSORS.get(fmt)
        if not compressor_cls:
            raise CompressionFormatError(f"不支持的压缩格式: {fmt}")
        return compressor_cls()


def compress_files(
        sources: List[Union[str, Path]],
        output_path: Union[str, Path],
        format: str = 'auto',
        password: Optional[str] = None,
        progress_callback: Optional[Callable] = None
) -> Path:
    """
    通用压缩入口函数
    :param sources: 源文件/目录列表
    :param output_path: 输出路径
    :param format: 压缩格式（auto/zip/gz）
    :param password: 加密密码
    :param progress_callback: 进度回调
    :return: 生成的压缩文件路径
    """
    sources = [Path(p) for p in sources]
    output_path = Path(output_path)

    if format == 'auto':
        if output_path.suffix:
            format = output_path.suffix
        else:
            format = '.zip'  # 默认格式

    compressor: BaseCompressor
    if format.lower() in ('.zip', '.zip'):
        compressor = ZipCompressor()
    elif format.lower() in ('.gz', '.gzip'):
        compressor = GzipCompressor()
    else:
        raise CompressionFormatError(f"不支持的压缩格式: {format}")

    if progress_callback:
        compressor.set_progress_callback(progress_callback)

    return compressor.compress(sources, output_path, password=password)


def decompress_file(
        source: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        password: Optional[str] = None,
        progress_callback: Optional[Callable] = None
) -> List[Path]:
    """
    通用解压入口函数
    :param source: 压缩文件路径
    :param output_dir: 输出目录（默认当前目录）
    :param password: 解压密码
    :param progress_callback: 进度回调
    :return: 解压后的文件列表
    """
    source = Path(source)
    output_dir = Path(output_dir) if output_dir else Path.cwd()

    compressor = SmartCompressor().get_compressor(source)
    if progress_callback:
        compressor.set_progress_callback(progress_callback)

    return compressor.decompress(source, output_dir, password=password)


# 示例用法
if __name__ == "__main__":
    # 压缩示例
    def print_progress(p: float):
        print(f"\r进度: {p * 100:.1f}%", end='')


    input_files = [Path("test1.txt"), Path("test2.jpg")]
    compress_files(
        input_files,
        "archive.zip",
        password="secret",
        progress_callback=print_progress
    )

    # 解压示例
    decompress_file("archive.zip", output_dir="output", password="secret")