# 02 — 锁定缩放比例（ADR 002）

**What to build:** 工具栏 Toggle 按钮锁定当前缩放比例，切换图片时保持固定缩放，手动调整会更新锁定值，点击 FIT_WINDOW/FIT_WIDTH 自动解锁。用户可以在标注一批相同尺寸的图片时保持一致的缩放级别。

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] 工具栏添加"锁定缩放"Toggle 按钮（图标：🔓/🔒）
- [ ] 点击按钮时记录当前 zoom_widget.value() 为 locked_zoom_value
- [ ] 锁定状态下加载图片时应用 locked_zoom_value，跳过 adjust_scale()
- [ ] 锁定状态下手动缩放（滚轮、Ctrl++/-、zoom_widget 输入）会更新 locked_zoom_value
- [ ] 点击 FIT_WINDOW/FIT_WIDTH 按钮或按 Ctrl+F/Ctrl+Shift+F 时自动解锁
- [ ] 按钮图标/颜色反映锁定状态
- [ ] 锁定状态不持久化（关闭应用后重置）
