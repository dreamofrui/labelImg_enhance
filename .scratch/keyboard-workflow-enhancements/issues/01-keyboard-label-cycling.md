> 历史任务记录，保留当时的设计与检查项。当前实现以 [操作说明](../../../docs/current-behavior.md) 为准：I 循环标签，F/H 缩放框，O/U 删除/恢复框，Shift+O/Shift+U 删除/恢复图片，Ctrl+K 锁定显示比例。

# 01 — 键盘循环聚焦标签（ADR 001）

**What to build:** 用户加载图片后最后一个标签自动选中（保持默认），按 'h' 键可以向上循环遍历所有标签（从后往前），配合 Delete 键纯键盘删除标签。实现纯键盘工作流：D（下一张图片）→ 自动聚焦最后标签 → h（向上循环）→ Delete（删除标签）。

**Blocked by:** None — can start immediately.

**Status:** ✅ Implemented

- [x] 加载图片后，如果 label_list 有标签，自动选中最后一个标签（保持 Qt 默认行为）
- [x] 按 'h' 键循环到前一个标签（向上），第一个标签后回到最后一个
- [x] 无标签时按 'h' 静默忽略（不报错）
- [x] 删除标签后焦点自动移到下一个可用标签（Qt 默认行为）
- [x] Canvas 点击标签会同步 label_list 的选中状态（已有功能）
- [x] 纯键盘工作流验证：D（下一张）→ 自动聚焦最后标签 → h（向上循环）→ Delete（删除）

## Implementation Details

实现文件：`labelImg.py`

### 新增方法
- `cycle_prev_label()`: 循环到前一个标签的核心逻辑
  - 处理边界：索引 <= 0 时跳转到最后一个
  - 无标签时静默返回
  - 调用 `setCurrentRow()` 触发 UI 更新

### 键盘事件处理
- `keyPressEvent()`: 添加 `Qt.Key_H` 处理
  - 按 'h' 键调用 `cycle_prev_label()`
  - 保持与其他键盘快捷键一致的代码风格

### 自动聚焦
- 保持原有的 `load_file()` 行为：图片加载后自动选中最后一个标签
- 无需修改，Qt 默认行为已满足需求
