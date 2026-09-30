# labelImg Context

## Domain Model

### Core Concepts

#### Label（标签）
A **Label** is an annotation attached to a region in an image. In labelImg:
- Represented as a **Shape** object in `canvas.shapes` (geometry + metadata)
- Displayed as a **QListWidgetItem** in `label_list` (text + color indicator)
- Persisted to disk as XML/JSON/TXT format (depends on `self.label_file_format`)

**Key operations**:
- Delete: `delete_selected_shape()` removes from both canvas and list, pushes to `label_deletion_stack`
- Restore: `restore_last_deleted_label()` pops from `label_deletion_stack` and restores label (ADR 003 - Issue #7)
- Cycle: `cycle_next_label()` moves selection to next label (ADR 001)

#### Image Deletion（图片删除）
**Temporary trash deletion** with undo support (ADR 003):
- Deleted images move to system temp directory `%TEMP%/labelImg_trash_{timestamp}/`
- Trash directory auto-created at app startup, old trash dirs (>24h) auto-cleaned
- Both image file and label file are moved atomically
- Same-name conflicts → overwrite old file (recent deletion overwrites previous)
- `image_deletion_stack` maintains deletion order for undo (LIFO)
- Restored images **insert at current position**, not original position

**Navigation after deletion**:
- Delete middle image → load next image (index unchanged, list shortened)
- Delete last image → load previous image (index decremented)
- Restore image → insert at current position, load restored image

#### Zoom Locking（缩放锁定）
**Lock zoom ratio** across image navigation (ADR 002):
- Toggle button in toolbar (checkable action, **no keyboard shortcut**)
- When locked: apply fixed zoom ratio to all loaded images
- Manual zoom adjustments update the locked value in real-time
- Auto-unlock when switching to adaptive mode:
  - Click FIT_WINDOW/FIT_WIDTH button
  - Press `Ctrl+F` (fit window) or `Ctrl+Shift+F` (fit width)

### Current Enhancements (Proposed)

#### ADR 001: 键盘循环聚焦标签
- **Auto-focus**: Last label auto-selected when image loads (current default)
- **'h' key**: Cycle to previous label (backward, wraps to last at beginning)
- **Pure keyboard workflow**: D/A (navigate images) + h (cycle labels backward) + Delete (remove)

#### ADR 002: 锁定缩放比例
- **Lock button**: Toggle zoom lock (no keyboard shortcut by design)
- **Behavior**: Fixed zoom ratio maintained across image navigation
- **Visual feedback**: Button icon/color changes when locked

#### ADR 003: 图片删除与恢复（临时回收站模式）
- **Two-layer undo**:
  - Label undo ('z'): current image only, cleared on image switch or image deletion
  - Image undo ('u'): cross-directory, LIFO restoration
- **'o' key**: Delete current image to temp trash (no confirmation dialog)
- **'u' key**: Restore last deleted image, **insert at current position**
- **Temp trash**: `%TEMP%/labelImg_trash_{timestamp}/`, auto-cleaned after 24 hours on app startup
- **Same-name conflicts**: overwrite old file (recent deletion overwrites previous)
- **File list context menu**: Delete/Restore actions

## Technical Architecture

### Key Components
- `MainWindow` (libs/app.py): Main application controller
- `Canvas` (libs/canvas.py): Drawing surface, shape management
- `LabelFile` (libs/label_file.py): XML/JSON/TXT persistence
- `Shape` (libs/shape.py): Geometry and metadata for annotations

### State Management
```python
# Image navigation
self.m_img_list: List[str]  # Paths to all images in current directory
self.cur_img_idx: int       # Current image index

# Label management
self.canvas.shapes: List[Shape]         # All shapes in current image
self.label_deletion_stack: List[tuple]  # Undo stack for labels: (shape, label_text, item_flags)
                                         # Cleared when switching images, saving, or deleting image
                                         # Press 'z' to restore (Issue #7 - ADR 003)

# Image deletion
self.image_deletion_stack: List[tuple]  # Undo stack for images: (trash_img_path, trash_label_path, original_dir)
self.trash_dir: str                     # Path to temp trash: %TEMP%/labelImg_trash_{timestamp}/

# Zoom control
self.lock_zoom: bool           # Is zoom locked?
self.locked_zoom_value: int    # Locked zoom ratio (percentage)
```

### Keyboard Shortcuts

#### Existing
- `D`: Next image
- `A`: Previous image
- `W`: Create rectangle box
- `Ctrl+S`: Save
- `Delete`/`Backspace`: Remove selected label
- `Ctrl++/Ctrl+-`: Zoom in/out
- `Ctrl+Wheel`: Zoom
- `Ctrl+F`: Fit to window
- `Ctrl+Shift+F`: Fit to width

#### New (Proposed)
- `h`: Cycle to previous label (backward, ADR 001)
- `z`: Restore last deleted label (ADR 003)
- `o`: Delete current image to trash (ADR 003)
- `u`: Restore last deleted image (ADR 003)

## User Workflows

### Data Cleaning Workflow
**Goal**: Review images and labels, delete low-quality data

1. Open directory of images
2. Image loads, last label auto-selected (default Qt behavior)
3. Press `h` to cycle backward through labels
4. Press `Delete` to remove bad labels
5. Press `z` to undo label deletion if needed
6. Press `o` to delete entire image if quality is poor
7. Press `D` to next image (auto-save if enabled)
8. Press `u` if previous deletion was a mistake

### Zoom-Locked Labeling
**Goal**: Maintain consistent zoom level across similar-sized images

1. Open directory
2. Zoom to comfortable level (e.g., 150%)
3. Click "Lock Zoom" button in toolbar
4. Navigate images with `D`/`A` - zoom stays at 150%
5. Manually adjust zoom if needed (locked value updates)
6. Click "Lock Zoom" again or "Fit Window" to unlock

## Technical Context

### Key Files
- `libs/app.py`: Main application window (`MainWindow` class)
  - Handles all keyboard shortcuts in `keyPressEvent()`
  - Manages image list and navigation
  - Coordinates between canvas, label list, and file I/O
- `libs/canvas.py`: Drawing canvas (`Canvas` class)
  - Shape rendering and interaction
  - Mouse event handling
  - Zoom and pan logic
- `libs/shape.py`: Shape geometry definitions
- `libs/label_file.py`: XML/JSON/TXT file I/O

### Qt Widgets
- `self.label_list` (QListWidget): Displays all labels in current image
- `self.file_list_widget` (QListWidget): Displays all image files in directory
- `self.canvas` (Canvas): Custom QWidget for image/shape rendering
- `self.zoom_widget` (QSpinBox): Displays/controls zoom percentage
