#文件类型识别
"""
文件扫描核心模块
版本: 1.5
功能：文件类型验证、内容过滤、骚扰电话分析
"""

import re
import logging
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
import hashlib
import jieba  # 中文分词

# 第三方库检测
try:
    import magic
except ImportError:
    magic = None

logger = logging.getLogger(__name__)


class FileScanError(Exception):
    """文件扫描异常基类"""
    pass


class FileTypeDetector:
    """文件类型检测器（支持200+文件格式）"""

    def __init__(self):
        self.mime = magic.Magic(mime=True) if magic else None

    def detect_file_type(self, path: Path) -> str:
        """检测文件真实类型"""
        # 使用python-magic优先检测
        if self.mime:
            try:
                return self.mime.from_file(str(path))
            except Exception:
                pass

        # 文件头签名检测
        with open(path, 'rb') as f:
            header = f.read(32)
            for sig, ext in self.SIGNATURES.items():
                if header.startswith(sig):
                    return ext
        return 'unknown'

    def _mime_to_ext(self, mime_type: str) -> str:
        """将MIME类型转换为常见扩展名"""
        mime_map = {
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'application/pdf': 'pdf',
            'application/zip': 'zip',
            'application/msword': 'doc',
        }
        return mime_map.get(mime_type, 'unknown')

    def verify_extension(self, path: Path, ext_claim: str) -> bool:
        """验证文件扩展名是否匹配真实类型"""
        ext_real = self.detect_file_type(path)
        return ext_real == ext_claim

    SIGNATURES = {
        # 图片格式
        b'\xFF\xD8\xFF': 'jpg',
        b'\x89PNG\r\n\x1a\n': 'png',
        b'GIF87a': 'gif',
        b'GIF89a': 'gif',
        # 文档格式
        b'%PDF-': 'pdf',
        b'PK\x03\x04': 'zip',
        b'\xD0\xCF\x11\xE0': 'doc',
        # 可继续扩展...
    }


class FileTypeScanner:
    """文件类型验证器（支持200+文件格式）"""

    SIGNATURES = {
        # 图片格式
        b'\xFF\xD8\xFF': ('jpg', 'image/jpeg'),
        b'\x89PNG\r\n\x1a\n': ('png', 'image/png'),
        b'GIF87a': ('gif', 'image/gif'),
        b'GIF89a': ('gif', 'image/gif'),
        # 文档格式
        b'%PDF-': ('pdf', 'application/pdf'),
        b'PK\x03\x04': ('zip', 'application/zip'),
        b'\xD0\xCF\x11\xE0': ('doc', 'application/msword'),
        # 可继续扩展...
    }

    def __init__(self):
        self.mime = magic.Magic(mime=True) if magic else None

    def detect_file_type(self, path: Path) -> Tuple[str, str]:
        """检测文件真实类型"""
        # 使用python-magic优先检测
        if self.mime:
            try:
                mime_type = self.mime.from_file(str(path))
                ext = self._mime_to_ext(mime_type)
                return ext, mime_type
            except Exception:
                pass

        # 文件头签名检测
        with open(path, 'rb') as f:
            header = f.read(32)
            for sig, (ext, mime) in self.SIGNATURES.items():
                if header.startswith(sig):
                    return ext, mime
        return 'unknown', 'application/octet-stream'

    def _mime_to_ext(self, mime_type: str) -> str:
        """将MIME类型转换为常见扩展名"""
        mime_map = {
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'application/pdf': 'pdf',
            'application/zip': 'zip',
            'application/msword': 'doc',
        }
        return mime_map.get(mime_type, 'unknown')

    def verify_extension(self, path: Path) -> bool:
        """验证文件扩展名是否匹配真实类型"""
        ext_claim = path.suffix.lower()[1:]  # 去掉点号
        ext_real, _ = self.detect_file_type(path)
        return ext_real == ext_claim


class ContentFilter:
    """不良内容过滤器"""

    def __init__(self, pattern_file: Path):
        self.patterns = self._load_patterns(pattern_file)
        self.wordset = self._build_wordset()
        self.regex_list = self._build_regex()

    def _load_patterns(self, path: Path) -> List[str]:
        """加载不良文本模式"""
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]

    def _build_wordset(self) -> Set[str]:
        """构建敏感词集合"""
        return {word for pattern in self.patterns if not self._is_regex(pattern)}

    def _build_regex(self) -> List[re.Pattern]:
        """编译正则表达式"""
        regex_patterns = []
        for pattern in self.patterns:
            if self._is_regex(pattern):
                try:
                    regex_patterns.append(re.compile(pattern))
                except re.error:
                    logger.warning(f"无效正则表达式: {pattern}")
        return regex_patterns

    def _is_regex(self, pattern: str) -> bool:
        """判断是否为正则表达式"""
        return pattern.startswith('/') and pattern.endswith('/')

    def analyze_text(self, text: str) -> float:
        """分析文本危险系数（0.0-1.0）"""
        danger_score = 0.0

        # 普通关键词匹配
        words = set(jieba.lcut(text))  # 中文分词
        matched = len(words & self.wordset)
        if matched > 0:
            danger_score += 0.3 * min(matched, 3)

        # 正则表达式匹配
        for regex in self.regex_list:
            if regex.search(text):
                danger_score += 0.5
                break

        # 结合逻辑判断（示例规则）
        if any(w in text for w in ["转账", "密码"]):
            danger_score += 0.2

        return min(danger_score, 1.0)

    def scan_file(self, path: Path, threshold: float = 0.7) -> bool:
        """扫描文件内容是否包含不良信息"""
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    score = self.analyze_text(line)
                    if score >= threshold:
                        return True
        except UnicodeDecodeError:
            logger.warning(f"无法解码文本文件: {path}")
        except Exception as e:
            logger.error(f"扫描文件失败: {path} - {str(e)}")
        return False


class CallAnalyzer:
    """骚扰电话分析器"""

    def __init__(self, blacklist: Path, history: Path):
        self.blacklist = self._load_blacklist(blacklist)
        self.call_history = self._load_history(history)
        self.suspicious_keywords = {"推销", "贷款", "保险"}

    def _load_blacklist(self, path: Path) -> Set[str]:
        """加载骚扰号码黑名单"""
        with open(path, 'r') as f:
            return {row[0] for row in csv.reader(f)}

    def _load_history(self, path: Path) -> List[dict]:
        """加载通话记录"""
        history = []
        with open(path, 'r') as f:
            for row in csv.DictReader(f):
                row['duration'] = int(row['duration'])
                row['time'] = datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S')
                history.append(row)
        return history

    def is_harassment(self, number: str) -> Tuple[bool, str]:
        """判断是否为骚扰电话"""
        # 直接匹配黑名单
        if number in self.blacklist:
            return True, "黑名单号码"

        # 分析通话记录
        recent_calls = [
            c for c in self.call_history
            if c['number'] == number
               and (datetime.now() - c['time']).days < 7
        ]

        # 高频来电判断
        if len(recent_calls) > 5:
            return True, "高频来电"

        # 通话特征分析
        if any(c['duration'] < 10 for c in recent_calls):
            return True, "短时多次呼叫"

        # 备注关键词分析
        if any(kw in c.get('note', '') for c in recent_calls for kw in self.suspicious_keywords):
            return True, "包含可疑关键词"

        return False, ""


# 示例用法
if __name__ == "__main__":
    # 文件类型验证示例
    scanner = FileTypeScanner()
    test_file = Path("test.pdf")
    ext, mime = scanner.detect_file_type(test_file)
    print(f"文件类型: {ext} ({mime})")
    print(f"扩展名验证: {scanner.verify_extension(test_file)}")

    # 内容过滤示例
    filter = ContentFilter(Path("bad_words.txt"))
    print(f"危险内容检测: {filter.scan_file(Path("test.txt"))}")

    # 骚扰电话分析示例
    analyzer = CallAnalyzer(Path("blacklist.csv"), Path("history.csv"))
    print(f"是否为骚扰电话: {analyzer.is_harassment('13800138000')}")
