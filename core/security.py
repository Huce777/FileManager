#安全相关
"""
安全增强核心模块
版本: 4.2
功能：密钥保护、反调试、代码混淆、完整性校验
"""

import sys
import hashlib
import ctypes
import inspect
import random
from pathlib import Path
from typing import Optional, List, Tuple
from Crypto.Cipher import AES
from Crypto.Util import Counter

# 反逆向工程检测库
try:
    import pytransform
except ImportError:
    pytransform = None

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """安全相关异常基类"""
    pass


class AntiDebugger:
    """反调试检测器（跨平台）"""

    WINDOWS_CHECKS = [
        'IsDebuggerPresent',
        'CheckRemoteDebuggerPresent'
    ]

    LINUX_CHECKS = [
        'ptrace',
        'getppid'
    ]

    def __init__(self):
        self.os_type = sys.platform
        self._detected = False

    def _windows_checks(self) -> bool:
        kernel32 = ctypes.windll.kernel32
        for check in self.WINDOWS_CHECKS:
            func = getattr(kernel32, check, None)
            if func and func():
                return True
        return False

    def _linux_checks(self) -> bool:
        try:
            # 检测ptrace
            if ctypes.CDLL(None).ptrace(0x20, 0, 0, 0) != 0:
                return True
            # 检测父进程
            if Path('/proc/self/status').read_text().find('TracerPid: 0') == -1:
                return True
        except:
            pass
        return False

    def detect_debugger(self) -> bool:
        """检测调试器存在"""
        if self._detected:
            return True

        if self.os_type.startswith('win32'):
            result = self._windows_checks()
        elif self.os_type.startswith('linux'):
            result = self._linux_checks()
        else:
            result = False

        self._detected = result
        return result


class CodeIntegrity:
    """代码完整性校验器"""

    def __init__(self):
        self.valid_hashes = {
            'security': self._calculate_hash(__file__),
            'main': self._calculate_hash(Path('main.py'))
        }

    def _calculate_hash(self, path: Path) -> str:
        """计算文件SHA3-256哈希"""
        hasher = hashlib.sha3_256()
        with open(path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def verify_integrity(self) -> bool:
        """校验关键文件完整性"""
        try:
            for module, expected in self.valid_hashes.items():
                current = self._calculate_hash(Path(f"{module}.py"))
                if current != expected:
                    raise SecurityError(f"文件 {module} 已被篡改")
            return True
        except Exception as e:
            self._safe_shutdown(str(e))

    def _safe_shutdown(self, reason: str):
        """安全关闭程序"""
        logger.critical(f"安全违规: {reason}")
        sys.exit(1)


class SecurityManager:
    """安全管理器（包含密钥保护、白盒加密、运行时保护）"""

    def __init__(self):
        self.key_vault = KeyVault()
        self.whitebox_crypto = WhiteboxCrypto(self.key_vault.assemble_key())
        self.runtime_protection = RuntimeProtection()

    def encrypt_data(self, data: bytes) -> bytes:
        """白盒加密数据"""
        return self.whitebox_crypto.encrypt(data)

    def secure_wipe(self):
        """安全擦除内存中的密钥"""
        self.key_vault.secure_wipe()     # 安全擦除密钥分片
        self.whitebox_crypto = None      # 安全销毁白盒加密器
        self.runtime_protection = None   # 安全销毁运行时保护器

    def enable_protection(self):
        """启用持续保护"""
        self.runtime_protection.enable_protection()

    def disable_protection(self):
        """禁用持续保护"""
        self.runtime_protection.disable_protection()     # 禁用运行时保护器

    def __del__(self):
        self.secure_wipe()   # 安全销毁密钥管理器
                                                                                # 示例密钥分片存储（实际应分散在不同位置）

class KeyVault:
    """安全密钥存储器（支持分片存储）"""

    def __init__(self):
        self.key_fragments = self._load_fragments()
        self._anti_dump = True

    def _load_fragments(self) -> List[bytes]:
        """从隐蔽位置加载密钥分片"""
        fragments = []
        # 示例存储位置（实际应分散在不同位置）
        locations = [
            self._get_embedded_data(0x100),
            self._get_stack_data(),
            self._get_code_segment()
        ]
        for data in locations:
            fragments.append(self._extract_fragment(data))
        return fragments

    def _get_embedded_data(self, offset: int) -> bytes:
        """从二进制文件读取隐藏数据"""
        try:
            with open(sys.executable, 'rb') as f:
                f.seek(offset)
                return f.read(128)
        except:
            return b''

    def _get_stack_data(self) -> bytes:
        """从调用栈获取混淆数据"""
        frame = inspect.currentframe()
        return bytes(str(frame.f_back.f_locals), 'utf-8')

    def _get_code_segment(self) -> bytes:
        """从代码段获取混淆数据"""
        return inspect.getsource(KeyVault).encode('utf-8')

    def _extract_fragment(self, data: bytes) -> bytes:
        """使用XOR算法提取密钥分片"""
        mask = b'\x5F' * len(data)
        return bytes([a ^ b for a, b in zip(data, mask)])

    def assemble_key(self) -> bytes:
        """组合分片生成主密钥"""
        if len(self.key_fragments) < 3:
            raise SecurityError("密钥分片不完整")

        # 使用AES-CTR模式解密主密钥
        combined = b''.join(self.key_fragments)
        counter = Counter.new(128, initial_value=int.from_bytes(combined[:16], 'big'))
        cipher = AES.new(combined[16:48], AES.MODE_CTR, counter=counter)
        return cipher.decrypt(combined[48:])

    def secure_wipe(self):
        """安全擦除内存中的密钥"""
        for i in range(len(self.key_fragments)):
            self.key_fragments[i] = os.urandom(len(self.key_fragments[i]))
        self.key_fragments = []


class WhiteboxCrypto:
    """白盒加密实现（AES-256）"""

    def __init__(self, key: bytes):
        self._tables = self._generate_whitebox_tables(key)

    def _generate_whitebox_tables(self, key: bytes) -> List[list]:
        """生成白盒加密查表数据"""
        cipher = AES.new(key, AES.MODE_ECB)
        tables = []
        # 生成混淆的S盒（示例实现）
        for _ in range(16):
            table = [random.getrandbits(8) for _ in range(256)]
            tables.append(table)
        return tables

    def encrypt(self, data: bytes) -> bytes:
        """白盒加密方法"""
        if len(data) != 16:
            raise ValueError("数据长度必须为16字节")

        state = list(data)
        # 执行10轮混淆查表操作
        for round in range(10):
            state = [self._tables[round][b] for b in state]
            # 添加行移位混淆
            state = self._shift_rows(state)
        return bytes(state)

    def _shift_rows(self, state: List[int]) -> List[int]:
        """行移位混淆操作"""
        return [
            state[0], state[5], state[10], state[15],
            state[4], state[9], state[14], state[3],
            state[8], state[13], state[2], state[7],
            state[12], state[1], state[6], state[11]
        ]


class RuntimeProtection:
    """运行时保护机制"""

    def __init__(self):
        self._checks = [
            self.check_debugger,
            self.check_memory_tamper,
            self.check_hooks
        ]

    def enable_protection(self):
        """启用持续保护"""
        import threading
        self._timer = threading.Timer(5.0, self._run_checks)
        self._timer.daemon = True
        self._timer.start()

    def _run_checks(self):
        """执行安全检查"""
        for check in self._checks:
            if check():
                self._safe_terminate()
        self.enable_protection()

    def check_debugger(self) -> bool:
        return AntiDebugger().detect_debugger()

    def check_memory_tamper(self) -> bool:
        # 检测关键内存区域是否被修改
        current_hash = hashlib.sha3_256(pytransform.get_data() if pytransform else b'').hexdigest()
        return current_hash != "预设哈希值"

    def check_hooks(self) -> bool:
        # 检测API钩子（Windows示例）
        if sys.platform == 'win32':
            ntdll = ctypes.windll.ntdll
            return ntdll.DbgUiRemoteBreakin != id(ntdll.DbgUiRemoteBreakin)
        return False

    def _safe_terminate(self):
        """安全终止程序"""
        KeyVault().secure_wipe()
        os._exit(1)


# 安全增强装饰器
def secure_execute(func):
    """安全执行装饰器（包含完整性校验和反调试）"""

    def wrapper(*args, **kwargs):
        CodeIntegrity().verify_integrity()
        if AntiDebugger().detect_debugger():
            RuntimeProtection()._safe_terminate()
        return func(*args, **kwargs)

    return wrapper


# 示例密钥分片存储（实际应分散在不同位置）
FRAGMENT1 = b'\x12\x34\x56\x78'  # 隐藏在二进制文件
FRAGMENT2 = b'\x9A\xBC\xDE\xF0'  # 隐藏在代码段
FRAGMENT3 = b'\x11\x22\x33\x44'  # 隐藏在资源文件

if __name__ == "__main__":
    # 示例使用
    vault = KeyVault()
    try:
        master_key = vault.assemble_key()
        print(f"主密钥安全加载: {master_key.hex()}")
    except SecurityError as e:
        print(f"密钥错误: {str(e)}")

    # 初始化运行时保护
    RuntimeProtection().enable_protection()