# 05 — 图片恢复功能（ADR 003 第二部分）

**What to build:** 按 'u' 键恢复最近删除的图片，插入到当前位置，LIFO 顺序，支持跨目录恢复。允许用户撤销误删操作，恢复的图片立即显示。

**Blocked by:** 04-delete-image-to-trash

**Status:** ready-for-agent

- [ ] 'u' 快捷键绑定到 restore_last_deleted_image() 方法
- [ ] 从 image_deletion_stack 弹出最近删除的记录
- [ ] 移动图片和标签文件回原始目录
- [ ] 原位置同名文件存在时覆盖（用户期望恢复的文件替换当前文件）
- [ ] 插入到 m_img_list 当前索引位置，同步更新 file_list_widget
- [ ] 立即加载恢复的图片
- [ ] 恢复图片触发自动聚焦（如果已实现键盘循环功能）
- [ ] 栈为空时按 'u' 静默忽略
- [ ] 跨目录恢复验证：目录 A 删除图片 → 切换到目录 B → 按 'u' → 恢复到目录 A
- [ ] 文件列表右键菜单添加"恢复图片"项
