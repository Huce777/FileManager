#自定义打包
"""
自定义文件打包核心模块
版本: 3.2
功能：支持多种打包规则、加密文件头、分块切割等
"""

import logging
#import os
import struct
import zlib
import hashlib
import random
from pathlib import Path
from typing import Callable,List, Dict, Generator, Optional
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes
from utils.helpers import (
    validate_paths,
    safe_delete,
    #convert_size,
    FileSystemError
)
from core.encryption import KeyManager

logger = logging.getLogger(__name__)


class PackingError(FileSystemError):
    """打包相关异常基类"""
    pass


class BasePackager:
    """打包器抽象基类"""

    HEADER_MAGIC = b'CUSPKG'
    VERSION = 3
    CHUNK_SIZE = 4 * 1024 * 1024  # 4MB分块

    def __init__(self, key: Optional[bytes] = None):
        self.key_manager = KeyManager(key)
        self.cipher = None
        self._progress_callback = None

    def set_progress_callback(self, callback: Callable[[float], None]):
        """设置进度回调函数"""
        self._progress_callback = callback

    def _update_progress(self, current: int, total: int):
        """更新进度信息"""
        if self._progress_callback and total > 0:
            progress = min(current / total, 1.0)
            self._progress_callback(progress)

    def _generate_header(self, files: List[Dict]) -> bytes:
        """生成加密文件头"""
        header_data = bytearray()
        # 头部结构：[文件数量(4B)] + [文件条目]*n
        header_data += struct.pack('!I', len(files))

        for file_info in files:
            # 文件条目结构：路径长度(2B) + UTF8路径 + 文件大小(8B) + SHA256(32B)
            path_encoded = file_info['path'].encode('utf-8')
            header_data += struct.pack('!H', len(path_encoded))
            header_data += path_encoded
            header_data += struct.pack('!Q', file_info['size'])
            header_data += bytes.fromhex(file_info['sha256'])

        # 添加校验和
        checksum = zlib.crc32(header_data)
        header_data = struct.pack('!I', checksum) + header_data

        # 加密头部
        if self.key_manager.has_key():
            iv = get_random_bytes(16)
            cipher = AES.new(self.key_manager.get_key(), AES.MODE_GCM, nonce=iv)
            encrypted_header, tag = cipher.encrypt_and_digest(header_data)
            return self.HEADER_MAGIC + struct.pack('!B', self.VERSION) + iv + tag + encrypted_header
        else:
            return self.HEADER_MAGIC + struct.pack('!B', self.VERSION) + header_data

    def _parse_header(self, header_data: bytes) -> List[Dict]:
        """解析加密文件头"""
        if not header_data.startswith(self.HEADER_MAGIC):
            raise PackingError("无效的打包文件格式")

        version = struct.unpack('!B', header_data[6:7])[0]
        if version != self.VERSION:
            raise PackingError(f"不支持的版本号: {version}")

        if self.key_manager.has_key():
            iv = header_data[7:23]
            tag = header_data[23:39]
            encrypted = header_data[39:]
            cipher = AES.new(self.key_manager.get_key(), AES.MODE_GCM, nonce=iv)
            header_data = cipher.decrypt_and_verify(encrypted, tag)
        else:
            header_data = header_data[7:]

        checksum = struct.unpack('!I', header_data[:4])[0]
        if zlib.crc32(header_data[4:]) != checksum:
            raise PackingError("文件头校验失败")

        file_count = struct.unpack('!I', header_data[4:8])[0]
        offset = 8
        files = []

        for _ in range(file_count):
            path_len = struct.unpack('!H', header_data[offset:offset + 2])[0]
            offset += 2
            path = header_data[offset:offset + path_len].decode('utf-8')
            offset += path_len
            size = struct.unpack('!Q', header_data[offset:offset + 8])[0]
            offset += 8
            sha256 = header_data[offset:offset + 32].hex()
            offset += 32
            files.append({'path': path, 'size': size, 'sha256': sha256})

        return files



class CustomPackager(BasePackager):
    """自定义打包器"""

    def package(self, files: List[Path], output: Path) -> Path:
        """打包文件"""
        validated = validate_paths(*files)
        file_list = []
        total_size = 0

        # 准备文件信息
        for path in validated:
            sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
            file_list.append({
                'path': str(path.relative_to(Path.cwd())),
                'size': path.stat().st_size,
                'sha256': sha256
            })
            total_size += path.stat().st_size

        # 生成文件头
        header = self._generate_header(file_list)
        processed = 0

        try:
            with open(output, 'wb') as fout:
                # 写入文件头
                fout.write(header)

                # 写入文件内容
                for file_info, path in zip(file_list, validated):
                    with open(path, 'rb') as fin:
                        while chunk := fin.read(self.CHUNK_SIZE):
                            fout.write(chunk)
                            processed += len(chunk)
                            self._update_progress(processed, total_size)

            return output
        except Exception as e:
            safe_delete(output)
            raise PackingError(f"打包失败: {str(e)}") from e

    def unpack(self, package: Path, output_dir: Path) -> List[Path]:
        """解包文件"""
        validated = validate_paths(package)
        output_dir.mkdir(exist_ok=True, parents=True)

        with open(package, 'rb') as fin:
            # 读取文件头
            magic = fin.read(len(self.HEADER_MAGIC))
            if magic != self.HEADER_MAGIC:
                raise PackingError("无效的打包文件")

            header_size = struct.unpack('!I', fin.read(4))[0]
            fin.seek(0)
            header_data = fin.read(header_size)
            files = self._parse_header(header_data)

            # 提取文件
            extracted = []
            total_size = sum(f['size'] for f in files)
            processed = 0

            for file_info in files:
                output_path = output_dir / file_info['path']
                output_path.parent.mkdir(exist_ok=True, parents=True)

                with open(output_path, 'wb') as fout:
                    remaining = file_info['size']
                    while remaining > 0:
                        chunk_size = min(remaining, self.CHUNK_SIZE)
                        chunk = fin.read(chunk_size)
                        if not chunk:
                            raise PackingError("文件数据不完整")
                        fout.write(chunk)
                        remaining -= len(chunk)
                        processed += len(chunk)
                        self._update_progress(processed, total_size)

                # 验证哈希
                current_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
                if current_hash != file_info['sha256']:
                    safe_delete(output_path)
                    raise PackingError(f"文件校验失败: {file_info['path']}")

                extracted.append(output_path)

            return extracted


class SequentialPackager(BasePackager):
    """顺序打包器（文件头前置）"""

    def package(self, files: List[Path], output: Path) -> Path:
        """打包文件"""
        validated = validate_paths(*files)
        file_list = []
        total_size = 0

        # 准备文件信息
        for path in validated:
            sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
            file_list.append({
                'path': str(path.relative_to(Path.cwd())),
                'size': path.stat().st_size,
                'sha256': sha256
            })
            total_size += path.stat().st_size

        # 生成文件头
        header = self._generate_header(file_list)
        processed = 0

        try:
            with open(output, 'wb') as fout:
                # 写入文件头
                fout.write(header)

                # 写入文件内容
                for file_info, path in zip(file_list, validated):
                    with open(path, 'rb') as fin:
                        while chunk := fin.read(self.CHUNK_SIZE):
                            fout.write(chunk)
                            processed += len(chunk)
                            self._update_progress(processed, total_size)

            return output
        except Exception as e:
            safe_delete(output)
            raise PackingError(f"打包失败: {str(e)}") from e

    def unpack(self, package: Path, output_dir: Path) -> List[Path]:
        """解包文件"""
        validated = validate_paths(package)
        output_dir.mkdir(exist_ok=True, parents=True)

        with open(package, 'rb') as fin:
            # 读取文件头
            magic = fin.read(len(self.HEADER_MAGIC))
            if magic != self.HEADER_MAGIC:
                raise PackingError("无效的打包文件")

            header_size = struct.unpack('!I', fin.read(4))[0]
            fin.seek(0)
            header_data = fin.read(header_size)
            files = self._parse_header(header_data)

            # 提取文件
            extracted = []
            total_size = sum(f['size'] for f in files)
            processed = 0

            for file_info in files:
                output_path = output_dir / file_info['path']
                output_path.parent.mkdir(exist_ok=True, parents=True)

                with open(output_path, 'wb') as fout:
                    remaining = file_info['size']
                    while remaining > 0:
                        chunk_size = min(remaining, self.CHUNK_SIZE)
                        chunk = fin.read(chunk_size)
                        if not chunk:
                            raise PackingError("文件数据不完整")
                        fout.write(chunk)
                        remaining -= len(chunk)
                        processed += len(chunk)
                        self._update_progress(processed, total_size)

                # 验证哈希
                current_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
                if current_hash != file_info['sha256']:
                    safe_delete(output_path)
                    raise PackingError(f"文件校验失败: {file_info['path']}")

                extracted.append(output_path)

            return extracted


class ChunkedPackager(BasePackager):
    """分块切割打包器"""

    def __init__(self, key: Optional[bytes] = None, chunk_size: int = 1024 * 1024):
        super().__init__(key)
        self.chunk_size = chunk_size
        self.block_map = {}

    def _split_file(self, path: Path) -> Generator[bytes, None, None]:
        """分块生成器"""
        with open(path, 'rb') as f:
            while chunk := f.read(self.chunk_size):
                yield chunk

    def package(self, files: List[Path], output: Path) -> Path:
        """分块打包文件"""
        validated = validate_paths(*files)
        file_blocks = []
        total_blocks = 0

        # 生成分块映射表
        for path in validated:
            blocks = []
            for chunk in self._split_file(path):
                block_id = hashlib.sha256(chunk).digest()[:16]
                blocks.append(block_id)
                self.block_map[block_id] = chunk
                total_blocks += 1
            file_blocks.append({
                'path': str(path.relative_to(Path.cwd())),
                'blocks': blocks
            })

        # 打乱块顺序
        all_blocks = list(self.block_map.keys())
        random.shuffle(all_blocks)

        # 生成文件头
        header = self._generate_header(file_blocks)
        processed = 0

        try:
            with open(output, 'wb') as fout:
                fout.write(header)
                # 写入块位置索引
                index_data = bytearray()
                for block_id in all_blocks:
                    index_data += block_id
                fout.write(index_data)

                # 写入实际块数据
                for block_id in all_blocks:
                    chunk = self.block_map[block_id]
                    encrypted = self._encrypt_chunk(chunk)
                    fout.write(encrypted)
                    processed += len(chunk)
                    self._update_progress(processed, total_blocks * self.chunk_size)

            return output
        except Exception as e:
            safe_delete(output)
            raise PackingError(f"分块打包失败: {str(e)}") from e

    def _encrypt_chunk(self, chunk: bytes) -> bytes:
        """加密数据块"""
        if self.key_manager.has_key():
            iv = get_random_bytes(16)
            cipher = AES.new(self.key_manager.get_key(), AES.MODE_CBC, iv)
            return iv + cipher.encrypt(pad(chunk, AES.block_size))
        return chunk


class PackageManager:
    """打包管理入口类"""

    PACKAGE_TYPES = {
        'sequential': SequentialPackager,
        'chunked': ChunkedPackager,
        'custom': None  # 可扩展自定义类型
    }

    def __init__(self, pack_type: str = 'sequential', key: Optional[bytes] = None):
        self.packager = self.PACKAGE_TYPES.get(pack_type.lower(), SequentialPackager)(key)
        if not self.packager:
            raise PackingError(f"不支持的打包类型: {pack_type}")

    def pack(self, files: List[Path], output: Path) -> Path:
        """执行打包操作"""
        return self.packager.package(files, output)

    def unpack(self, package: Path, output_dir: Path) -> List[Path]:
        """执行解包操作"""
        return self.packager.unpack(package, output_dir)


# 高级加密打包示例
class SecureChunkedPackager(ChunkedPackager):
    """安全分块打包器（增强加密）"""

    def _generate_header(self, files: List[Dict]) -> bytes:
        header = super()._generate_header(files)
        # 添加额外校验信息
        checksum = hashlib.sha3_256(header).digest()
        return header + checksum

    def _parse_header(self, header_data: bytes) -> List[Dict]:
        checksum = header_data[-32:]
        if hashlib.sha3_256(header_data[:-32]).digest() != checksum:
            raise PackingError("头部校验失败")
        return super()._parse_header(header_data[:-32])


# 示例用法
if __name__ == "__main__":
    # 顺序打包示例
    packager = PackageManager('sequential')
    packed_file = packager.pack(
        [Path('file1.txt'), Path('file2.jpg')],
        Path('archive.pkg')
    )

    # 解包示例
    unpacked_files = packager.unpack(
        Path('archive.pkg'),
        Path('output_dir')
    )

    # 分块打包示例
    chunk_packager = PackageManager('chunked', key=b'secret_key')
    chunk_packager.pack(
        [Path('largefile.bin')],
        Path('chunked.pkg')
    )