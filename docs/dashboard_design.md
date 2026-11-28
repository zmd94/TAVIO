# TAVIO – Dashboard Design Specification

**Document status:** Working design specification; component selection and detailed layout remain under review  
**Scope:** Dashboard content, information hierarchy, components, and interaction behaviour  
**Implementation status:** Design record only; no application code, database schema, or migration changes are authorized by this document.

## 1. Purpose and design goals

Dashboard is the main landing page after a workspace opens successfully. It should provide a useful overview of the currently selected school workspace without requiring users to open several modules.

The Dashboard should feel modern, clear, and useful. It should help users understand the current workspace context, school-data overview, timetable state, and likely next actions without becoming overcrowded.

This is a living design specification. A component mentioned here is not automatically final. Components may be retained, changed, removed, or added as they are discussed.

## 2. Decision status convention

Use the following labels when recording design decisions:

- **Agreed:** Explicitly accepted design decision.
- **Proposed:** A suggested direction that has not yet been accepted as final.
- **Open:** Requires further discussion or a decision.

The status of a section or component should be updated as the discussion progresses. Do not treat a proposal as implementation authorization.

## 3. Dashboard information hierarchy

**Status: Proposed**

The current working arrangement is to organize the Dashboard in the following hierarchy:

1. **Workspace context area:** School name and official school logo, with academic-year and session selectors near the top.
2. **Summary area:** Compact cards for key school-data counts and timetable/generation indicators.
3. **Operational overview:** Workspace-readiness information and the selected academic-year/session timetable status.
4. **Quick Actions:** Shortcuts to commonly used modules or workflows.

This is a working arrangement, not a locked component list or final pixel-level layout. The exact card set, grouping, order, dimensions, and responsive behaviour remain open for review.

## 4. Dashboard components

### 4.1 School information

**Status: Proposed**

Display relevant workspace context, including:

- School name.
- The school's official logo. This is the school identity asset, not the TAVIO application logo used for sidebar branding.
- Selected academic year.
- Selected session.

### 4.2 Summary cards

**Status: Proposed**

Show summary counts based on actual workspace data, such as:

- Teachers.
- Classes.
- Subjects.
- Special Rooms.
- Timetable status.

Displayed counts must be read from the active workspace. Illustrative figures in design mock-ups are not real data.

The exact cards to retain, remove, or add remain open for component-by-component discussion.

### 4.3 Workspace readiness

**Status: Proposed**

Show clear completion or attention-needed indicators for relevant setup areas, for example:

- School Profile.
- Master Data.
- Class Teacher Assignment.
- Timetable.

Readiness indicators should be calculated from actual data and validation rules, not manually entered status text. The Dashboard must not silently change or create user data.

The readiness categories, calculation rules, and visual treatment remain open for detailed design.

### 4.4 Timetable status

**Status: Proposed**

Show the relevant timetable state and version information for the selected academic year and session.

Do not imply that a timetable is current merely because it has the highest version number; follow the application's explicit timetable-version selection rules.

The exact information and presentation remain open for review.

### 4.5 Quick Actions

**Status: Proposed**

Provide shortcuts to commonly used destinations, such as:

- Master Data.
- Generate Timetable.
- Reports.

Quick Actions navigate to existing functions; they must not bypass the normal validation and confirmation rules of those functions.

The final actions, ordering, and presentation remain open.

## 5. Generation Attempts metric

**Status: Agreed — label and counting semantics**

The Dashboard metric previously referred to as **Current Version** is named **Generation Attempts**.

- It represents the total number of timetable-generation attempts for the relevant selected academic year and session.
- The count includes both successful and failed generation attempts.
- It is not the number of saved timetable versions.
- The intended data source is a dedicated `timetable_generation` record for each generation attempt.
- The existing `timetable_versions` table continues to represent saved timetable versions. It must not be used as the sole source for counting generation attempts because failed attempts may not create a saved timetable version.
- The proposed `timetable_generation` table is separate from `timetable_versions`. Adding it should be handled through a new migration (Migration v5 is the current candidate), not by rewriting historical migrations or changing the stable timetable-version structure.

**Technical design still open:** The table's detailed columns, status lifecycle, indexes, retention policy, and transaction behaviour require a separate technical design review. This document does not approve a SQL schema or authorize implementation.

**Additional Dashboard detail open:** Whether a separate timestamp indicator (for example, the most recent generation attempt) should appear, and its final label and semantics, remain undecided.

## 6. Academic year and session selection

**Status: Proposed**

Provide academic year and session selectors near the top of the Dashboard.

- The user can select the academic year and session to inspect.
- Dashboard summaries, readiness indicators, and timetable status update to reflect the selected context.
- The selection is a viewing/filtering context and must not silently modify the workspace's underlying academic-year or session records.
- If a selected combination has no relevant data, show a clear empty state rather than misleading counts or status.

## 7. Visual and interaction principles

**Status: Proposed**

- Use a clean, modern desktop layout with clear visual hierarchy.
- Use consistent icons, labels, spacing, and component behaviour.
- Use concise status indicators and explanatory text where needed.
- Avoid overcrowding the Dashboard; prioritize information that helps users understand workspace readiness and their next useful action.
- Ensure keyboard and accessibility considerations are included during detailed UI design.
- Define responsive behaviour for different application-window sizes during detailed layout design.

## 8. Open design work

The following work remains for future discussion:

1. Review Dashboard components one at a time and classify each as **Keep**, **Change**, **Remove**, or **Add**.
2. Confirm which summary cards are genuinely useful.
3. Decide the final placement and visual priority of Workspace Readiness and Timetable Status.
4. Decide whether Generation Attempts should be shown as a summary card and whether any additional generation timestamp/status detail is useful.
5. Confirm the final Quick Actions.
6. Agree the detailed layout, spacing, dimensions, and behaviour at different window sizes.

## 9. Scope boundaries and implementation notes

This document records Dashboard design direction only.

It does not authorize:

- Changes to the database schema or migrations.
- Changes to existing stable application workflows.
- Implementation of modules that are not yet developed.
- Changes to workspace persistence, recovery, or timetable-generation logic.

Detailed page layouts, field-level behaviour, validation messages, permissions (if applicable), and implementation sequencing should be designed and authorized separately before implementation.
