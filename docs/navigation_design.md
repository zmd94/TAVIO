# TAVIO – UI Navigation and Dashboard Design Decisions

**Document status:** Navigation structure agreed  
**Scope:** Sidebar and main navigation structure  
**Implementation status:** Design record only; no application code, database schema, or migration changes are authorized by this document.

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

## 4. Dashboard

Dashboard is the main landing page after a workspace opens successfully. Its content, information hierarchy, components, and interaction design are maintained separately in [Dashboard Design Specification](dashboard_design.md).

## 7. Scope boundaries and implementation notes

This document records the agreed UI navigation structure and sidebar design direction only. Dashboard content and layout decisions belong in [dashboard_design.md](dashboard_design.md).

It does not authorize:
- Changes to the database schema or migrations.
- Changes to existing stable application workflows.
- Implementation of modules that are not yet developed.
- Changes to workspace persistence, recovery, or timetable-generation logic.

Detailed page layouts, field-level behaviour, validation messages, permissions (if applicable), and implementation sequencing should be designed separately before implementation.

## 8. Agreed design summary

1. TAVIO uses a modern ribbon-style left sidebar.
2. The sidebar supports Expanded and Collapsed modes.
3. The sidebar state is remembered between application launches.
4. Navigation is organized into the modules listed in Section 3.
5. Dashboard is the main landing page after opening a workspace; its design is specified in [dashboard_design.md](dashboard_design.md).
6. File is a command menu: New, Open, Save, Save As, and Exit execute actions and never open content pages.
7. Other main menus and their submenus navigate to pages only when the corresponding page exists and is implemented.
8. This is a design record, not implementation authorization.
