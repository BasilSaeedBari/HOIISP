# Website Specification
## Open Innovation & Independent Study Platform (OIISP)
### Habib University — Engineering & Computer Science Division

**Document Version:** 1.0  
**Status:** Draft — Pilot Phase  
**Maintained By:** OIISP Initiative Lead  
**Last Revised:** May 2026

---

## 1. Purpose & Scope

This document defines the full functional specification, information architecture, and user-experience design of the OIISP web platform. The platform serves as the single source of truth for all independent student projects: from initial proposal submission through milestone tracking, faculty endorsement, and final archival. It is designed to operate as a lightweight, self-hosted application that integrates transparently with existing university communication infrastructure (Microsoft Teams).

---

## 2. Design Philosophy

The platform is governed by three non-negotiable principles:

1. **Friction-Minimal Submission.** A student with a finished Markdown proposal should be able to create a live, publicly visible project entry in under three minutes.
2. **Zero New Habits for Faculty.** All faculty notifications arrive through Microsoft Teams — a channel they already monitor. Faculty are never required to log into the platform to participate.
3. **Permanent, Auditable Record.** Every project, milestone update, and endorsement is versioned and publicly archived. The platform is a living portfolio, not a bulletin board.

---

## 3. User Roles

| Role | Description | Key Permissions |
|---|---|---|
| **Student (Owner)** | Proposes and manages a project | Submit proposal, post updates, upload files, invite collaborators |
| **Student (Collaborator)** | Added to a project by the Owner | Post updates, upload files |
| **Faculty (Observer)** | Browses and endorses projects | Star, Vouch, Endorse, comment on final report |
| **Lab Technician** | Reviews resource requests | Approve/deny resource bookings, flag safety concerns |
| **OIISP Admin** | Platform administrator | Approve proposals, manage users, moderate content, manage tags |
| **Public (Unauthenticated)** | General viewer | Read-only access to all public projects and the leaderboard |

---

## 4. Information Architecture

```
/                           → Landing Page + Live Leaderboard
/projects                   → Full Project Directory (filterable)
/projects/[project-slug]    → Individual Project Page
/submit                     → Proposal Upload Portal (authenticated students only)
/faculty                    → Faculty Directory with Expertise Tags
/resources                  → Lab Resource Availability Dashboard
/about                      → Platform Documentation & How-It-Works
/admin                      → Admin Panel (role-gated)
```

---

## 5. Page Specifications

### 5.1 Landing Page (`/`)

The landing page is the primary public face of the platform. It must communicate the initiative's purpose in seconds and immediately surface active projects.

**Components:**

- **Hero Block:** One-sentence description of OIISP. A single call-to-action: `Submit a Proposal`.
- **Live Leaderboard (Primary Feature):** See Section 6 for full specification.
- **Stats Bar:** Three live counters — `Active Projects`, `Faculty Endorsements`, and `Lab Hours Logged`.
- **Recent Activity Feed:** The five most recent project updates, shown as compact cards with project name, update type (Milestone / Photo / Data), and timestamp.
- **Footer:** Links to `ProposalFormat.md`, `TermsAndConditions.md`, Faculty Directory, and contact.

---

### 5.2 Project Directory (`/projects`)

A searchable, filterable grid of all project cards.

**Filter Controls:**
- Domain (Electrical Engineering, Computer Science, Mechatronics, etc.)
- Lab Resource Used (DLD Lab, Communications Lab, CNC, Lathe, etc.)
- Status (`Proposed` / `Active` / `Completed` / `Archived`)
- Faculty Endorsement (toggle: "Endorsed Only")
- Sort by: Stars, Date Created, Last Updated, Milestone Progress

**Project Card (Compact View):**
```
┌─────────────────────────────────────────────┐
│  [DOMAIN TAG]  [STATUS BADGE]               │
│  Project Title                              │
│  ─────────────────────────────────────────  │
│  Lead: Student Name   Team: 2 members       │
│  Progress: ████████░░ 80%  [M3 of 4]       │
│  ★ 12 Stars   ✓ 2 Faculty Endorsements     │
│  Last Update: 3 days ago                   │
└─────────────────────────────────────────────┘
```

---

### 5.3 Individual Project Page (`/projects/[project-slug]`)

This is the core unit of the platform. Every approved proposal auto-generates one of these pages.

**Sections (in order):**

1. **Project Header**
   - Title, Status badge, Domain tags, Team members with Habib email links
   - Date Approved, Target Completion Date
   - Star count + Star button (authenticated users)

2. **Abstract & Objective** *(auto-populated from submitted Markdown)*

3. **Milestone Tracker**
   - Visual progress bar segmented by milestone
   - Each milestone card: name, planned date, actual date, status (Pending / In Progress / Complete / Delayed)

4. **Update Feed** *(chronological)*
   - Each update card: date, update type tag, written description, attached photos/simulation files/data CSVs
   - Faculty can comment on individual updates (threaded)

5. **Resource Log**
   - Table: Resource Used | Date | Hours | Technician Sign-Off

6. **Documents**
   - Linked to original submitted `proposal.md`
   - All milestone reports (downloadable)
   - Final Report (if completed)

7. **Endorsements Panel** *(right sidebar)*
   - Faculty "Stars" with name and department
   - Faculty "Vouches" with name, department, and optional quote
   - Faculty "Endorsements" (post-completion) with full endorsement text

---

### 5.4 Proposal Upload Portal (`/submit`)

The entry point for all new projects. This page accepts a student's completed Markdown file and auto-parses it to create a project entry.

**Upload Flow:**

```
Step 1: Authentication
  └─ Student logs in with Habib University SSO (Microsoft)

Step 2: Upload Proposal
  └─ Drag-and-drop or file picker — accepts .md files only
  └─ Live preview of parsed proposal renders on the right

Step 3: Auto-Validation
  └─ System checks that all required sections are present (see ProposalFormat.md)
  └─ Missing sections are flagged inline with red markers before submission
  └─ Student confirms or corrects

Step 4: Resource Declaration
  └─ System extracts the Resource Management Matrix from the proposal
  └─ Student confirms which specific labs and equipment will be required
  └─ A resource request is queued for Lab Technician review

Step 5: Declaration & Submit
  └─ Student checks: "I have read and agree to the Terms and Conditions"
  └─ Student checks: "All stated collaborators have been informed"
  └─ Submit → Proposal enters 'Pending Review' status

Step 6: Admin Review (48-hour SLA)
  └─ OIISP Admin reviews for completeness and policy compliance
  └─ On Approval: project page goes live + Teams notification fires
  └─ On Rejection: student receives itemized feedback via email
```

**Markdown Parser Rules:**

The system uses the following heading anchors to auto-populate project page fields. These headings are defined in `ProposalFormat.md` and are treated as required keys:

| Markdown Heading | Maps To |
|---|---|
| `# Project Title` | Page title, leaderboard entry |
| `## Abstract` | Abstract section |
| `## Problem Statement` | Problem section |
| `## Domain & IEEE Alignment` | Domain tags |
| `## Methodology` | Methodology section |
| `## Work Breakdown Structure` | Milestone tracker (parsed as table) |
| `## Resource Management Matrix` | Resource log (pre-populated) |
| `## Risk Assessment` | Risk section |
| `## Success Metrics` | Metrics panel |
| `## Team Members` | Team display (parsed as list) |

---

### 5.5 Faculty Directory (`/faculty`)

A publicly browsable directory of Habib University faculty, cross-referenced with active and completed projects in their domain.

**Each Faculty Card:**
- Name, title, department
- Research interests / expertise tags
- "Active in X Projects" (linked)
- "Has Endorsed X Projects" (linked)
- Contact link (Habib email)

This page directly addresses the original problem: students not knowing the expertise of their professors.

---

### 5.6 Resource Availability Dashboard (`/resources`)

A live-updating view of which labs and major equipment items are currently booked by active OIISP projects.

**Displays:**
- Lab name
- Equipment items
- Current booking (project name + student name)
- Next available slot
- Cumulative OIISP usage hours (resets each semester)

This gives lab technicians and students a shared, transparent view of demand.

---

## 6. The Leaderboard — Full Specification

The leaderboard is the most important feature. It is not a competition; it is a **discovery engine** for both students and faculty.

### 6.1 Default Columns

| Column | Description |
|---|---|
| `#` | Rank (sorted by Stars by default) |
| Project Name | Linked to project page |
| Domain | Primary domain tag |
| Field | Specific sub-field (e.g., "FPGA Design") |
| Team | Number of students (expandable to show names) |
| Status | `Proposed` / `Active` / `Completed` |
| Progress | Visual progress bar (milestone-based) |
| Stars | Total stars from students + faculty |
| Endorsements | Number of faculty endorsements |
| Last Update | Days since last milestone post |

### 6.2 Sorting & Discovery

- Columns are sortable
- Rows are filterable by domain, status, endorsement status
- A "New This Week" highlight stripe draws attention to recently approved proposals
- A "Stale" warning badge appears on projects with no update in 14 days (configurable)

### 6.3 Leaderboard as a Faculty Tool

Faculty can subscribe to specific domain tags directly from the leaderboard. When a new project with a matching tag is approved, they receive a single Teams notification (not an email). This is the mechanism through which organic mentorship is ignited.

---

## 7. Technical Stack (Pilot Phase)

The following stack is chosen for simplicity, self-hostability, and zero vendor lock-in.

| Layer | Technology | Rationale |
|---|---|---|
| **Frontend** | Next.js (React) | Fast static rendering for public pages; SSR for dynamic leaderboard |
| **Backend** | Node.js / Express or Next.js API routes | Simple REST API for proposal ingestion and webhook dispatch |
| **Database** | PostgreSQL | Relational model maps cleanly to projects/milestones/endorsements |
| **File Storage** | MinIO (self-hosted S3-compatible) | Stores uploaded `.md` files, photos, and data files |
| **Markdown Parser** | `remark` / `gray-matter` | Parses proposal `.md` files and extracts front-matter + sections |
| **Auth** | Microsoft Azure AD (Habib SSO) | No new passwords; students and faculty use their Habib credentials |
| **Notification Engine** | Microsoft Teams Incoming Webhook | Pushes read-only Cards to the designated Teams channel |
| **Hosting** | Docker on a university server (or a low-cost VPS for pilot) | Self-contained, no dependency on paid cloud services |
| **Reverse Proxy** | Nginx | SSL termination, routing |

---

## 8. Content Policy

- All project content is public by default. Students agree to this at submission.
- No proprietary or commercially sensitive data may be posted. If a project has IP concerns, students must flag it at submission for admin review.
- Faculty endorsements are voluntary, non-binding, and do not constitute formal academic supervision unless separately arranged.
- The platform is not a grading system. No grades are issued through OIISP.

---

## 9. Data Retention & Archival

- Active and completed projects are retained permanently as a public portfolio.
- Stale projects (no update for 60 days, not marked complete) are moved to `Archived` status after admin notification.
- All submitted `.md` files, update photos, and reports are stored and versioned.
- At the end of each academic year, a compiled PDF of the year's completed projects is generated and published.

---

## 10. Pilot Success Metrics (Week 1)

The following metrics will be collected during the 7-day pilot sprint and presented to the administration in the formal proposal:

| Metric | Target |
|---|---|
| Proposals submitted | ≥ 8 |
| Unique lab resources requested | ≥ 5 |
| Faculty accounts active | ≥ 3 |
| Total faculty stars given | ≥ 15 |
| Teams channel messages received | ≥ 20 (automated) |
| Page views (public, unauthenticated) | ≥ 100 |
| Student-reported time to submit (UX) | ≤ 10 minutes |

---

*This document is a living specification. All sections are subject to revision based on pilot feedback.*
