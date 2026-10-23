# RenderX interaction conventions

This audit was performed against the live SDL application on 2026-10-23. The
baseline was launched at a virtual 1360×900 desktop; SDL provided 1178×780, and
the first-frame screenshot was inspected at
`%TEMP%/renderx-jakob-audit/frame-000001.png`. Existing automated tests and the
real-app QA harness are used again after each behavior change. The project is a
software-rendered wireframe viewer with games, so viewer and desktop-editor
conventions apply to Explore; game-specific controls remain scoped to their
destinations. “Gap?” records the baseline mismatch; decisions describe the
implemented behavior and the remaining limits.

## Audit and decisions

| Area | What RenderX does now (observed or verified) | Convention and references | Gap? | Decision |
|---|---|---|---|---|
| Startup | Opens on Shooter with Breakpoint available; a first-run welcome explains Open OBJ and viewport controls before the workspace is used. | Blender, Fusion 360, MeshLab, and Sketchfab open on the editing/viewing workspace. | Yes | Preserve the inventoried Breakpoint launch destination, keep Explore one click away, and make the welcome easy to dismiss or reopen from Help. |
| View orbit | Left-drag orbits X/Y in both presets. Orbit Viewer is the default. | Sketchfab and common web viewers use left-drag orbit; desktop tools vary. | Partial | Use the widely recognized viewer preset by default; retain original Z-turn behavior in RenderX Classic. |
| View pan | Orbit Viewer uses right-drag and middle-drag; Shift+left-drag remains an alias. A short right-click opens a context menu. | Web viewers commonly use right-drag pan; Blender/Fusion commonly use middle-drag pan. | Yes | Keep right-click menus and distinguish a click from a drag. Classic keeps the old right-drag Z-turn and middle/Shift+left pan. |
| View zoom | Wheel changes object scale while over the viewport; positive wheel increases scale. | All listed viewers use the wheel to zoom, generally toward the view center or pointer. | Partial | Keep wheel zoom and its direction. The renderer has no independent camera target, so zoom remains centered on the view/object origin. |
| Drag outside viewport | View navigation continues outside the viewport until mouse-up; focus loss cancels capture. Verified with injected boundary-crossing events. | Desktop editors capture pointer movement until release or focus loss. | Yes | Capture the pointer only after a right-click becomes a drag; keep orbit and pan continuous; release on button-up or focus loss. |
| Frame/reset | `R`, Home, F, and keypad period reset the full scene pose; there is no independent camera target or true frame-to-selection command. | Blender/Fusion use Home/F or a visible frame command. | Yes | Keep `R` and add Home/F/keypad-period aliases for the existing pose reset. Label the action “Reset scene pose” and document that it restores the model's default position, rotation, and scale rather than fitting its bounds. |
| Standard views | No axis snap keys or clickable axis hit targets. | Blender/Maya/Fusion expose front/right/top views and an orientation gizmo. | Yes | Add keypad 1/3/7 and laptop aliases Ctrl+1/3/7, opposites with Ctrl+Shift, keypad 5 and Ctrl+5 projection toggle, and clickable ± axis gizmo labels. |
| Up axis | World axes use X/Y/Z colors, but the up axis is not labelled. | Common 3D tools state and consistently use a world up-axis. | Yes | Identify Y-up in the viewport hint and use the existing axis colors. |
| Open | `O` loads the bundled sample house; a folder button also loads that sample. No native file chooser. | Desktop apps use Ctrl/Cmd+O and a system file chooser. | Yes | Preserve `O` for the sample; add Ctrl/Cmd+O for Wavefront OBJ files using the system chooser and retain recent paths. |
| Export/save | `F12` exports a screenshot; no project save format exists. | Ctrl/Cmd+S saves or exports the current document. | Partial | Preserve F12; alias Ctrl/Cmd+S to the existing screenshot export and label it accordingly. Explain that scene/project saving is not supported. |
| Undo/redo | No undoable action history exists. | Ctrl/Cmd+Z and Ctrl/Cmd+Y (or Shift+Z) apply when an app has reversible edits. | N/A | Do not bind these keys to another action. Record that transform history is not implemented. |
| Quit/fullscreen | Esc exits RenderX outside Maze; the title-bar close works; Shooter alone uses F11. | Ctrl/Cmd+Q or Alt+F4 quits; F11 commonly toggles fullscreen. | Yes | Preserve Esc; add Ctrl/Cmd+Q and Alt+F4 quit aliases, and F11 fullscreen in the main window. |
| Menus/settings | File popover provides Open, Open Recent, screenshot export, Preferences, and Quit in that order; Ctrl/Cmd+, opens navigation preferences. Help contains shortcuts, Getting started, and About. Esc closes the topmost overlay; F1 returns from About to shortcuts. | Desktop apps expose File/Edit/View, Help, and platform Preferences. | Partial | Keep the compact shell's conventional File action order. View choices stay in the visible toolbar and context menu; there is no full menu bar or document/edit history. |
| Layout | Left Scene dock, center viewport, right Inspector, bottom status bar; splitter dividers are draggable. | Shared by Blender, Fusion, Unity, and VS Code-style editors. | No | Keep the existing layout; retain its draggable splitters and collapsible docks. |
| Sections/toggles | Section headers and their full row are clickable; labels on toggles share the action hit rectangle. | Standard desktop controls use full-row headers and label-click toggles. | No | Keep this behavior. Add clearer chevrons/labels only if the existing affordance test shows ambiguity. |
| Text fields | Click-to-replace numeric fields; Enter commits, Esc reverts, Tab moves between fields while editing, Ctrl/Cmd+A selects all, and Up/Down steps values. | Standard editors support Enter commit, Esc revert, Tab traversal, select all, and arrow stepping. | Yes | Keep destination cycling on Tab outside a numeric edit; make field traversal contextual and report invalid values visibly. |
| Sliders | Drag changes values; numeric fields allow exact entry. Shift drag is fine adjustment, Ctrl/Cmd snaps, and double-click restores a value's default. | Desktop editors use drag, exact values, and modifier-assisted fine/snap changes. | Partial | Keep the existing slider and field controls; add modifier behavior and a double-click reset. The inspector reset button remains available. |
| Context menus | Right-clicking the viewport opens Reset transform, Front/Right/Top view, and projection actions. Right-clicking an object row offers Select/frame and, for the selected object, Reset transform. | Standard editors use context menus; web viewers reserve right-drag for pan. | Yes | A short right-click opens the menu; a drag keeps the selected preset's right-button navigation. The built-in mesh catalog is not editable, so delete/hide actions are not offered. |
| Tooltips/cursors | Tooltips show control names and bound shortcuts; navigation uses a move cursor, fields use text, and splitters/sliders use resize cursors. SDL dummy cannot display native cursors. | Desktop and editor apps show delayed labels and contextual cursors. | Partial | Keep tooltips inside the window and use familiar cursors. Native cursor appearance still needs confirmation in a normal desktop session. |
| Errors/file safety | OBJ parsing returns readable errors and preserves the running app; replacing the active mesh does not prompt. | Native open dialogs, recent files, and save/discard prompts are standard. | Partial | Keep safe parsing and provide recent files. Since the application has no project-save format or unsaved document state, no Save/Don't Save prompt applies. |
| Window behavior | Resizable, minimum size, HiDPI pointer mapping, title/icon, and clean close are covered by tests. F11 round-trips fullscreen. | Standard desktop window behavior. | No | Preserve the window lifecycle and coordinate mapping. |
| Discoverability | F1/? opens a grouped shortcut overlay; Explore's status line names the active mouse gestures and Y-up axis. First-run welcome is reopenable from Help. | Desktop apps provide a welcome/empty state and contextual status hints. | Yes | Keep the live shortcut map as the source of truth, explain mouse navigation in the status bar, and let users reopen the short welcome guide. |
| Shortcut overlay | Rows come from the shared input map and include Explore navigation, platform modifiers, field traversal, and destination-specific controls only where they work. | Help lists shortcuts by area from the real input map. | Yes | Keep metadata in `renderx/input_map.py`, scope navigation rows to Explore, render all rows without truncation at the minimum supported window, and preserve game-scoped keys. |
| Game controls | Maze, Challenges, and Breakpoint use distinct control sets; Maze keeps WASD/arrows, Q/E, P, Space, R, Esc; Breakpoint keeps WASD/arrows, mouse fire, Shift dash, Esc, F11. | Games commonly scope controls to their mode and publish them in contextual help. | Partial | Preserve these bindings and show mode-specific groups in help. |

## Preset choice

The default is **Orbit Viewer**: left-drag orbit, right-drag pan, middle-drag
pan, wheel zoom, and Shift+left-drag pan. This matches Sketchfab and the common
web 3D viewer pattern while retaining middle-drag pan familiar from desktop
tools. **RenderX Classic** preserves the previous map: left-drag orbit,
Shift+left/middle-drag pan, right-drag Z-turn, and wheel scale. Both presets
retain the existing keyboard controls. A short right-click opens the context
menu in either preset; dragging still performs the selected gesture.

## Verified deviations and scope

- Ctrl/Cmd+Z and redo remain unbound because there is no edit history; they do
  not trigger unrelated actions.
- Ctrl/Cmd+S exports the screenshot because RenderX has no project/document
  save format. F12 remains available.
- Ctrl/Cmd+Z and redo remain unbound because transforms have no undo history;
  Delete is not offered because the Scene panel is a built-in mesh catalog, not
  a deletable object hierarchy.
- No unsaved-change prompt is shown because loaded OBJ geometry is not edited
  and there is no project file to save.
- A complete File/Edit/View menu bar is not introduced in this pass. File
  actions remain in a conventional File popover; View actions stay on the
  toolbar and viewport context menu. There is no document/edit history for an
  Edit menu to operate on.
- Scene zoom remains centered on the selected model's origin; the renderer has
  no independent camera target to support pointer-centered zoom.
- Home/F/keypad-period reset the scene pose through the existing `Scene.reset()`
  action. They do not fit arbitrary mesh bounds to the viewport because RenderX
  has no independent camera/framing system.
- SDL's dummy video driver cannot prove the appearance of OS cursors or the
  OpenGL Breakpoint window. These require a normal desktop session.
