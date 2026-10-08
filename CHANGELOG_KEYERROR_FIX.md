# KeyError Crash Fix Changelog

## 2026-10-08 - Critical Bug Fix

### 🐛 Fixed
- **Critical crash when resizing bounding boxes during image switching**
  - Root cause: Shape reference inconsistency between Canvas and MainWindow
  - Error: `KeyError: <libs.shape.Shape object at 0x...>` in `shape_selection_changed()`
  - Impact: Production users experienced application crashes during normal annotation workflow

### ✅ Changes Made

#### Modified Files (2)
1. **labelImg.py** - 2 functions modified
2. **libs/canvas.py** - 2 functions modified

#### Detailed Changes

**1. `labelImg.py:shape_selection_changed()` (Lines 1001-1021)**
- Added dictionary lookup guard using `.get()` instead of direct `[]` access
- Added fallback logic to clear selection when shape not found in dictionary
- Prevents KeyError crash, provides graceful degradation

**2. `labelImg.py:show_bounding_box_from_annotation_file()` (Line 1439)**
- Added `self.canvas.de_select_shape()` call after clearing dictionaries
- Ensures Canvas selection state is cleared when loading new image
- Maintains consistency between Canvas and MainWindow state

**3. `libs/canvas.py:load_shapes()` (Lines 723-725)**
- Added check for `selected_shape` validity after loading new shapes
- Automatically clears selection if selected_shape not in new shapes list
- Prevents stale shape references from previous images

**4. `libs/canvas.py:reset_state()` (Line 752)**
- Added `self.shapes = []` to clear shapes list during reset
- Ensures complete state reset, matching behavior of `load_pixmap()`
- Improves consistency of reset operations

### 🧪 Testing

#### New Tests Added
- Created `tests/test_shape_keyerror_fix.py` with 5 test cases
- All tests pass (0.088s execution time)

#### Regression Tests
- ✅ `test_utils.py` - 2/2 tests pass
- ✅ `test_io.py` - 3/3 tests pass
- ✅ Application import successful

### 📊 Risk Assessment

**Risk Level**: Minimal
- All changes are additive (defensive checks and cleanup)
- No API changes
- No behavior changes in normal scenarios
- Backward compatible

### 🎯 Scenarios Fixed

1. **Primary scenario**: User resizing bounding box → rapid image switch → crash
2. **Fast image switching**: Rapid keyboard navigation between images
3. **Stale references**: Any case where Canvas.selected_shape points to old Shape object

### 📝 Technical Details

**Defense-in-Depth Strategy** (3 layers):
1. **Symptom defense**: Guard against KeyError in `shape_selection_changed()`
2. **State sync**: Clear stale references in `load_shapes()` and during image loading
3. **Architecture**: Complete state reset in `reset_state()`

### 🔍 Related Documentation

- Detailed analysis: `memory/shape_keyerror_crash.md`
- Fix documentation: `docs/fixes/keyerror-crash-fix-20261008.md`
- Test code: `tests/test_shape_keyerror_fix.py`

### 👥 Credits

**Analysis & Fix**: Claude (Kiro AI)  
**Reported by**: Production user (氧化物项目团队)  
**Date**: 2026-10-08

---

## Migration Notes

No migration required. Changes are transparent to users.

## Rollback Procedure

If issues arise, revert these 4 specific changes:
1. `labelImg.py:1007-1014` - Restore direct dictionary access
2. `labelImg.py:1439` - Remove `de_select_shape()` call
3. `libs/canvas.py:723-725` - Remove shape validity check
4. `libs/canvas.py:752` - Remove `self.shapes = []`

Git revert command (after commit):
```bash
git revert <commit-hash>
```
