#!/usr/bin/env python3
"""
Hermes-Skill 自动触发安装系统
自动配置 EasyClaw/OpenClaw Cron 定时任务
"""

import sys
import json
import subprocess
from pathlib import Path

# 路径配置
THIS_DIR = Path(__file__).parent
SCRIPT_DIR = THIS_DIR / "scripts"
PARENT_DIR = THIS_DIR.parent
WORKSPACE_DIR = PARENT_DIR  # ~/.easyclaw/workspace
CONFIG_FILE = THIS_DIR / "auto_trigger_config.json"

# 任务定义
JOBS = [
    {
        "name": "hermes-skill Nudge 提醒",
        "schedule": {"kind": "every", "everyMs": 3600000},  # 每 1 小时
        "message": "请检查 hermes-skill 的 Nudge 提醒。\n\n请运行：\npython ~/.easyclaw/workspace/skills/hermes-skill/scripts/evo_main.py nudge\n\n然后告诉我有哪些提醒需要处理。",
        "description": "每小时检查 Nudge 智能提醒"
    },
    {
        "name": "hermes-skill 上游追踪",
        "schedule": {"kind": "cron", "expr": "0 9 * * *", "tz": "Asia/Shanghai"},  # 每天 09:00
        "message": "执行 hermes-skill 上游追踪检查\n\n请运行：\npython ~/.easyclaw/workspace/skills/hermes-skill/scripts/evo_main.py upstream check\n\n然后告诉我有哪些高价值的融合机会。",
        "description": "每天 09:00 检查 Hermes Agent 上游更新"
    },
    {
        "name": "hermes-skill 记忆自检",
        "schedule": {"kind": "cron", "expr": "0 23 * * *", "tz": "Asia/Shanghai"},  # 每天 23:00
        "message": "执行 hermes-skill 记忆自检\n\n请运行：\npython ~/.easyclaw/workspace/skills/hermes-skill/scripts/evo_main.py stats\npython ~/.easyclaw/workspace/skills/hermes-skill/scripts/evo_main.py nudge\n\n然后告诉我记忆库的状态和建议的清理操作。",
        "description": "每天 23:00 记忆库自检和清理建议"
    }
]


def check_cli_available():
    """检查 easyclaw/openclaw CLI 是否可用"""
    import shutil
    
    for cmd in ["easyclaw", "openclaw"]:
        # 检查命令是否存在
        if not shutil.which(cmd):
            continue
        
        try:
            # 尝试不同的命令来检测
            for test_cmd in ["--version", "version", "--help", "help"]:
                result = subprocess.run(
                    [cmd, test_cmd],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    shell=True  # Windows 可能需要 shell
                )
                if result.returncode == 0:
                    # 提取版本号（如果可能）
                    version = result.stdout.strip() or "installed"
                    return cmd, version
        except FileNotFoundError:
            continue
        except Exception as e:
            # 继续尝试下一个命令
            continue
    return None, None


def check_cron_available(cli_cmd):
    """检查 Cron 系统是否可用"""
    try:
        result = subprocess.run(
            [cli_cmd, "cron", "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def list_cron_jobs(cli_cmd):
    """列出现有的 Cron 任务"""
    try:
        result = subprocess.run(
            [cli_cmd, "cron", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
            shell=True  # Windows 需要
        )
        if result.returncode == 0:
            # 尝试从输出中提取 JSON
            # EasyClaw 可能输出其他内容，需要找到 JSON 部分
            output = result.stdout.strip()
            
            # 尝试解析整个输出
            try:
                data = json.loads(output)
                return data.get("jobs", [])
            except json.JSONDecodeError:
                # 尝试提取 JSON 部分（查找 { 或 [）
                for start_char in ['{', '[']:
                    if start_char in output:
                        start_idx = output.index(start_char)
                        # 找到匹配的结束位置
                        if start_char == '{':
                            end_idx = output.rfind('}')
                            if end_idx > start_idx:
                                json_str = output[start_idx:end_idx + 1]
                        elif start_char == '[':
                            end_idx = output.rfind(']')
                            if end_idx > start_idx:
                                json_str = output[start_idx:end_idx + 1]
                        try:
                            data = json.loads(json_str)
                            return data.get("jobs", [])
                        except json.JSONDecodeError:
                            pass
                
                # 如果都失败，尝试按行查找 JSON
                for line in output.split('\n'):
                    line = line.strip()
                    if line.startswith('{') or line.startswith('['):
                        try:
                            data = json.loads(line)
                            return data.get("jobs", [])
                        except json.JSONDecodeError:
                            pass
                
                print(f"⚠️ 无法解析 JSON 输出", file=sys.stderr)
                print(f"原始输出（前 200 字符）：{output[:200]}", file=sys.stderr)
        else:
            print(f"⚠️ Cron list 返回错误: {result.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ 无法列出 Cron 任务: {e}", file=sys.stderr)
    return []


def install_job(cli_cmd, job):
    """安装单个 Cron 任务"""
    try:
        # 构建 cron add 命令
        cmd_parts = [cli_cmd, "cron", "add", "--name", job["name"]]
        
        # 添加调度
        if "every" in job["schedule"]:
            duration_ms = job["schedule"]["everyMs"]
            cmd_parts.extend(["--every", f"{duration_ms}ms"])
        elif "expr" in job["schedule"]:
            cmd_parts.extend(["--cron", job["schedule"]["expr"]])
            if "tz" in job["schedule"]:
                cmd
        
        # 添加会话目标和消息
        cmd_parts.extend([
            "--session", "isolated",
            "--message", job["message"]
        ])
        
        # 执行
        result = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return True, json.loads(result.stdout)
        else:
            return False, result.stderr
            
    except Exception as e:
        return False, str(e)


def remove_job_by_name(cli_cmd, name):
    """根据名称删除 Cron 任务"""
    jobs = list_cron_jobs(cli_cmd)
    for job in jobs:
        if job.get("name") == name:
            job_id = job.get("id")
            try:
                result = subprocess.run(
                    [cli_cmd, "cron", "rm", "--job-id", job_id],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print(f"✅ 已删除任务: {name}")
                    return True
            except Exception as e:
                print(f"⚠️ 删除任务失败: {name} - {e}", file=sys.stderr)
    return False


def install_all():
    """安装所有自动触发任务"""
    print("🚀 Hermes-Skill 自动触发安装系统\n")
    print("=" * 50)
    
    # 检查 CLI
    cli_cmd, version = check_cli_available()
    if not cli_cmd:
        print("❌ 未找到 EasyClaw/OpenClaw CLI", file=sys.stderr)
        print("请确保已安装: https://easyclaw.cn/ 或 https://openclaw.ai/", file=sys.stderr)
        sys.exit(1)
    
    print(f"✅ 找到 CLI: {cli_cmd} {version}")
    
    # 检查 Cron
    if not check_cron_available(cli_cmd):
        print("❌ Cron 系统不可用", file=sys.stderr)
        print("请确保 Gateway 正在运行", file=sys.stderr)
        sys.exit(1)
    
    print("✅ Cron 系统可用")
    print()
    
    # 列出现有任务
    existing_jobs = list_cron_jobs(cli_cmd)
    hermes_jobs = [j for j in existing_jobs if j.get("name", "").startswith("hermes-skill")]
    
    if hermes_jobs:
        print(f"⚠️ 发现 {len(hermes_jobs)} 个已存在的 hermes-skill 任务:")
        for job in hermes_jobs:
            print(f"   - {job.get('name')} (ID: {job.get('id')[:8]}...)")
        print()
        response = input("是否先删除这些任务？(y/N): ").strip().lower()
        if response == 'y':
            for job in hermes_jobs:
                remove_job_by_name(cli_cmd, job["name"])
            print()
    
    # 安装新任务
    print("开始安装定时任务...\n")
    
    installed = []
    failed = []
    
    for job in JOBS:
        print(f"📦 安装: {job['name']}")
        print(f"   {job['description']}")
        
        success, result = install_job(cli_cmd, job)
        
        if success:
            job_id = result.get("id", "unknown")
            print(f"   ✅ 成功 (ID: {job_id[:8]}...)")
            installed.append({
                "name": job["name"],
                "id": job_id,
                "schedule": job["schedule"]
            })
        else:
            print(f"   ❌ 失败: {result}")
            failed.append(job["name"])
        
        print()
    
    # 保存配置
    config = {
        "cli": cli_cmd,
        "version": version,
        "installed_jobs": installed,
        "failed_jobs": failed,
        "installed_at": subprocess.check_output(["date", "+%Y-%m-%d %H:%M:%S"], text=True).strip()
    }
    
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    # 总结
    print("=" * 50)
    print("📊 安装总结:")
    print(f"   ✅ 成功: {len(installed)} 个")
    print(f"   ❌ 失败: {len(failed)} 个")
    print()
    
    if installed:
        print("已安装的任务:")
        for job in installed:
            print(f"   • {job['name']}")
            if "every" in job["schedule"]:
                print(f"     频率: 每 {job['schedule']['everyMs'] / 1000 / 60:.0f} 分钟")
            elif "expr" in job["schedule"]:
                print(f"     频率: Cron 表达式 '{job['schedule']['expr']}'")
        print()
    
    if failed:
        print("失败的任务:")
        for name in failed:
            print(f"   • {name}")
        print()
    
    print(f"✅ 配置已保存到: {CONFIG_FILE}")
    print()
    print("🎉 安装完成！现在 hermes-skill 会自动运行。")


def uninstall_all():
    """卸载所有自动触发任务"""
    print("🗑️ Hermes-Skill 自动触发卸载\n")
    print("=" * 50)
    
    # 检查 CLI
    cli_cmd, _ = check_cli_available()
    if not cli_cmd:
        print("❌ 未找到 CLI", file=sys.stderr)
        sys.exit(1)
    
    # 列出任务
    jobs = list_cron_jobs(cli_cmd)
    hermes_jobs = [j for j in jobs if j.get("name", "").startswith("hermes-skill")]
    
    if not hermes_jobs:
        print("✅ 没有找到 hermes-skill 任务")
        return
    
    print(f"找到 {len(hermes_jobs)} 个 hermes-skill 任务:")
    print()
    
    for job in hermes_jobs:
        print(f"• {job.get('name')} (ID: {job.get('id')[:8]}...)")
    
    print()
    response = input("确定要删除这些任务吗？(y/N): ").strip().lower()
    
    if response == 'y':
        for job in hermes_jobs:
            remove_job_by_name(cli_cmd, job["name"])
        
        # 删除配置文件
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
            print(f"\n✅ 配置文件已删除")
        
        print("\n🎉 卸载完成！")


def status():
    """显示当前状态"""
    print("📊 Hermes-Skill 自动触发状态\n")
    print("=" * 50)
    
    # 检查 CLI
    cli_cmd, version = check_cli_available()
    if not cli_cmd:
        print("❌ CLI 未安装")
        return
    
    print(f"CLI: {cli_cmd} {version}")
    print()
    
    # 检查配置文件
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            config = json.load(f)
        print("✅ 已安装 (自动触发)")
        print(f"安装时间: {config.get('installed_at', 'unknown')}")
        print(f"已安装任务: {len(config.get('installed_jobs', []))} 个")
        print()
    else:
        print("⚠️ 未安装 (自动触发)")
        print()
    
    # 列出当前任务
    jobs = list_cron_jobs(cli_cmd)
    hermes_jobs = [j for j in jobs if j.get("name", "").startswith("hermes-skill")]
    
    if hermes_jobs:
        print("当前运行的 Cron 任务:")
        print()
        for job in hermes_jobs:
            print(f"• {job.get('name')}")
            print(f"  ID: {job.get('id')}")
            print(f"  状态: {'✅ 启用' if job.get('enabled') else '❌ 禁用'}")
            
            schedule = job.get("schedule", {})
            if "every" in schedule:
                print(f"  频率: 每 {schedule['everyMs'] / 1000 / 60:.0f} 分钟")
            elif "expr" in schedule:
                print(f"  频率: {schedule['expr']}")
                if "tz" in schedule:
                    print(f"  时区: {schedule['tz']}")
            print()
    else:
        print("当前没有运行的 Cron 任务")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Hermes-Skill 自动触发安装系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python install_auto_trigger.py install    # 安装自动触发
  python install_auto_trigger.py uninstall  # 卸载自动触发
  python install_auto_trigger.py status     # 查看状态
        """
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="status",
        choices=["install", "uninstall", "status"],
        help="安装、卸载或查看状态"
    )
    
    args = parser.parse_args()
    
    if args.action == "install":
        install_all()
    elif args.action == "uninstall":
        uninstall_all()
    elif args.action == "status":
        status()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
