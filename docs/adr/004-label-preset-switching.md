# Label Preset Switching

Users annotate multiple projects per day, each requiring different label sets (e.g., vehicle detection vs medical imaging). Manual replacement of `predefined_classes.txt` is error-prone and time-consuming. We decided to support multiple label presets with menu-based switching.

## Decision

- **Storage**: Label presets are `.txt` files under `data/` and `data/label_presets/`; root files take precedence when names collide.
- **Default**: Restore the saved preset; otherwise choose the first available preset sorted by name (currently ADC). The legacy `data/predefined_classes.txt` is no longer shipped.
- **Naming**: File name without extension becomes preset name in UI (`cars.txt` → `cars`)
- **UI**: Menu-based single-selection (similar to `Format` menu for PascalVOC/YOLO)
- **Persistence**: Selected preset saved to `settings.pkl`, restored on next launch
- **Session isolation**: Switching presets clears `label_hist` and reloads from new preset file; temporary labels added during annotation are discarded

## Why This Design

**Storage locations**: Existing root presets such as `data/ADC.txt` remain discoverable, while `data/label_presets/` keeps additional project lists organized.

**Menu-based UI**: Users already understand the `Format` menu pattern (PascalVOC/YOLO switching). Reusing this interaction model reduces learning cost. Dropdown in toolbar was considered but clutters the interface when preset names are long.

**Session isolation for temporary labels**: When users add labels during annotation, these are context-specific decisions for the current project. Carrying them to a new project (new preset) would pollute the label namespace. Users who need a temporary label permanently should edit the preset file before switching.

**No in-app preset management**: Creating/editing/deleting presets is a low-frequency operation compared to switching. Text file editing is faster and more flexible than building UI forms for this.

## Rejected Alternatives

- **Per-directory preset binding**: Would require `.labelimg_config` files in every image directory. Adds complexity for team collaboration (who owns the config file?). Users said they switch projects (presets) multiple times per day, not per directory.
- **Merge multiple presets**: Allowing users to load multiple preset files and merge labels creates ambiguity (what if two presets have conflicting labels?). Single preset per session is clearer.
- **Toolbar dropdown**: Clutters toolbar when preset names are long. Menu provides unlimited space for preset names and is consistent with existing `Format` switching pattern.
