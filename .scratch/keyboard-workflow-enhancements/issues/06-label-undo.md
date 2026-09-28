# 06 — 标签撤销功能（ADR 003 第三部分）

**What to build:** 按 'z' 键恢复当前图片最近删除的标签，切换图片时清空撤销栈，图片级别的 undo。允许用户快速撤销标签删除误操作，每张图片的撤销栈相互独立。

**Blocked by:** None — can start immediately.

**Status:** ready-for-agent

- [ ] delete_selected_shape() 中将 (shape, item.text(), item.flags()) 压入 label_deletion_stack
- [ ] 'z' 快捷键绑定到 restore_last_deleted_label() 方法
- [ ] 从 label_deletion_stack 弹出栈顶，恢复到 canvas.shapes 和 label_list
- [ ] 恢复后自动选中恢复的标签
- [ ] 栈为空时按 'z' 静默忽略
- [ ] load_file() 中调用 label_deletion_stack.clear()（切换图片时清空）
- [ ] save_file() 中调用 label_deletion_stack.clear()（保存后清空）
- [ ] delete_current_image() 中调用 label_deletion_stack.clear()（删除图片时清空）
- [ ] 验证独立性：标签撤销和图片撤销不互相影响
