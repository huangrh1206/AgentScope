# -*- coding: utf-8 -*-
"""三国狼人杀游戏日志模块 - 实时将终端输出保存为 Markdown"""
import io
import os
import sys
from datetime import datetime
from typing import TextIO


class GameLogger:
    """游戏日志记录器，实时保存终端输出为 Markdown 格式"""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

        # 生成带时间戳的日志文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_path = os.path.join(log_dir, f"game_{timestamp}.md")

        self._file: TextIO | None = None
        self._original_stdout: TextIO | None = None
        self._tee: "_TeeWriter | None" = None

    # ------------------------------------------------------------------
    # 上下文管理 / 手动启停
    # ------------------------------------------------------------------
    def start(self) -> "GameLogger":
        """开始记录：劫持 stdout，同时写到终端 + 日志文件"""
        self._file = open(
            self.log_path, "w", encoding="utf-8", buffering=1  # 行缓冲
        )
        # 写入 Markdown 头部
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._file.write(f"# 🎮 三国狼人杀 游戏日志\n\n")
        self._file.write(f"> 📅 游戏时间：{now}\n\n")
        self._file.write(f"---\n\n")
        self._file.flush()

        # 用 TeeWriter 同时输出到终端和文件
        self._original_stdout = sys.stdout
        self._tee = _TeeWriter(self._original_stdout, self._file)
        sys.stdout = self._tee
        return self

    def stop(self):
        """停止记录：恢复 stdout，关闭文件"""
        if self._original_stdout is not None:
            sys.stdout = self._original_stdout
            self._original_stdout = None
        if self._file is not None:
            # 写入结尾
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self._file.write(f"\n---\n\n")
            self._file.write(f"> 📅 日志结束：{now}\n")
            self._file.flush()
            self._file.close()
            self._file = None
        self._tee = None

    def __enter__(self):
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False

    # ------------------------------------------------------------------
    # 手动写入（供 GameModerator 等调用）
    # ------------------------------------------------------------------
    def write_section(self, title: str, level: int = 2):
        """写入一个 Markdown 章节标题"""
        prefix = "#" * level
        self._write_raw(f"\n{prefix} {title}\n\n")

    def write_event(self, event: str):
        """写入一条游戏事件（带时间戳 + 引用格式）"""
        ts = datetime.now().strftime("%H:%M:%S")
        self._write_raw(f"> `[{ts}]` {event}\n\n")

    def write_table(self, headers: list[str], rows: list[list[str]]):
        """写入一个 Markdown 表格"""
        header_line = "| " + " | ".join(headers) + " |"
        sep_line = "| " + " | ".join(["---"] * len(headers)) + " |"
        self._write_raw(header_line + "\n")
        self._write_raw(sep_line + "\n")
        for row in rows:
            self._write_raw("| " + " | ".join(row) + " |\n")
        self._write_raw("\n")

    def write_divider(self):
        """写入分隔线"""
        self._write_raw("\n---\n\n")

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------
    def _write_raw(self, text: str):
        """直接写入日志文件（不经过 stdout）"""
        if self._file and not self._file.closed:
            self._file.write(text)
            self._file.flush()


class _TeeWriter(io.TextIOBase):
    """同时写入两个流的 Writer，实现 stdout 的 tee 功能"""

    def __init__(self, stream_a: TextIO, stream_b: TextIO):
        super().__init__()
        self._a = stream_a  # 终端
        self._b = stream_b  # 日志文件

    def write(self, s: str) -> int:
        if s:
            self._a.write(s)
            self._a.flush()
            # 把终端输出以代码块引用的形式写入 Markdown
            # 但只对有实际内容的行做处理，空行直接写
            self._b.write(s)
            self._b.flush()
        return len(s) if s else 0

    def flush(self):
        self._a.flush()
        self._b.flush()

    @property
    def encoding(self):
        return getattr(self._a, "encoding", "utf-8")

    def fileno(self):
        return self._a.fileno()

    def isatty(self):
        return self._a.isatty()
