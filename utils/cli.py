#命令行接口
"""
命令行界面工具模块
包含进度条、表格显示、颜色输出等组件
"""

import sys
import platform
from contextlib import contextmanager
from typing import Optional, Generator, List, Dict, Tuple
from time import time, sleep

# 第三方库导入
try:
    from tqdm import tqdm
    import colorama
    from colorama import Fore, Style
    from tabulate import tabulate
except ImportError as e:
    print("缺少依赖库，请先执行：")
    print("pip install tqdm colorama tabulate")
    raise e

# 初始化颜色支持
colorama.init(autoreset=True)


class CLIFormatter:
    """命令行格式化输出工具类"""

    COLORS = {
        'info': Fore.CYAN,
        'warning': Fore.YELLOW,
        'error': Fore.RED,
        'success': Fore.GREEN,
        'header': Fore.MAGENTA + Style.BRIGHT
    }

    @staticmethod
    def colorize(text: str, color: str) -> str:
        """为文本添加颜色"""
        return f"{CLIFormatter.COLORS.get(color, '')}{text}{Style.RESET_ALL}"

    @staticmethod
    def print_table(data: List[Dict], headers: List[str]) -> None:
        """打印格式化表格"""
        table_data = [[row[h] for h in headers] for row in data]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

    @staticmethod
    def confirm(prompt: str, default: bool = False) -> bool:
        """获取用户确认"""
        choices = 'Y/n' if default else 'y/N'
        prompt = f"{prompt} [{choices}]: "
        while True:
            sys.stdout.write(prompt)
            choice = sys.stdin.readline().strip().lower()
            if not choice:
                return default
            if choice in ('y', 'yes'):
                return True
            if choice in ('n', 'no'):
                return False
            print("请输入 y 或 n")


@contextmanager
def display_progress_bar(description: str, total: int) -> Generator[callable, None, None]:
    """带进度条的上下文管理器

    参数:
        description (str): 进度条描述
        total (int): 总进度数

    生成:
        Generator[callable, None, None]: 进度更新回调函数
    """
    pbar = tqdm(
        desc=CLIFormatter.colorize(description, 'info'),
        total=total,
        bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.BLUE, Fore.RESET),
        file=sys.stdout,
        dynamic_ncols=True
    )

    def update_progress(step: int = 1):
        pbar.update(step)
        pbar.refresh()

    try:
        yield update_progress
    finally:
        pbar.close()


def prompt_input(prompt: str,
                 input_type: type = str,
                 validate: callable = None,
                 default: Optional[str] = None) -> any:
    """带验证的输入提示

    参数:
        prompt (str): 提示信息
        input_type (type): 输入类型
        validate (callable): 验证函数
        default (Optional[str]): 默认值

    返回:
        any: 验证后的输入值
    """
    prompt_suffix = ""
    if default is not None:
        prompt_suffix = f" (默认: {default})"

    while True:
        try:
            user_input = input(f"{CLIFormatter.colorize(prompt, 'header')}{prompt_suffix}: ")
            if not user_input and default is not None:
                user_input = default
            converted = input_type(user_input)

            if validate and not validate(converted):
                raise ValueError("输入值不符合验证规则")

            return converted
        except ValueError as e:
            print(CLIFormatter.colorize(f"输入错误: {str(e)}", "error"))


def clear_screen():
    """清空终端屏幕"""
    system = platform.system()
    if system == 'Windows':
        os.system('cls')
    else:
        os.system('clear')


def display_file_info(file_info: dict):
    """显示文件信息表格"""
    headers = ["属性", "值"]
    rows = [
        {"属性": "文件名", "值": file_info["name"]},
        {"属性": "路径", "值": file_info["path"]},
        {"属性": "大小", "值": f"{file_info['size']} 字节"},
        {"属性": "类型", "值": file_info["type"]},
        {"属性": "修改时间", "值": file_info["mtime"]},
        {"属性": "属性", "值": ", ".join(file_info["attrs"])}
    ]
    CLIFormatter.print_table(rows, headers)


def show_spinner(duration: float = 3.0, message: str = "处理中"):
    """显示加载动画"""
    symbols = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    end_time = time() + duration
    i = 0

    try:
        while time() < end_time:
            sys.stdout.write(f"\r{CLIFormatter.colorize(symbols[i % len(symbols)], 'info')} {message}")
            sys.stdout.flush()
            sleep(0.1)
            i += 1
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write("\r" + " " * (len(message) + 10) + "\r")


if __name__ == "__main__":
    # 示例使用
    with display_progress_bar("测试进度条", 100) as update:
        for _ in range(100):
            sleep(0.05)
            update()

    user_name = prompt_input("请输入用户名",
                             validate=lambda x: len(x) >= 3,
                             default="guest")

    print(CLIFormatter.colorize("操作成功完成！", "success"))