# 01 — 键盘循环聚焦标签（ADR 001）

**What to build:** 用户加载图片后第一个标签自动选中，按 'h' 键可以循环遍历所有标签，配合 Delete 键纯键盘删除标签。实现纯键盘工作流：D（下一张图片）→ 自动聚焦第一个标签 → h（循环遍历）→ Delete（删除标签）。

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] 加载图片后，如果 canvas.shapes 非空，label_list 自动选中第一个标签
- [ ] 按 'h' 键循环到下一个标签，最后一个标签后回到第一个
- [ ] 无标签时按 'h' 静默忽略（不报错）
- [ ] 删除标签后焦点自动移到下一个可用标签（Qt 默认行为）
- [ ] Canvas 点击标签会同步 label_list 的选中状态
- [ ] 纯键盘工作流验证：D（下一张）→ 自动聚焦 → h（循环）→ Delete（删除）
