# TAVIO – UI Navigation Design Decisions

**Document status:** Navigation layout and hierarchy agreed; button and submenu functionality remains under design.  
**Scope:** Sidebar appearance, navigation hierarchy, menu labels, ordering, and placement.  
**Implementation status:** Design record only; this document does not authorize application-code, database-schema, or migration changes.

## 1. Design goals

The TAVIO interface should feel modern, capable, clear, and user-friendly. Navigation should remain predictable as the application grows to include more modules. The design should make good use of desktop screen space while keeping the main navigation readily accessible.

## 2. Modern ribbon-style collapsible sidebar

The primary navigation uses a modern ribbon-style sidebar on the left side of the application.

### 2.1 Expanded mode

- Display each main menu item with its icon and text label.
- Present the menu hierarchy clearly and consistently.
- Keep the sidebar layout consistent when users move between modules.

### 2.2 Collapsed mode

- Keep a narrow icon-only strip visible on the left; do not hide the sidebar completely.
- Provide a dedicated control to expand the sidebar.
- Preserve the agreed icon placement and visual alignment.

### 2.3 Layout and state

- Provide a dedicated expand/minimize control near the top of the sidebar.
- Remember the selected expanded or collapsed state between application launches.
- Keep the sidebar layout consistent when users navigate between modules.
- Allow the overall layout to adapt to smaller application-window sizes where appropriate.

## 3. Main navigation structure

The agreed navigation design establishes the main menu groups, their labels, submenu labels, ordering, and placement. The structure is recorded here as a navigation and layout specification.

### 3.1 Dashboard

- Dashboard

Dashboard is the main landing-page destination after a workspace has been opened successfully. Its content and component design are specified separately in [Dashboard Design Specification](dashboard_design.md).

### 3.2 File

- New
- Open
- Save
- Save As
- Exit

The menu labels and their placement in the navigation hierarchy are recorded as agreed. The exact behaviour of each item—including its action, workflow, prompts, validation, save semantics, and handling of unsaved changes—has **not** been finalized in this document and must be designed separately.

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

The menu groups and labels above document the agreed navigation arrangement. Listing a menu item here does not mean that its page, command, or underlying feature is implemented or that its functional requirements have been approved.

## 4. Dashboard reference

Dashboard is the main landing page after a workspace opens successfully. Its information hierarchy, components, content, and interaction design are maintained separately in [Dashboard Design Specification](dashboard_design.md).

## 5. Agreed scope and outstanding design

### 5.1 Agreed

- The modern ribbon-style left sidebar.
- Expanded and collapsed sidebar presentation.
- The sidebar's expand/minimize control and remembered display state.
- The main menu groups, submenu labels, ordering, and placement recorded in this document.
- Dashboard's role as the landing-page destination, with its detailed design maintained in a separate document.

### 5.2 Not yet finalized

- The action performed by each button or submenu item.
- The workflows, prompts, validation, confirmations, and error handling associated with those actions.
- The page-level behaviour and detailed interaction requirements for each module.
- The functional relationship and integration between modules.
- Implementation sequencing and technical details.

For example, the File submenu items (New, Open, Save, Save As, and Exit) have agreed labels and navigation placement, but their individual functions and complete workflows remain open for separate discussion and approval.

## 6. Implementation boundaries

This document records navigation presentation and structure only. It does not authorize:

- Implementing or changing button and submenu functionality.
- Implementing module workflows or page-level behaviour.
- Changes to the database schema or migrations.
- Changes to workspace persistence, recovery, or timetable-generation logic.
- Treating a listed menu item as evidence that its feature is complete.

Functional specifications should be discussed and approved separately before implementation.

## 7. Agreed design summary

1. TAVIO uses a modern ribbon-style left sidebar.
2. The sidebar supports Expanded and Collapsed presentation.
3. The sidebar's selected display state is remembered between application launches.
4. Navigation is organized into the main menu groups and submenu labels listed in Section 3.
5. Dashboard is the landing-page destination after a workspace opens; its detailed design is specified in [dashboard_design.md](dashboard_design.md).
6. The menu labels, hierarchy, ordering, and placement are agreed.
7. The functions and workflows behind individual buttons and submenu items—including the File submenu—remain to be designed and approved.
8. This document is a navigation design record, not implementation authorization.
