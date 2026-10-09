# 当前操作与项目结构

本文件记录当前实现；历史规格和 `.scratch` 任务笔记不作为快捷键依据。

## 快捷键

| 按键 | 操作 |
|---|---|
| D / A | 下一张 / 上一张图片 |
| W | 绘制矩形框 |
| I | 向前一个标签循环选择，到列表开头后回到最后一个 |
| E | 编辑选中框的标签 |
| Delete / O | 删除选中标注框 |
| U | 恢复当前图片最近删除的标注框 |
| Shift+O | 将当前图片及关联标注文件移到临时回收站 |
| Shift+U | 恢复最近删除的图片 |
| Ctrl+Shift+Delete | 将文件列表选中的图片移到临时回收站 |
| F / H | 缩小 / 放大选中标注框 |
| 方向键 | 按原图像素移动选中框 |
| Ctrl+S | 保存 |
| Ctrl+D | 复制选中框 |
| Ctrl+[ / Ctrl+] | 缩小 / 放大图片显示 |
| Ctrl+Shift+[ / Ctrl+Shift+] | 降低 / 提高图片亮度 |
| Ctrl+F / Ctrl+Shift+F | 适应窗口 / 适应宽度，并解除缩放锁定 |
| Ctrl+K | 切换图片显示比例锁定 |
| Ctrl+H / Ctrl+A | 隐藏 / 显示全部标注框 |

`F/H` 仅在画布或标签列表聚焦时生效，每边默认移动 1 原图像素。
步长可在编辑菜单设置为 1～100；边界及保存约束见 [标注框像素缩放](specs/box-resize.md)。

## 图片和标签恢复

标签删除记录只属于当前图片，在切图、保存或删除当前图片时清空。
图片删除记录按后进先出恢复；切换目录时清空，因此不支持跨目录恢复。
恢复图片后插入当前浏览位置并加载。临时回收站位于系统临时目录，启动时清理超过 24 小时的旧目录。
图片和关联标注分别移动；标注移动失败时可能只保留图片恢复能力，并非文件事务。

锁定缩放比例只在当前会话内有效，重启后解锁。手动改变图片显示比例会更新锁定值。

## 标签预设

从 `data/*.txt` 和 `data/label_presets/*.txt` 扫描预设。文件名去掉 `.txt` 后即预设名；
同名时优先加载 `data/` 根目录的文件。空行和 `#` 注释不作为标签。
启动时恢复上次预设；没有保存值时使用按名称排序的第一个可用预设，当前为 `ADC`。
本仓库已删除原来的 `data/predefined_classes.txt`，内置预设为 ADC、ARS、none。
预设切换会清除会话内临时标签名称，重载标签候选，不改写已有标注框的标签。

## 代码与文档入口

- `labelImg.py`：`MainWindow`、QAction 快捷键、选中映射、切图和保存。
- `libs/canvas.py`：画布交互、原图坐标、选择和几何提交。
- `libs/shape.py`：标注框点坐标及标签属性。
- `libs/labelFile.py`：VOC、YOLO、CreateML 保存；格式读取见对应的 `*_io.py`。
- `CONTEXT.md`：领域术语；`docs/adr/`：决策记录。

## 本地验证

在已安装 PyQt5、lxml 的 Python 环境中运行：

```powershell
python -m PyQt5.pyrcc_main resources.qrc -o libs/resources.py
python -m unittest tests.test_box_resize tests.test_box_resize_workflow tests.test_shape_keyerror_fix tests.test_integration_lite tests.test_utils tests.test_io -v
```

`libs/resources.py` 为忽略的构建产物，更新字符串后须重新生成。
新功能测试使用临时设置与目录，不写入用户的 `.labelImgSettings.pkl`。
旧的 `test_qt` 和 `test_settings` 会访问用户设置，只有隔离设置文件路径后再运行；
`test_stringBundle` 的环境变量用例还需要预设 `LC_ALL` 和 `LANG`。
