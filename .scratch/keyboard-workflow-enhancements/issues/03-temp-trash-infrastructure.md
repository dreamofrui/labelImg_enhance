# 03 — 临时回收站基础设施

**What to build:** 应用启动时创建临时回收站目录，清理超过 24 小时的旧回收站，为图片删除功能提供基础设施。确保跨平台兼容性（Windows/Linux/macOS）。

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] 应用启动时在系统临时目录创建 `labelImg_trash_{timestamp}/`
- [ ] 启动时扫描并删除超过 24 小时的旧 `labelImg_trash_*` 目录
- [ ] trash_dir 路径存储在 self.trash_dir 状态字段
- [ ] 如果临时目录创建失败，记录错误日志（不阻塞应用启动）
- [ ] 验证跨平台兼容性（Windows %TEMP%、Linux /tmp、macOS /tmp）
