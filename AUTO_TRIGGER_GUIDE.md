# 自动触发系统 - 安装和使用指南

## 概述

`install_auto_trigger.py` 是 hermes-skill 的**自动触发安装系统**，它可以：

- ✅ 自动配置 EasyClaw/OpenClaw Cron 定时任务
- ✅ 检测系统环境（CLI、Cron 系统）
- ✅ 一键安装/卸载/查看状态
- ✅ 智能避免重复安装

## 使用方法

### 1. 安装自动触发

```bash
# 进入技能目录
cd ~/.easyclaw/workspace/skills/hermes-skill

# 安装自动触发
python install_auto_trigger.py install
```

**安装过程：**
1. 检测 EasyClaw/OpenClaw CLI
2. 检测 Cron 系统可用性
3. 列出已存在的 hermes-skill 任务（若有）
4. 询问是否删除旧任务
5. 安装 3 个定时任务：
   - **Nudge 提醒**: 每 1 小时
   - **上游追踪**: 每天 09:00
   - **记忆自检**: 每天 23:00

### 2. 查看状态

```bash
python install_auto_trigger.py status
```

**输出示例：**
```
📊 Hermes-Skill 自动触发状态

==================================================
CLI: easyclaw 2026.3.13

✅ 已安装 (自动触发)
安装时间: 2026-04-18 15:10:25
已安装任务: 3 个

当前运行的 Cron 任务:

• hermes-skill Nudge 提醒
  ID: 1509a5e5-d40c-4e19-8afe-3775e6994b41
  状态: ✅ 启用
  频率: 每 60 分钟

• hermes-skill 上游追踪
  ID: 300d007a-ac3a-40b4-bbdc-3acc6353381a
  状态: ✅ 启用
  频率: 0 9 * * *
  时区: Asia/Shanghai

• hermes-skill 记忆自检
  ID: 79278c94-748c-4956-b740-241aedc45b99
  状态: ✅ 启用
  频率: 0 23 * * *
  时区: Asia/Shanghai
```

### 3. 卸载自动触发

```bash
python install_auto_trigger.py uninstall
```

**卸载过程：**
1. 列出所有 hermes-skill 任务
2. 询问确认
3. 逐个删除任务
4. 删除配置文件

## 技术细节

### 定时任务配置

| 任务 | 调度类型 | 参数 | 说明 |
|------|---------|------|------|
| Nudge 提醒 | every | 3600000ms (1小时) | 检查智能提醒 |
| 上游追踪 | cron | 0 9 * * * | 每天上午 9 点检查上游 |
| 记忆自检 | cron | 0 23 * * * | 每天晚上 11 点自检 |

### 会话配置

所有任务使用 `--session isolated` 模式，确保：
- 隔离执行，不影响主会话
- 即使失败也不阻塞其他任务
- 资源独立管理

### 消息格式

任务触发时发送的 agentTurn 消息示例：

```
请检查 hermes-skill 的 Nudge 提醒。

请运行：
python ~/.easyclaw/workspace/skills/hermes-skill/scripts/evo_main.py nudge

然后告诉我有哪些提醒需要处理。
```

## 环境要求

### 必需

- ✅ EasyClaw 或 OpenClaw CLI
- ✅ EasyClaw/OpenClaw Gateway（运行中）
- ✅ Cron 系统（Gateway 内置）
- ✅ Python 3.8+

### 检测逻辑

```python
# 优先检测
1. easyclaw --version
2. openclaw --version

# Cron 检测
easyclaw cron status  # 必须成功
```

## 故障排查

### CLI 未找到

```
❌ 未找到 EasyClaw/OpenClaw CLI
```

**解决方案：**
- 安装 EasyClaw: https://easyclaw.cn/
- 安装 OpenClaw: https://openclaw.ai/
- 确保 CLI 在 PATH 中

### Cron 不可用

```
❌ Cron 系统不可用
```

**解决方案：**
- 启动 Gateway: `easyclaw gateway start`
- 检查 Gateway 状态: `easyclaw gateway status`

### 任务安装失败

```
❌ 失败: Gateway not running
```

**解决方案：**
1. 检查 Gateway 是否运行
2. 检查 Gateway 日志: `easyclaw gateway logs`
3. 重启 Gateway: `easyclaw gateway restart`

## 高级用法

### 手动触发任务

即使不使用自动触发，也可以手动运行：

```bash
# 触发 Nudge 检查
python scripts/evo_main.py nudge

# 触发上游追踪
python scripts/evo_main.py upstream check

# 触发记忆自检
python scripts/evo_main.py stats
```

### 查看任务运行历史

```bash
# 列出所有任务
easyclaw cron list

# 查看特定任务的历史
easyclaw cron runs --job-id 1509a5e5-d40c-4e19-8afe-3775e6994b41

# 手动运行任务（测试）
easyclaw cron run --job-id 1509a5e5-d40c-4e19-8afe-3775e6994b41
```

### 禁用单个任务

```bash
# 禁用某个任务
easyclaw cron disable --job-id 1509a5e5-d40c-4e19-8afe-3775e6994b41

# 启用某个任务
easyclaw cron enable --job-id 1509a5e5-d40c-4e19-8afe-3775e6994b41
```

## 安全考虑

### 权限

- 脚本只操作 hermes-skill 相关任务
- 不会影响其他 Cron 任务
- 卸载前会询问确认

### 输入验证

- 所有 CLI 参数都经过验证
- 错误输出到 stderr
- 失败时返回非零退出码

## 贡献

如果您想改进自动触发系统：

1. 修改 `install_auto_trigger.py`
2. 更新本文档
3. 遵循 PR 流程提交

## 许可证

MIT License（与 hermes-skill 主项目一致）
