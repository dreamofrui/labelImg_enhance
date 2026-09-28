# ADR 001: 键盘循环聚焦标签

## Status
Proposed

## Context
当前删除标签的工作流需要频繁使用鼠标：
1. 鼠标点击 label_list 中的 item 来选中标签
2. 按 Delete 键删除
3. 重复上述过程

在数据清理场景中，一张图可能有多个标签需要审查和删除，频繁的鼠标操作效率低。

## Decision

### 自动聚焦机制
**图片加载后自动选中第一个标签**：
- `load_file()` 完成图片和标签加载后，如果 `self.canvas.shapes` 非空，自动调用 `self.label_list.setCurrentRow(0)`
- 用户打开图片时，第一个标签立即处于选中状态（label_list 高亮 + canvas 高亮）
- 配合 'h' 键循环，用户无需额外按键即可开始遍历标签

### 'h' 键循环行为
添加键盘快捷键 'h' 实现循环选中下一个标签：

**核心逻辑**：
```python
def cycle_next_label(self):
    if not self.canvas.shapes:
        return  # 无标签时静默忽略
    
    current_index = self.label_list.currentRow()  # -1 表示无选中
    next_index = (current_index + 1) % len(self.canvas.shapes)
    
    self.label_list.setCurrentRow(next_index)  # 触发 label_selection_changed
```

**行为特性**：
- 当前有选中标签 → 移到下一个
- 到达列表末尾 → 循环回第一个
- 无标签时 → 静默忽略（因为有自动聚焦，这种情况极少出现）
- 删除标签后 → label_list 自动调整选中到下一个可用索引

### 用户工作流
**典型场景**：快速审查并删除错误标签
```
1. 用户按 D 切换到下一张图片
2. 自动聚焦第一个标签（无需按键）
3. 用户查看 canvas 上高亮的标签
4. 标签正确 → 按 'h' 查看下一个
5. 标签错误 → 按 Delete/Backspace 删除
6. 继续按 'h' 遍历剩余标签
7. 审查完毕 → 按 D 到下一张（自动保存当前图片）
```

**纯键盘操作**：
- D/A：切换图片
- h：循环标签
- Delete/Backspace：删除当前标签
- z：恢复删除的标签（ADR 003）

## Consequences

### Positive
- 纯键盘操作，无需鼠标
- 适合批量审查/删除标签的工作流
- 'h' 键语义：hjkl vim风格导航，h=左/上一个

### Negative
- 需要维护 label_list 的当前索引状态
- 删除标签后需要智能调整焦点位置
