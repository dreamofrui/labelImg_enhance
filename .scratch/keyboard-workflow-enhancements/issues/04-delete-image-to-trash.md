> 历史任务记录，保留当时的设计与检查项。当前实现以 [操作说明](../../../docs/current-behavior.md) 为准：I 循环标签，F/H 缩放框，O/U 删除/恢复框，Shift+O/Shift+U 删除/恢复图片，Ctrl+K 锁定显示比例。

# 04 — 图片删除到回收站（ADR 003 第一部分）

**What to build:** 按 'o' 键将当前图片和标签文件移动到临时回收站，无确认对话框，自动加载下一张图片。支持快速清理低质量数据的工作流。

**Blocked by:** 03-temp-trash-infrastructure

**Status:** ready-for-agent

- [ ] 'o' 快捷键绑定到 delete_current_image() 方法
- [ ] 移动图片和标签文件（如果存在）到 trash_dir
- [ ] 同名文件冲突时覆盖旧文件
- [ ] 删除记录压入 image_deletion_stack: (trash_img_path, trash_label_path, original_dir)
- [ ] 从 m_img_list 移除图片，同步更新 file_list_widget
- [ ] 删除后加载下一张图片（最后一张则加载上一张，列表空则显示空白）
- [ ] 删除当前图片时清空 label_deletion_stack（如果已实现标签撤销）
- [ ] 文件列表右键菜单添加"删除到回收站"项
