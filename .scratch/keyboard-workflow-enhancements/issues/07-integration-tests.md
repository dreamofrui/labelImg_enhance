# 07 — 集成测试

**What to build:** 完整的自动化测试套件，覆盖所有三个功能的核心场景和边界情况。使用 unittest.TestCase 框架，遵循现有测试模式，验证端到端行为。

**Blocked by:** 01-keyboard-label-cycling, 02-lock-zoom-ratio, 05-restore-deleted-image, 06-label-undo

**Status:** ready-for-agent

- [ ] MainWindow 集成测试：键盘循环、锁定缩放、图片删除恢复、标签撤销
- [ ] 文件操作测试：临时目录清理、同名文件覆盖、跨目录恢复
- [ ] 跨功能集成测试：删除图片时标签栈清空、恢复图片时自动聚焦、锁定状态下删除/恢复图片
- [ ] 边界情况测试：空列表、单张图片、最后一张、栈为空
- [ ] 测试使用 unittest.TestCase 框架，遵循现有测试模式（参考 tests/test_io.py）
- [ ] 测试可通过 `python -m pytest tests/` 或 `python -m unittest` 运行
