#!/usr/bin/env python3
"""
自进化系统统一入口 v1.2
Usage: python evo_main.py <command>

Commands:
  nudge [type]          - 检查/触发 nudge
  remember <text>       - 添加记忆
  forget <text>         - 删除记忆
  recall <query>        - 搜索记忆 (alias: search)
  stats                 - 显示记忆统计
  skills                - 列出自动创建的 skills
  eval <skill,rating>   - 评估 skill
  improve <skill,notes>  - 改进 skill
  upstream <cmd>         - 上游追踪 (check|status|diff|list|fuse)
  check                  - 运行完整自检

Examples:
  python evo_main.py remember "重要知识"
  python evo_main.py recall "关键词"
  python evo_main.py search "关键词"    # alias for recall
  python evo_main.py upstream check
"""

import sys
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
UPSTREAM_SCRIPT = SCRIPT_DIR / "upstream_tracker.py"


def get_python_cmd():
    """跨平台 Python 命令检测"""
    # 优先使用 sys.executable，确保与当前运行环境一致
    return sys.executable


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print(__doc__)
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]
    python_cmd = get_python_cmd()

    # 支持 search 作为 recall 的别名
    if cmd == "search":
        cmd = "recall"

    if cmd == "upstream":
        sub = args[0] if args else "status"
        try:
            result = subprocess.run(
                [python_cmd, str(UPSTREAM_SCRIPT), sub] + args[1:],
                capture_output=True, text=True, timeout=120
            )
            print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
        except subprocess.TimeoutExpired:
            print("❌ 上游追踪超时（120s），可能是网络问题或 GitHub API 限流", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"❌ 上游追踪失败：{e}", file=sys.stderr)
            sys.exit(1)
        return

    valid_commands = ["nudge", "remember", "forget", "recall", "stats", "skills", "eval", "improve", "check"]
    if cmd not in valid_commands:
        print(f"❌ 未知命令：{cmd}")
        print(f"可用命令：{', '.join(valid_commands)}")
        print("\n使用 'search' 作为 'recall' 的别名")
        return

    try:
        if cmd == "nudge":
            if args:
                result = subprocess.run(
                    [python_cmd, str(SCRIPT_DIR / "nudge_system.py"), "--trigger", args[0]],
                    capture_output=True, text=True
                )
            else:
                result = subprocess.run(
                    [python_cmd, str(SCRIPT_DIR / "nudge_system.py"), "--check"],
                    capture_output=True, text=True
                )
        elif cmd in ["remember", "forget", "recall"]:
            result = subprocess.run(
                [python_cmd, str(SCRIPT_DIR / "memory_tool.py"), cmd] + args,
                capture_output=True, text=True
            )
        elif cmd == "stats":
            result = subprocess.run(
                [python_cmd, str(SCRIPT_DIR / "memory_tool.py"), "stats"],
                capture_output=True, text=True
            )
        elif cmd == "skills":
            result = subprocess.run(
                [python_cmd, str(SCRIPT_DIR / "auto_skill_creator.py"), "--list"],
                capture_output=True, text=True
            )
        elif cmd in ["eval", "improve"]:
            if not args:
                print(f"❌ {cmd} 命令需要参数", file=sys.stderr)
                print(f"用法：python evo_main.py {cmd} <参数>")
                sys.exit(1)
            result = subprocess.run(
                [python_cmd, str(SCRIPT_DIR / "skill_evaluator.py"), f"--{cmd}", args[0]],
                capture_output=True, text=True
            )
        elif cmd == "check":
            result = subprocess.run(
                ["bash", str(SCRIPT_DIR / "self_check_cron.sh")],
                capture_output=True, text=True
            )
        else:
            print(f"❌ 未实现命令：{cmd}", file=sys.stderr)
            sys.exit(1)

        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        if result.returncode != 0:
            sys.exit(result.returncode)

    except FileNotFoundError as e:
        print(f"❌ 脚本文件未找到：{e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行失败：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()