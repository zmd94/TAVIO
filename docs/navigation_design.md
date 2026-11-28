# TAVIO – UI Navigation and Dashboard Design Decisions

**Document status:** Agreed UI design direction  
**Scope:** Navigation structure and Dashboard concept only  
**Implementation status:** Design decisions; no application code or database changes are authorized by this document.

## 1. Design goals

The TAVIO interface should feel modern, capable, clear, and user-friendly. Navigation should remain predictable as the application grows to include more modules. The design should make good use of desktop screen space without hiding the main navigation completely.

## 2. Modern Ribbon-style Collapsible Sidebar

The primary navigation will use a modern ribbon-style sidebar on the left side of the application.

### 2.1 Expanded mode

- Display each main menu item with its icon and text label.
- Allow users to access the relevant submenu or module.
- Keep the hierarchy clear and visually consistent.

### 2.2 Collapsed mode

- Keep a narrow icon-only strip visible on the left; do not hide the sidebar completely.
- Show the menu name through a tooltip when the pointer hovers over an icon.
- Allow users to expand the sidebar through a dedicated control.

### 2.3 State and navigation behaviour

- Provide a dedicated expand/minimize control near the top of the sidebar.
- Preserve the selected expanded or collapsed state after the application is closed and reopened.
- Keep the sidebar state consistent when users navigate between modules.
- On smaller windows, the layout may adapt to use a temporary navigation panel where appropriate.

## 3. Main navigation structure

The agreed navigation direction is a set of main modules with relevant submenus. The proposed structure is:

### 3.1 Dashboard
- Main landing page after a workspace has been opened successfully.

### 3.2 File
- New
- Open
- Save
- Save As
- Exit

The File menu is a **command menu**, not a page-navigation module. Its submenu items execute workspace or application actions; they must not create or display placeholder pages in the main content area.

Command mapping:
- **New** executes the agreed **NEW TIMETABLE** operation and creates a new workspace.
- **Open** executes the agreed **OPEN AS** operation and prompts the user to select a `.tavio` workspace file.
- **Save** explicitly saves the active workspace to its current `.tavio` file.
- **Save As** saves the active workspace to a separately selected `.tavio` file without modifying its source.
- **Exit** runs the application's safe exit workflow, including unsaved-change and applicable recovery-failure handling.

The visible labels may remain concise as shown above; the underlying operation must follow the workspace-management decisions. These commands are not master-data pages and must never be routed to the page stack.

### 3.3 School Setup
- School Profile
- School Administrators
- Schedule Signatories

### 3.4 Master Data
- Teachers
- Classes
- Class Teacher
- Subjects
- Special Rooms
- Teaching Distribution

### 3.5 Timetable
- Generate Timetable
- Timetable Versions
- View Timetable

### 3.6 Manual Editor
- Edit Timetable
- Validate Changes

### 3.7 Absences & Relief
- Teacher Absences
- Relief Management
- Relief Timetable

### 3.8 Reports
- PDF Preview
- Generate PDF
- Report Settings

### 3.9 Settings
- General
- Appearance
- About TAVIO

The module names and submenu labels above describe the intended navigation structure. File is intentionally different from the other main items: it dispatches commands instead of navigating to pages. The presence of any menu item does not mean its underlying feature has already been implemented.

## 4. Dashboard design

Dashboard is the main landing page after a workspace opens successfully. It should provide a useful overview of the currently selected school workspace without requiring users to open several modules.

### 4.1 School information

Display relevant workspace context, including:
- School name and logo.
- Selected academic year.
- Selected session.

### 4.2 Summary cards

Show summary counts based on actual workspace data, such as:
- Teachers.
- Classes.
- Subjects.
- Special Rooms.
- Timetable status.

The displayed counts must be read from the active workspace. Illustrative figures in design mock-ups are not real data.

### 4.3 Workspace readiness

Show clear completion or attention-needed indicators for relevant setup areas, for example:
- School Profile.
- Master Data.
- Class Teacher Assignment.
- Timetable.

Readiness indicators should be calculated from actual data and validation rules, not manually entered status text. The Dashboard must not silently change or create user data.

### 4.4 Timetable status

Show the relevant timetable state and version information for the selected academic year and session. Do not imply that a timetable is current merely because it has the highest version number; follow the application's explicit timetable-version selection rules.

### 4.5 Quick Actions

Provide shortcuts to commonly used destinations, such as:
- Master Data.
- Generate Timetable.
- Reports.

Quick Actions navigate to existing functions; they must not bypass the normal validation and confirmation rules of those functions.

## 5. Academic year and session selection

Provide academic year and session selectors near the top of the Dashboard.

- The user can select the academic year and session to inspect.
- Dashboard summaries, readiness indicators, and timetable status update to reflect the selected context.
- The selection is a viewing/filtering context and must not silently modify the workspace's underlying academic-year or session records.
- If a selected combination has no relevant data, show a clear empty state rather than misleading counts or status.

## 6. Visual and interaction principles

- Use a clean, modern desktop layout with clear visual hierarchy.
- Use consistent icons, labels, spacing, and submenu behaviour.
- Keep navigation discoverable in both expanded and collapsed modes.
- Use concise status indicators and explanatory text where needed.
- Avoid overcrowding the Dashboard; prioritize information that helps users understand workspace readiness and their next useful action.
- Ensure keyboard and accessibility considerations are included during detailed UI design.

## 7. Scope boundaries and implementation notes

This document records UI navigation and Dashboard design decisions only.

It does not authorize:
- Changes to the database schema or migrations.
- Changes to existing stable application workflows.
- Implementation of modules that are not yet developed.
- Changes to workspace persistence, recovery, or timetable-generation logic.

Detailed page layouts, field-level behaviour, validation messages, permissions (if applicable), and implementation sequencing should be designed separately before implementation.

## 8. Agreed design summary

1. TAVIO uses a modern ribbon-style left sidebar.
2. The sidebar supports Expanded and Collapsed modes.
3. Collapsed mode remains visible as a narrow icon strip with hover tooltips.
4. The sidebar state is remembered between application launches.
5. Navigation is organized into the modules listed in Section 3.
6. File is a command menu: New, Open, Save, Save As, and Exit execute actions and never open content pages.
7. Other main menus and their submenus navigate to pages only when the corresponding page exists and is implemented.
6. Dashboard is the main landing page after opening a workspace.
7. Dashboard presents school context, summary cards, workspace readiness, timetable status, and Quick Actions.
8. Dashboard summaries are based on actual workspace data.
9. Academic year and session selectors filter the Dashboard's displayed context.
10. This is a design record, not implementation authorization.
