# KeyError Crash Fix - Shape Reference Inconsistency

**Date**: 2026-10-08  
**Issue**: Production crash when resizing bounding boxes during image switching  
**Severity**: Critical (Application crash with data loss risk)  
**Status**: ✅ Fixed

---

## 问题描述

### 崩溃现象
生产环境中，用户在调整标注框大小时快速切换图片，应用程序崩溃并报错：
```
KeyError: <libs.shape.Shape object at 0x000001A680057F10>
```
崩溃位置：`labelImg.py:1007` 在 `shape_selection_changed()` 方法中

### 根本原因
应用维护了两个独立的 Shape 存储结构：
1. **MainWindow.shapes_to_items** (dict): Shape → QListWidgetItem 映射
2. **Canvas.shapes** (list): 所有绘制的 Shape 对象列表

这两个数据结构由不同模块管理，缺乏同步机制。当用户在调整框大小（长操作）期间切换图片时：
- MainWindow 清空并重建 `shapes_to_items` 字典
- Canvas 加载新的 `shapes` 列表
- 但 `canvas.selected_shape` 仍指向旧图片的 Shape 对象
- 导致访问字典时 KeyError

---

## 修复方案

采用**多层防御策略**（Defense in Depth），共修改 4 处：

### 第一层：症状防护（阻止崩溃）

#### 1. `MainWindow.shape_selection_changed()` - 添加字典查找防护
**文件**: `labelImg.py:1001-1021`

**修改内容**:
- 使用 `.get()` 代替 `[]` 直接访问字典
- 发现 shape 不在字典中时，主动清除 Canvas 选择状态

**效果**: 即使出现不一致，也优雅降级而非崩溃

```python
# 修改前
if shape:
    self.shapes_to_items[shape].setSelected(True)  # ❌ KeyError

# 修改后
if shape:
    item = self.shapes_to_items.get(shape)  # ✅ 安全访问
    if item is not None:
        item.setSelected(True)
    else:
        # 发现不一致，清除选择
        self.canvas.de_select_shape()
        self.label_list.clearSelection()
```

---

### 第二层：状态同步修复（根治问题）

#### 2. `Canvas.load_shapes()` - 清除无效选择状态
**文件**: `libs/canvas.py:720-726`

**修改内容**:
- 加载新 shapes 后，检查 `selected_shape` 是否仍在列表中
- 如果不在，立即调用 `de_select_shape()` 清除

**效果**: 切断旧 shape 引用，防止后续访问

```python
def load_shapes(self, shapes):
    self.shapes = list(shapes)
    self.current = None
    # 清除选择状态，防止指向旧图片的shape引用
    if self.selected_shape and self.selected_shape not in self.shapes:
        self.de_select_shape()  # ✅ 主动检测并清理
    self.repaint()
```

#### 3. `MainWindow.show_bounding_box_from_annotation_file()` - 强制清除
**文件**: `labelImg.py:1429-1441`

**修改内容**:
- 清空字典后，立即清除 Canvas 的选择状态

**效果**: 确保加载新图片时状态完全重置

```python
self.label_list.clear()
self.items_to_shapes.clear()
self.shapes_to_items.clear()
# 强制清除 Canvas 的选择状态，防止指向旧 shapes
self.canvas.de_select_shape()  # ✅ 新增
```

---

### 第三层：架构增强（完善逻辑）

#### 4. `Canvas.reset_state()` - 补充清空 shapes
**文件**: `libs/canvas.py:748-756`

**修改内容**:
- `reset_state()` 时清空 `shapes` 列表

**效果**: 确保 reset 是完整的全状态清理

```python
def reset_state(self):
    self.de_select_shape()
    self.un_highlight()
    self.selected_shape_copy = None
    self.shapes = []  # ✅ 新增：清空shapes列表
    
    self.restore_cursor()
    self.pixmap = None
    self.update()
```

---

## 验证结果

### 自动化测试
创建了专门的测试文件：`tests/test_shape_keyerror_fix.py`

**测试用例**:
1. ✅ `test_load_shapes_clears_invalid_selected_shape` - 验证清除无效选择
2. ✅ `test_load_shapes_keeps_valid_selected_shape` - 验证保留有效选择
3. ✅ `test_reset_state_clears_shapes` - 验证 reset 清空列表
4. ✅ `test_shape_selection_changed_with_invalid_shape` - 验证字典防护
5. ✅ `test_scenario_resizing_then_switch_image` - 端到端场景复现

**测试结果**: 所有 5 个测试通过（0.088s）

### 代码质量检查
- ✅ Python 语法检查通过
- ✅ 模块导入成功
- ✅ 无副作用，正常场景行为不变

---

## 影响评估

### 修改范围
- **修改文件**: 2 个 (`labelImg.py`, `libs/canvas.py`)
- **修改函数**: 4 个
- **新增代码**: 12 行
- **删除代码**: 0 行

### 风险等级
**极低** - 所有修改均为：
- 添加防护检查（不改变正常流程）
- 补充清理逻辑（符合现有模式）
- 无架构变更
- 无API变更

### 兼容性
- ✅ 向后兼容
- ✅ 不影响现有功能
- ✅ 不改变用户交互

---

## 部署建议

### 测试清单
在部署到生产前，建议测试以下场景：

- [ ] 正常标注流程（创建、调整、删除框）
- [ ] 快速连续切换图片
- [ ] 在调整框大小期间切换图片（原崩溃场景）
- [ ] 使用快捷键快速切换图片
- [ ] 撤销/重做操作
- [ ] 删除标注后切换图片

### 回滚方案
如果出现意外问题，可以回滚 4 处修改：
1. `labelImg.py:1007-1014` 恢复为 `self.shapes_to_items[shape].setSelected(True)`
2. `labelImg.py:1439` 删除 `self.canvas.de_select_shape()`
3. `libs/canvas.py:723-725` 删除检查逻辑
4. `libs/canvas.py:752` 删除 `self.shapes = []`

---

## 经验教训

### 架构层面
1. **单一数据源原则**: 多个模块维护相同数据的副本容易导致不一致
2. **事件驱动同步**: 状态变更应通过事件/回调通知相关模块
3. **防御性编程**: 对外部数据访问应有防护检查

### 代码层面
1. **字典访问**: 优先使用 `.get()` 而非 `[]`，除非确定键存在
2. **状态清理**: reset/load 等操作应清理所有相关状态
3. **引用生命周期**: 对象引用应与数据结构生命周期同步

### 测试层面
1. **边界条件**: 测试快速操作、并发场景等边界情况
2. **长操作中断**: 测试长操作（拖动、绘制）期间的状态切换
3. **端到端场景**: 模拟真实用户操作路径

---

## 相关链接

- 问题分析文档: `memory/shape_keyerror_crash.md`
- 测试代码: `tests/test_shape_keyerror_fix.py`
- Git commit: (待提交)

---

**修复人员**: Claude (Kiro AI)  
**审核状态**: 待人工审核  
**部署状态**: 待部署
