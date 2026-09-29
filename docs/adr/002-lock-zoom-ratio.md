# ADR 002: 锁定缩放比例模式

## Status
Implemented

## Context
当前行为：切换图片时，如果之前是手动缩放（MANUAL_ZOOM），会自动切回自适应模式（通常是 FIT_WINDOW），导致每张图片的显示比例不一致。

在标注一批尺寸相似的图片时，用户需要为每张图片重新调整缩放比例，效率低。

## Decision
添加"锁定缩放比例"Toggle 按钮：

### UI 设计
- **控件类型**：工具栏 Toggle 按钮（QAction with checkable=True）
- **位置**：紧邻 FIT_WINDOW 和 FIT_WIDTH 按钮
- **图标**：
  - 解锁状态：🔓 或类似图标
  - 锁定状态：🔒 或类似图标
- **标签**：「锁定缩放」
- **视觉反馈**：
  - 锁定时：按钮高亮（背景色变化）+ 🔒图标
  - 解锁时：正常状态 + 🔓图标
- **默认状态**：OFF（解锁），会话级，不持久化
- **键盘快捷键**：无（仅工具栏按钮操作）

### 锁定行为
用户点击「锁定缩放」按钮时：
1. **捕获当前缩放比例**：从 `self.zoom_widget.value()` 读取（百分比，如 150）
2. **存储锁定值**：`self.locked_zoom_value = current_zoom`
3. **设置锁定标志**：`self.lock_zoom = True`
4. **后续图片加载**：`load_file()` 中跳过 `adjust_scale()` 逻辑，直接应用 `self.set_zoom(locked_zoom_value)`

**关键特性：严格比例保留**
- 不考虑图片尺寸差异
- 始终应用相同的百分比值
- 可能导致图片超出或小于视口（这是预期行为，用户可滚动查看）

### 解锁触发条件
锁定状态自动解除的两种方式：

#### 方式1：用户主动解锁
- 再次点击「锁定缩放」按钮 → Toggle OFF → `lock_zoom = False`

#### 方式2：切换到自适应模式自动解锁
- 点击 FIT_WINDOW 按钮 → `set_fit_window()` 中自动设置 `lock_zoom = False`
- 点击 FIT_WIDTH 按钮 → `set_fit_width()` 中自动设置 `lock_zoom = False`
- 按 `Ctrl+F` 快捷键（触发 `set_fit_window()`）→ 自动解锁
- 按 `Ctrl+Shift+F` 快捷键（触发 `set_fit_width()`）→ 自动解锁
- 所有自适应操作会同时更新「锁定缩放」按钮的视觉状态（checked=False）

**设计理由**：FIT_WINDOW/FIT_WIDTH 的语义是"让每张图片都适应窗口/宽度"，这与"锁定固定比例"本质冲突。用户切换到自适应模式时，应自动解除锁定。

### 锁定期间手动缩放
当锁定状态下，用户仍可以：
- **滚轮缩放** / **Ctrl++/-/=** → `locked_zoom_value` **实时更新**
- 切换到下一张图片 → 使用更新后的 `locked_zoom_value`

**场景示例**：
```
1. 用户缩放到 150% → 点击「锁定缩放」
2. 切换到图2 → 显示 150%
3. 用户滚轮调整到 180%（locked_zoom_value 自动更新为 180）
4. 切换到图3 → 显示 180%
```

## Implementation Notes

### State Management
```python
self.lock_zoom = False  # Toggle 状态标志
self.locked_zoom_value = 100  # 锁定的缩放比例值（百分比）
self.lock_zoom_action = None  # 工具栏按钮引用（用于同步视觉状态）
```

### 关键修改点

#### 1. `load_file()` / `paint_canvas()` - 图片加载后
```python
def paint_canvas(self):
    # ... 加载图片逻辑 ...
    if self.lock_zoom:
        # 锁定模式：应用固定比例
        self.set_zoom(self.locked_zoom_value)
    else:
        # 正常模式：自适应缩放
        self.adjust_scale(initial=True)
```

#### 2. `set_zoom()` / `add_zoom()` - 手动缩放时
```python
def set_zoom(self, value):
    # ... 原有缩放逻辑 ...
    if self.lock_zoom:
        # 实时更新锁定值
        self.locked_zoom_value = value
```

#### 3. `set_fit_window()` / `set_fit_width()` - 切换到自适应模式时
```python
def set_fit_window(self, value=True):
    if value:
        self.lock_zoom = False  # 自动解锁
        if self.lock_zoom_action:
            self.lock_zoom_action.setChecked(False)  # 同步按钮状态
    # ... 原有逻辑 ...
```

#### 4. 新增 `toggle_lock_zoom()` 方法
```python
def toggle_lock_zoom(self):
    self.lock_zoom = not self.lock_zoom
    if self.lock_zoom:
        # 锁定：记录当前缩放比例
        self.locked_zoom_value = self.zoom_widget.value()
        # 更新按钮图标（如果需要动态切换）
        # self.lock_zoom_action.setIcon(new_icon('lock'))
    else:
        # 解锁：恢复按钮图标
        # self.lock_zoom_action.setIcon(new_icon('unlock'))
        pass
```

#### 5. 创建工具栏按钮
```python
lock_zoom = action('&Lock Zoom', self.toggle_lock_zoom,
                   None, 'lock',  # 无快捷键
                   'Lock zoom ratio across images', checkable=True)
self.lock_zoom_action = lock_zoom
# 添加到工具栏，放在 FIT_WINDOW/FIT_WIDTH 附近
```

## Consequences

### Positive
- 批量标注同类图片时，视觉连续性更好
- 减少重复调整缩放的操作
- 适合高分辨率图片标注（固定在某个"最佳标注比例"）

### Negative
- 图片尺寸差异大时，可能出现显示过大/过小
- 用户需要理解"锁定模式"的概念
- 需要增加一个工具栏按钮（UI 空间占用）

### Edge Cases
- 锁定模式下切换到空图片/损坏图片 → 保持锁定状态，等待下一张正常图片
- 锁定值为极端值（10%或500%）→ 允许，用户自行判断是否合理
