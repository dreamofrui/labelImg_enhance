#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple manual verification for Issue #7 implementation
"""

import sys
import os

# Check implementation in source code
print("=" * 60)
print("Issue #7: Label Undo Functionality - Implementation Verification")
print("=" * 60)

with open('labelImg.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Check label_deletion_stack initialization
print("\n1. Checking label_deletion_stack initialization...")
if 'self.label_deletion_stack = []' in content:
    print("   [PASS] label_deletion_stack is initialized in __init__")
else:
    print("   [FAIL] label_deletion_stack not found in __init__")

# 2. Check delete_selected_shape pushes to stack
print("\n2. Checking delete_selected_shape() implementation...")
if 'label_deletion_stack.append' in content and 'def delete_selected_shape' in content:
    # Find the method
    lines = content.split('\n')
    in_method = False
    found_append = False
    for line in lines:
        if 'def delete_selected_shape' in line:
            in_method = True
        elif in_method and line.strip().startswith('def '):
            break
        elif in_method and 'label_deletion_stack.append' in line:
            found_append = True
            break

    if found_append:
        print("   [PASS] delete_selected_shape() pushes to label_deletion_stack")
    else:
        print("   [FAIL] delete_selected_shape() does not push to stack")
else:
    print("   [FAIL] Implementation not found")

# 3. Check restore_last_deleted_label method exists
print("\n3. Checking restore_last_deleted_label() method...")
if 'def restore_last_deleted_label' in content:
    print("   [PASS] restore_last_deleted_label() method exists")

    # Check for key implementation details
    if 'label_deletion_stack.pop()' in content:
        print("   [PASS] Method pops from stack")
    if 'canvas.shapes.append' in content:
        print("   [PASS] Method restores to canvas")
else:
    print("   [FAIL] restore_last_deleted_label() method not found")

# 4. Check 'z' key binding
print("\n4. Checking 'z' key binding...")
if "'z'" in content and 'restore_last_deleted_label' in content:
    # Check they're in the same action definition
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'restore_last_deleted_label' in line and "'z'" in line:
            print("   [PASS] 'z' key is bound to restore_last_deleted_label")
            break
    else:
        # Check nearby lines
        for i, line in enumerate(lines):
            if 'restore_last_deleted_label' in line:
                # Check surrounding lines for 'z'
                context = '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
                if "'z'" in context:
                    print("   [PASS] 'z' key is bound to restore_last_deleted_label")
                    break
        else:
            print("   [WARNING] Could not verify 'z' key binding in context")
else:
    print("   [FAIL] 'z' key binding not found")

# 5. Check load_file() clears stack
print("\n5. Checking load_file() clears stack...")
lines = content.split('\n')
in_method = False
found_clear = False
for line in lines:
    if 'def load_file' in line:
        in_method = True
    elif in_method and line.strip().startswith('def ') and 'load_file' not in line:
        break
    elif in_method and 'label_deletion_stack.clear()' in line:
        found_clear = True
        break

if found_clear:
    print("   [PASS] load_file() clears label_deletion_stack")
else:
    print("   [FAIL] load_file() does not clear stack")

# 6. Check _save_file() clears stack
print("\n6. Checking _save_file() clears stack...")
in_method = False
found_clear = False
for line in lines:
    if 'def _save_file' in line:
        in_method = True
    elif in_method and line.strip().startswith('def '):
        break
    elif in_method and 'label_deletion_stack.clear()' in line:
        found_clear = True
        break

if found_clear:
    print("   [PASS] _save_file() clears label_deletion_stack")
else:
    print("   [FAIL] _save_file() does not clear stack")

# 7. Check delete_current_image() handles stack
print("\n7. Checking delete_current_image() handles stack...")
in_method = False
found_handling = False
for line in lines:
    if 'def delete_current_image' in line:
        in_method = True
    elif in_method and line.strip().startswith('def '):
        break
    elif in_method and 'label_deletion_stack' in line:
        found_handling = True
        break

if found_handling:
    print("   [PASS] delete_current_image() handles label_deletion_stack")
else:
    print("   [FAIL] delete_current_image() does not handle stack")

print("\n" + "=" * 60)
print("Verification Complete!")
print("=" * 60)
