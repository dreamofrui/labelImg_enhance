# ADR 003: 图片删除与恢复（临时回收站模式）

> 历史设计，以下伪代码与原快捷键用于保留决策背景。当前实现以 [操作说明](../current-behavior.md) 为准：I 循环标签；O/U 删除/恢复框；Shift+O/Shift+U 删除/恢复图片。标签恢复记录在保存时清空，图片恢复记录在换目录时清空，图片与标注移动不具备事务原子性。

## Status
Proposed

## Context
当前 `delete_image()` 使用 `os.remove()` 永久删除图片，且不删除对应的标签文件。误删无法恢复，不支持撤销操作。

在数据清理场景中，用户可能需要删除低质量图片，但希望有撤销机会，避免误删重要数据。

**为什么不用项目内 .trash/ 子目录**：
- 每个图片目录都会产生 .trash/ 目录，用户需要手动清理多个位置
- 长期积累会占用大量磁盘空间
- 用户不可能回头逐个目录手动删除

**解决方案**：使用系统临时目录 + 自动清理机制，在会话期间和近期保留恢复能力，避免长期垃圾积累。

## Decision
实现两层撤销系统：**标签级撤销**（当前图片）和**图片级撤销**（跨目录）。

### 一、标签删除与恢复

#### 删除行为（按 Delete/Backspace）
当前已有功能：`delete_selected_shape()` 永久删除选中的标签。

#### 恢复行为（按键 'z' + 工具栏按钮）
1. **维护标签删除栈**（当前图片范围）：
   ```python
   self.label_deletion_stack = []  # [(shape, item), ...]
   ```
   - 每次删除标签时，将 shape 对象和对应的 QListWidgetItem 压栈
   - 按 'z' 时弹出并恢复到 canvas 和 label_list

2. **作用域**：
   - 仅当前图片有效
   - **切换图片时清空** `label_deletion_stack`
   - **删除当前图片时清空** `label_deletion_stack`（删除图片 = 丢弃该图片的所有状态）
   - 保存文件后，**不清空**栈（标签删除是纯内存操作，与文件无关）

3. **恢复逻辑**：
   ```python
   def restore_last_deleted_label(self):
       if not self.label_deletion_stack:
           return  # 静默忽略
       shape, item = self.label_deletion_stack.pop()
       self.canvas.shapes.append(shape)
       self.add_label(shape)  # 重新添加到 label_list
       self.set_dirty()
   ```

### 二、图片删除与恢复

#### Trash 目录位置
**系统临时目录 + 会话隔离**：
- Trash 目录路径：`%TEMP%/labelImg_trash_{timestamp}/`（Windows）或 `/tmp/labelImg_trash_{timestamp}/`（Linux/Mac）
- `{timestamp}` 为应用启动时间戳（如 `20260928_143022`），确保多个 labelImg 实例互不干扰
- 应用启动时自动清理超过 **24 小时**的旧 trash 目录

**为什么选择这个方案**：
- 无需用户手动清理，系统会定期清理临时目录
- 避免污染项目目录（不产生 .trash/ 子目录）
- 保留短期恢复能力（24 小时内可恢复）
- 跨目录操作不需要维护多个 trash 位置

#### 删除行为（按键 'o' + 文件列表右键菜单）
1. **移动到临时回收站目录**（无确认对话框）：
   ```
   图片：/data/images/img001.jpg  →  %TEMP%/labelImg_trash_20260928_143022/img001.jpg
   标签：/data/images/img001.xml  →  %TEMP%/labelImg_trash_20260928_143022/img001.xml
   ```
   - 临时 trash 目录在应用启动时创建
   - 同时移动图片和对应的标签文件（XML/TXT/JSON，根据当前格式）
   - 同名文件冲突时**覆盖旧文件**（新删除覆盖旧删除，用户只关心最近一次）
   - **直接删除，不弹出确认对话框**（因为可以用 'u' 恢复）

2. **维护删除栈**（内存中）：
   ```python
   self.image_deletion_stack = []  # [(trash_img_path, trash_label_path, original_dir), ...]
   ```
   - 记录删除顺序，用于撤销
   - 存储完整路径（trash 中的路径 + 原目录路径）
   - **跨目录有效**：切换到其他目录后仍可恢复之前删除的图片

3. **清空标签撤销栈**：
   - 删除图片时清空 `label_deletion_stack`
   - 恢复图片后从空栈开始，不恢复旧的撤销记录

4. **删除后导航**：
   - 从 `self.m_img_list` 中移除已删除图片
   - **自动加载下一张图片**：
     - 如果删除的不是最后一张 → 加载下一张（索引保持不变，因为列表变短）
     - 如果删除的是倒数第二张以前 → 加载上一张（索引 -1）
     - 如果删除的是最后一张（列表变空）→ 显示空白界面，提示"No images"，可按 'u' 恢复

#### 恢复行为（按键 'u' + 文件列表右键菜单）
1. **栈式撤销**（LIFO）：
   ```
   按 'u' → 从 image_deletion_stack 弹出最后一个删除操作
   → 将文件从临时 trash 移回原目录
   → 插入到当前图片位置（不是原始位置）
   → 加载恢复的图片
   ```

2. **插入位置逻辑**（关键变更）：
   - **不恢复到原始索引**，而是插入到当前索引位置
   - 恢复的图片插入到当前索引，原本的图片被挤到下一个索引
   - 恢复后立即显示恢复的图片（用户可以确认是否恢复正确）
   
   **场景示例**：
   ```
   初始列表：[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
   
   用户删除图3：
     m_img_list = [1, 2, 4, 5, 6, 7, 8, 9, 10]
     image_deletion_stack = [(图3_trash_path, 图3_label_trash_path, 原目录)]
   
   用户浏览到图10（此时在列表索引8）：
     cur_img_idx = 8
   
   用户按 'u' 恢复图3：
     图3插入到索引8 → m_img_list = [1, 2, 4, 5, 6, 7, 8, 9, 图3, 10]
                                                      ↑
                                                  cur_idx=8
     当前显示：图3
     下次按 D → 显示图10（索引9）
   ```

3. **多次恢复行为**：
   - 每次恢复都插入到**当前位置**
   - LIFO 顺序：最后删除的最先恢复

### 三、两个撤销系统的交互

| 操作 | 按键 | 作用域 | 栈清空时机 |
|------|------|--------|-----------|
| 删除标签 | Delete/Backspace | 当前图片 | 切换图片时 / 删除图片时 |
| 恢复标签 | 'z' | 当前图片 | 切换图片时 / 删除图片时 |
| 删除图片 | 'o' | 跨目录 | 应用关闭时 |
| 恢复图片 | 'u' | 跨目录 | 应用关闭时 |

**关键设计点**：
- 删除图片时，**清空** `label_deletion_stack`（该图片状态被丢弃）
- 恢复图片后加载该图片，此时 `label_deletion_stack` 为空（全新加载）
- 标签删除是内存操作（修改 canvas.shapes），图片删除是文件操作（移动磁盘文件）

### 生命周期与作用域
- **标签删除栈**（`label_deletion_stack`）：
  - 切换图片时清空
  - 删除当前图片时清空
  - 不持久化，关闭程序后清空
  - 不受保存文件影响（标签删除后保存，栈仍保留，可继续撤销）

- **图片删除栈**（`image_deletion_stack`）：
  - 跨目录有效（不会因为切换目录而清空）
  - 不持久化，关闭程序后清空
  - 临时 trash 目录保留在系统临时目录中，24 小时后自动清理

### 边界情况
#### 标签删除与恢复
- **恢复栈为空时按 'z'**：静默忽略
- **恢复标签时的聚焦**：恢复的标签自动成为当前选中项
- **保存文件后恢复**：保存文件时清空 `label_deletion_stack`，确保已保存的删除操作不可撤销
  - 自动保存触发：切换图片时，如果 `auto_saving.isChecked()` 且 `dirty=True`
  - 手动保存触发：用户按 Ctrl+S
  - 清空时机：`save_file()` 方法末尾调用 `label_deletion_stack.clear()`
- **删除最后一个标签后焦点**：Qt 默认清空选中状态（`currentRow() = -1`），canvas 上无高亮

#### 图片删除与恢复
- **删除栈为空时按 'u'**：静默忽略
- **标签文件不存在**：只删除/恢复图片文件（`label_trash_path = None`）
- **同名文件冲突**：trash 中已有同名文件 → 覆盖旧文件（新删除覆盖旧删除）
- **恢复时原目录有同名文件**：覆盖（用户期望恢复的文件替换当前文件）
- **临时目录创建失败**：显示错误，禁用删除功能（不回退到永久删除）
- **删除最后一张图片**：显示空白界面，提示"No images"，可按 'u' 恢复
- **应用崩溃**：trash 目录保留在系统临时目录中，下次启动时 24 小时后自动清理

## Implementation Notes

### State Management
```python
# 标签删除栈（当前图片级别）
self.label_deletion_stack = []  # [(shape, item_text, item_flags), ...]

# 图片删除栈（跨目录级别）
self.image_deletion_stack = []  # [(trash_img_path, trash_label_path, original_dir), ...]
self.trash_dir = None            # 应用启动时创建的临时 trash 目录路径
                                 # 格式：%TEMP%/labelImg_trash_{timestamp}/
```

### 关键方法

#### 0. 应用启动时初始化 trash 目录并清理旧目录
```python
def __init__(self):
    # ... 原有初始化逻辑 ...
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    temp_dir = tempfile.gettempdir()
    self.trash_dir = os.path.join(temp_dir, f'labelImg_trash_{timestamp}')
    os.makedirs(self.trash_dir, exist_ok=True)
    
    # 清理超过 24 小时的旧 trash 目录
    self.cleanup_old_trash_dirs(temp_dir)

def cleanup_old_trash_dirs(self, temp_dir):
    cutoff_time = time.time() - 24 * 3600  # 24 小时前
    pattern = os.path.join(temp_dir, 'labelImg_trash_*')
    for trash_path in glob.glob(pattern):
        if os.path.isdir(trash_path) and os.path.getmtime(trash_path) < cutoff_time:
            shutil.rmtree(trash_path, ignore_errors=True)
```

#### 1. 标签撤销系统
```python
def delete_selected_shape(self):
    """删除选中的标签（修改现有方法）"""
    shape = self.canvas.selected_shape
    item = self.shapes_to_items[shape]
    
    # 保存到撤销栈
    self.label_deletion_stack.append((shape, item.text(), item.flags()))
    
    # 执行删除
    self.remove_label(self.canvas.delete_selected())
    self.set_dirty()

def restore_last_deleted_label(self):
    """恢复最后删除的标签（按键 'z'）"""
    if not self.label_deletion_stack:
        return
    
    shape, text, flags = self.label_deletion_stack.pop()
    self.canvas.shapes.append(shape)
    self.add_label(shape)
    self.canvas.select_shape(shape)  # 自动选中恢复的标签
    self.set_dirty()

def clear_label_deletion_history(self):
    """切换图片或删除图片时清空标签删除历史"""
    self.label_deletion_stack.clear()
```

#### 2. 删除当前图片（'o' 键）
```python
def delete_current_image(self):
    if not self.image_list:
        return
    
    current_path = self.image_list[self.cur_img_idx]
    label_path = self.get_label_path(current_path)
    original_dir = os.path.dirname(current_path)
    
    # 移动文件到临时 trash 目录（同名覆盖）
    trash_img_path = os.path.join(self.trash_dir, os.path.basename(current_path))
    shutil.move(current_path, trash_img_path)
    
    trash_label_path = None
    if os.path.exists(label_path):
        trash_label_path = os.path.join(self.trash_dir, os.path.basename(label_path))
        shutil.move(label_path, trash_label_path)
    
    # 清空该图片的标签撤销栈
    self.label_deletion_stack.clear()
    
    # 记录到图片撤销栈
    self.image_deletion_stack.append((trash_img_path, trash_label_path, original_dir))
    
    # 从列表中移除
    self.image_list.pop(self.cur_img_idx)
    
    # 加载下一张或上一张
    if self.image_list:
        if self.cur_img_idx >= len(self.image_list):
            self.cur_img_idx = len(self.image_list) - 1
        self.load_file(self.image_list[self.cur_img_idx])
    else:
        self.clear_canvas()  # 显示空白界面，提示 "No images"
```

#### 3. 恢复上一张删除的图片（'u' 键）
```python
def restore_last_deleted_image(self):
    """恢复最后删除的图片（按键 'u'）- 插入到当前位置"""
    if not self.image_deletion_stack:
        return
    
    trash_img_path, trash_label_path, original_dir = self.image_deletion_stack.pop()
    
    # 移回原目录
    original_img_path = os.path.join(original_dir, os.path.basename(trash_img_path))
    shutil.move(trash_img_path, original_img_path)
    
    if trash_label_path and os.path.exists(trash_label_path):
        original_label_path = os.path.join(original_dir, os.path.basename(trash_label_path))
        shutil.move(trash_label_path, original_label_path)
    
    # 插入到当前索引位置
    if not self.image_list:
        # 列表为空，重新扫描目录
        self.import_dir_images(original_dir)
        self.cur_img_idx = 0
    else:
        # 插入到当前位置，原图片被挤到下一个
        insert_pos = self.cur_img_idx
        self.image_list.insert(insert_pos, original_img_path)
        self.cur_img_idx = insert_pos
    
    # 加载恢复的图片（立即显示，用户确认恢复正确）
    self.load_file(original_img_path)
```

### 调用点
- `load_file()` → 调用 `clear_label_deletion_history()`（切换图片时）
- `delete_current_image()` → 调用 `label_deletion_stack.clear()`（删除图片时）
- `save_file()` → 调用 `label_deletion_stack.clear()`（保存后清空标签删除历史）
- `keyPressEvent()` → 检测 'o'、'u'、'z' 按键
- **文件列表右键菜单**：
  - 删除图片（'o'，图标：垃圾桶）
  - 恢复图片（'u'，图标：撤销箭头）

## Consequences

### Positive
- ✅ 双层撤销系统，分别适应不同工作流
- ✅ 标签撤销：快速修正标注错误，无需重新标注
- ✅ 图片撤销：安全删除低质量图片，可恢复误删
- ✅ 同时处理图片和标签文件（原子操作）
- ✅ 简单的栈式撤销，无需复杂UI
- ✅ 'z' 键符合通用撤销习惯（Ctrl+Z）
- ✅ 系统临时目录 + 自动清理，无需用户手动维护

### Negative
- ⚠️ 两个独立的撤销系统，用户需要理解 'z'（标签）vs 'u'（图片）的区别
- ⚠️ 标签恢复需要保存完整的 shape 对象，内存占用略增
- ⚠️ 移动文件比直接删除慢（但对单个文件影响不大）
- ⚠️ 临时目录清理依赖应用启动，长时间不使用 labelImg 会累积垃圾（但系统临时目录本身也会定期清理）
