#加密解密
"""
文件加密解密核心模块
版本: 3.0
支持算法：AES-256-GCM, ChaCha20-Poly1305
"""

import os
import logging
import struct
import hashlib
from pathlib import Path
from typing import Optional, Tuple, Callable
from Crypto.Cipher import AES, ChaCha20_Poly1305
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad, unpad
from utils.helpers import (
    validate_paths,
    safe_delete,
    convert_size,
    FileSystemError
)

# 日志配置
logger = logging.getLogger(__name__)


class EncryptionError(FileSystemError):
    """加密相关异常基类"""
    pass


class DecryptionError(EncryptionError):
    """解密失败异常"""
    pass


class KeyDerivationError(EncryptionError):
    """密钥派生异常"""
    pass


class AESEncryptor:  # 必须与导入名称完全一致
    def __init__(self, key):
        self.key = key

    def encrypt(self, data: bytes) -> bytes:
        """加密数据"""
        cipher = AES.new(self.key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        return cipher.nonce + tag + ciphertext

    def decrypt(self, data: bytes) -> bytes:
        """解密数据"""
        nonce, tag, ciphertext = struct.unpack('!16s16s%ds' % (len(data) - 32), data)
        cipher = AES.new(self.key, AES.MODE_EAX)
        try:
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            return unpad(plaintext, AES.block_size)
        except ValueError:
            raise DecryptionError("解密失败")


class ChaCha20Encryptor:  # 必须与导入名称完全一致
    def __init__(self, key):
        self.key = key

    def encrypt(self, data: bytes) -> bytes:
        """加密数据"""
        cipher = ChaCha20_Poly1305.new(key=self.key)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        return cipher.nonce + tag + ciphertext

    def decrypt(self, data: bytes) -> bytes:
        """解密数据"""
        nonce, tag, ciphertext = struct.unpack('!16s16s%ds' % (len(data) - 32), data)
        cipher = ChaCha20_Poly1305.new(key=self.key, nonce=nonce)
        try:
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            return unpad(plaintext, 1)
        except ValueError:
            raise DecryptionError("解密失败")






class KeyManager:
    """安全密钥管理类"""

    SALT_SIZE = 32  # 256-bit salt
    KDF_ITERATIONS = 100_000  # PBKDF2迭代次数
    KEY_LENGTHS = {
        'AES-256': 32,
        'CHACHA20': 32
    }

    def __init__(self, master_key: Optional[bytes] = None):
        self._key_cache = {}
        if master_key:
            self.store_key('master', master_key)

    @staticmethod
    def generate_key(algorithm: str = 'AES-256') -> bytes:
        """生成随机加密密钥"""
        key_len = KeyManager.KEY_LENGTHS.get(algorithm)
        if not key_len:
            raise KeyDerivationError(f"不支持的算法: {algorithm}")
        return get_random_bytes(key_len)

    @staticmethod
    def derive_key(password: str, salt: bytes, algorithm: str = 'AES-256') -> bytes:
        """从密码派生密钥"""
        key_len = KeyManager.KEY_LENGTHS.get(algorithm)
        if not key_len:
            raise KeyDerivationError(f"不支持的算法: {algorithm}")

        try:
            return PBKDF2(
                password.encode('utf-8'),
                salt,
                dkLen=key_len,
                count=KeyManager.KDF_ITERATIONS,
                hmac_hash_module=hashlib.sha256
            )
        except Exception as e:
            raise KeyDerivationError(f"密钥派生失败: {str(e)}") from e

    def store_key(self, key_id: str, key: bytes) -> None:
        """安全存储密钥（内存中）"""
        self._key_cache[key_id] = key

    def get_key(self, key_id: str) -> bytes:
        """获取存储的密钥"""
        if key_id not in self._key_cache:
            raise KeyDerivationError(f"密钥不存在: {key_id}")
        return self._key_cache[key_id]


class FileEncryptor:
    """文件加密解密处理器"""

    HEADER_FORMAT = '!32s16s16s'  # salt, iv, tag
    CHUNK_SIZE = 1024 * 1024  # 1MB

    def __init__(self, algorithm: str = 'AES-256-GCM'):
        self.algorithm = algorithm.upper()
        self._progress_callback = None

    def set_progress_callback(self, callback: Callable[[float], None]):
        """设置进度回调函数"""
        self._progress_callback = callback

    def _update_progress(self, processed: int, total: int):
        """更新进度信息"""
        if self._progress_callback and total > 0:
            progress = min(processed / total, 1.0)
            self._progress_callback(progress)

    def encrypt_file(
            self,
            input_path: Path,
            output_path: Optional[Path] = None,
            key: Optional[bytes] = None,
            password: Optional[str] = None
    ) -> Path:
        """
        加密文件
        :param input_path: 输入文件路径
        :param output_path: 输出文件路径（默认添加.enc后缀）
        :param key: 直接使用二进制密钥
        :param password: 使用密码派生密钥
        :return: 加密后的文件路径
        """
        input_path = validate_paths(input_path)[0]
        output_path = output_path or input_path.with_suffix('.enc')

        # 生成加密参数
        salt = get_random_bytes(KeyManager.SALT_SIZE)
        iv = get_random_bytes(16)

        # 获取加密密钥
        if password and not key:
            key = KeyManager.derive_key(password, salt, self.algorithm.split('-')[0])
        elif not key:
            raise EncryptionError("必须提供密钥或密码")

        try:
            # 初始化加密器
            if self.algorithm.startswith('AES'):
                cipher = AES.new(key, AES.MODE_GCM, nonce=iv, mac_len=16)
            elif self.algorithm.startswith('CHACHA20'):
                cipher = ChaCha20_Poly1305.new(key=key, nonce=iv)
            else:
                raise EncryptionError(f"不支持的算法: {self.algorithm}")

            total_size = input_path.stat().st_size
            processed = 0

            with open(input_path, 'rb') as fin, open(output_path, 'wb') as fout:
                # 写入文件头
                fout.write(struct.pack(self.HEADER_FORMAT, salt, iv, b''))  # 预留tag位置

                # 分块加密
                while True:
                    chunk = fin.read(self.CHUNK_SIZE)
                    if not chunk:
                        break
                    encrypted_chunk = cipher.encrypt(pad(chunk, AES.block_size))
                    fout.write(encrypted_chunk)
                    processed += len(chunk)
                    self._update_progress(processed, total_size)

                # 获取认证标签并回写
                if self.algorithm.endswith('GCM') or self.algorithm.endswith('POLY1305'):
                    tag = cipher.digest()
                    fout.seek(struct.calcsize(self.HEADER_FORMAT) - len(tag))
                    fout.write(tag)

            return output_path
        except Exception as e:
            safe_delete(output_path)
            raise EncryptionError(f"加密失败: {str(e)}") from e

    def decrypt_file(
            self,
            input_path: Path,
            output_path: Optional[Path] = None,
            key: Optional[bytes] = None,
            password: Optional[str] = None
    ) -> Path:
        """
        解密文件
        :param input_path: 加密文件路径
        :param output_path: 输出文件路径
        :param key: 直接使用二进制密钥
        :param password: 使用密码派生密钥
        :return: 解密后的文件路径
        """
        input_path = validate_paths(input_path)[0]
        output_path = output_path or input_path.with_suffix('.dec')

        try:
            with open(input_path, 'rb') as fin:
                # 读取文件头
                header_size = struct.calcsize(self.HEADER_FORMAT)
                header = fin.read(header_size)
                salt, iv, tag = struct.unpack(self.HEADER_FORMAT, header)

                # 获取解密密钥
                if password and not key:
                    key = KeyManager.derive_key(password, salt, self.algorithm.split('-')[0])
                elif not key:
                    raise DecryptionError("必须提供密钥或密码")

                # 初始化解密器
                if self.algorithm.startswith('AES'):
                    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
                elif self.algorithm.startswith('CHACHA20'):
                    cipher = ChaCha20_Poly1305.new(key=key, nonce=iv)
                else:
                    raise DecryptionError(f"不支持的算法: {self.algorithm}")

                # 设置认证标签
                if tag:
                    cipher.digest = tag

            total_size = input_path.stat().st_size - header_size
            processed = 0

            with open(input_path, 'rb') as fin, open(output_path, 'wb') as fout:
                fin.seek(header_size)

                while True:
                    chunk = fin.read(self.CHUNK_SIZE)
                    if not chunk:
                        break
                    decrypted_chunk = unpad(cipher.decrypt(chunk), AES.block_size)
                    fout.write(decrypted_chunk)
                    processed += len(chunk)
                    self._update_progress(processed, total_size)

                # 验证数据完整性
                try:
                    cipher.verify(tag)
                except ValueError as e:
                    safe_delete(output_path)
                    raise DecryptionError("数据完整性校验失败") from e

            return output_path
        except Exception as e:
            safe_delete(output_path)
            raise DecryptionError(f"解密失败: {str(e)}") from e


class HybridEncryptor:
    """混合加密系统（结合对称和非对称加密）"""

    def __init__(self, rsa_key_size=2048):
        from Crypto.PublicKey import RSA
        self.key = RSA.generate(rsa_key_size)

    def encrypt_with_public_key(self, data: bytes) -> bytes:
        """使用RSA公钥加密数据"""
        from Crypto.Cipher import PKCS1_OAEP
        cipher = PKCS1_OAEP.new(self.key.publickey())
        return cipher.encrypt(data)

    def decrypt_with_private_key(self, ciphertext: bytes) -> bytes:
        """使用RSA私钥解密数据"""
        from Crypto.Cipher import PKCS1_OAEP
        cipher = PKCS1_OAEP.new(self.key)
        return cipher.decrypt(ciphertext)


def secure_key_storage(key: bytes, output_path: Path, password: str) -> None:
    """安全存储密钥到文件"""
    salt = get_random_bytes(32)
    kdf = PBKDF2(password.encode(), salt, dkLen=32, count=100_000)
    cipher = AES.new(kdf, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(key)

    with open(output_path, 'wb') as f:
        f.write(salt)
        f.write(cipher.nonce)
        f.write(tag)
        f.write(ciphertext)


def load_secure_key(key_path: Path, password: str) -> bytes:
    """从加密文件加载密钥"""
    with open(key_path, 'rb') as f:
        salt = f.read(32)
        nonce = f.read(16)
        tag = f.read(16)
        ciphertext = f.read()

    kdf = PBKDF2(password.encode(), salt, dkLen=32, count=100_000)
    cipher = AES.new(kdf, AES.MODE_GCM, nonce=nonce)
    try:
        return cipher.decrypt_and_verify(ciphertext, tag)
    except ValueError as e:
        raise DecryptionError("密钥解密失败") from e


# 示例用法
if __name__ == "__main__":
    # 初始化加密器
    encryptor = FileEncryptor(algorithm='AES-256-GCM')
    key_manager = KeyManager()

    # 生成并存储密钥
    master_key = KeyManager.generate_key()
    key_manager.store_key('master', master_key)

    # 加密文件
    input_file = Path("secret.txt")
    encrypted_file = encryptor.encrypt_file(
        input_file,
        key=master_key
    )
    print(f"加密文件已保存至: {encrypted_file}")

    # 解密文件
    decrypted_file = encryptor.decrypt_file(
        encrypted_file,
        key=master_key
    )
    print(f"解密文件已保存至: {decrypted_file}")

    # 安全存储密钥
    secure_key_storage(master_key, Path("master.key"), "supersecretpassword")