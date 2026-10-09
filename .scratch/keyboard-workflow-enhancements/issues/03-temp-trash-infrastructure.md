> 历史任务记录，保留当时的设计与检查项。当前实现以 [操作说明](../../../docs/current-behavior.md) 为准：I 循环标签，F/H 缩放框，O/U 删除/恢复框，Shift+O/Shift+U 删除/恢复图片，Ctrl+K 锁定显示比例。

# 03 — 临时回收站基础设施

**What to build:** 应用启动时创建临时回收站目录，清理超过 24 小时的旧回收站，为图片删除功能提供基础设施。确保跨平台兼容性（Windows/Linux/macOS）。

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] 应用启动时在系统临时目录创建 `labelImg_trash_{timestamp}/`
- [ ] 启动时扫描并删除超过 24 小时的旧 `labelImg_trash_*` 目录
- [ ] trash_dir 路径存储在 self.trash_dir 状态字段
- [ ] 如果临时目录创建失败，记录错误日志（不阻塞应用启动）
- [ ] 验证跨平台兼容性（Windows %TEMP%、Linux /tmp、macOS /tmp）
