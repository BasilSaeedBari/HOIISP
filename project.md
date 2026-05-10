# Habib Open Innovation & Independent Study Platform

---

## GitHub Repository
https://github.com/BasilSaeedBari/HOIISP

---

## Team Members
| Full Name | Student ID | GitHub Username | Habib Email | Program | Year | Role |
|---|---|---|---|---|---|---|
| Basil Saeed Bari | bb09892 | BasilSaeedBari | bb09892@st.habib.edu.pk | CE | 2 | Lead |

---

## Abstract
The Habib Open Innovation & Independent Study Platform (HOIISP) is a centralized discovery engine designed to showcase, track, and manage student-led engineering and computer science projects at Habib University. Inspired by the need to bridge the gap between academic research, independent studies, and collaborative innovation, HOIISP provides a unified directory where students, faculty, and administrators can discover active projects and monitor milestones.

Version 3 of HOIISP represents a paradigm shift from the platform's original monolithic file-hosting architecture to a read-only, GitHub-centric discovery engine. Previous iterations of the platform (V1 and V2) suffered from excessive storage costs, complex user authentication systems, and high maintenance overhead due to built-in file editing and uploads. HOIISP V3 addresses these issues by treating student-owned GitHub repositories as the single source of truth. By utilizing a zero-storage policy, automated repository parsing via AST markdown extraction, and real-time Server-Sent Events (SSE) for leaderboards, this project delivers a highly scalable, frictionless experience. The successful outcome of this project is a fully deployed FastAPI-based backend capable of validating Habib University affiliations via commit history, parsing structured `project.md` files, and automatically provisioning project directory pages without requiring students to manage separate accounts on the platform.

---

## Problem Statement
Historically, student projects at Habib University existed in silos. There was no centralized platform to showcase independent studies, track hardware resource allocations, or allow faculty to discover innovative work being done across departments. This lack of visibility hindered cross-disciplinary collaboration and made it difficult for administrators to manage lab equipment efficiently. HOIISP was originally created to solve this by providing a unified, transparent project directory for the university.

However, as the platform evolved, the existing HOIISP V2 architecture became structurally flawed, burdened by its dependency on local file uploads, custom user authentication, and in-platform markdown editors. These features not only duplicate existing capabilities provided by industry-standard tools like GitHub but also create a maintenance nightmare and unnecessary liability regarding data retention. Consequently, the platform became difficult to deploy, costly to host, and created friction for engineering and computer science students who already utilize Git for their projects. There is a critical need to decouple the platform from data hosting and reimplement it as a purely read-only discovery layer that aggregates, parses, and beautifully presents project data directly from student-managed GitHub repositories.

---

## Domain & IEEE Alignment
**Primary Domain:**
- [ ] Computer Science
- [x] Computer Engineering
- [ ] Mechatronics / Robotics
- [ ] Telecommunications
- [ ] Power Systems
- [ ] Signal Processing
- [ ] Electrical Engineering
- [ ] Other: _______________

**Sub-Field / Specialization:**  
Software Engineering, Web Architecture, Webhooks & APIs

**Relevant IEEE Technical Society:**  
IEEE Computer Society

**Applicable IEEE Standard(s), if any:**  
None directly applicable

---

## Objectives
1. To implement a zero-storage architecture by replacing local file hosting with dynamic GitHub API fetching and webhook integrations.
2. To develop an AST-based Markdown parser capable of reliably extracting structured fields (e.g., WBS, Resource Matrix) from a standardized `project.md` file.
3. To secure the platform by replacing student accounts with an automated commit-history verification system that checks for `@st.habib.edu.pk` affiliations.
4. To deliver a responsive, visually stunning frontend using Jinja2, Sakura.css, and vanilla JavaScript (μJS) that updates in real-time via Server-Sent Events.

---

## Methodology
### Design & Simulation Phase
The system architecture was designed around a lightweight FastAPI backend utilizing aiosqlite for persistence. The database schema focuses solely on tracking submissions, webhooks, and parsed metadata rather than file blobs. UI mockups were developed using raw HTML/CSS with Sakura.css to ensure a semantic, highly accessible, and read-only aesthetic.

### Hardware / Software Implementation Phase
The application is built in Python 3.14. The GitHub integration layer utilizes `httpx` to fetch raw markdown and verify author emails via the public GitHub commit API. Parsing logic relies on `mistune` to generate an Abstract Syntax Tree (AST), which is then walked to map markdown tables to SQL rows. The frontend uses Jinja2 templates and a custom Micro-JS (`app.js`) library to handle AJAX form submissions (`u-post`) and maintain an active SSE connection for live leaderboard updates.

### Testing & Validation Phase
The parser is validated through an exhaustive suite of edge-cases utilizing `test_parser.py`, ensuring resilience against malformed tables and missing sections. API rate limits are monitored, and a fallback mechanism is implemented to prioritize `raw.githubusercontent.com` over the authenticated GitHub API where possible. 

---

## Work Breakdown Structure (WBS)
| Milestone # | Milestone Name | Key Deliverables | Start Date | End Date | Status |
|---|---|---|---|---|---|
| M1 | Architectural Design | Database schema, config loader, environment setup | 2026-05-01 | 2026-05-05 | Complete |
| M2 | GitHub Integration | Affiliation check, raw fetcher, commit scanner | 2026-05-06 | 2026-05-10 | Complete |
| M3 | AST Parser Development | `mistune` AST extraction, table parsing, validation | 2026-05-11 | 2026-05-15 | Complete |
| M4 | Frontend & Server-Sent Events | Jinja2 templates, Sakura.css styling, SSE Leaderboard | 2026-05-16 | 2026-05-20 | Complete |
| M5 | Webhooks & Automation | Push event handlers, APScheduler integration, Teams Bot | 2026-05-21 | 2026-05-28 | Not Started |

**Estimated Total Duration:** 4 weeks

---

## Resource Management Matrix
| Resource | Lab / Location | Estimated Hours | Purpose in Project | Required From | Required Until |
|---|---|---|---|---|---|
| Virtual Private Server (VPS) | Cloud / Remote | 720 hrs | Hosting the FastAPI backend | 2026-05-01 | 2026-06-01 |
| CI/CD Pipeline | GitHub Actions | 10 hrs | Automated testing and deployment | 2026-05-20 | 2026-05-28 |

> If you require access to Tier 2/3 equipment (Lathe, Drill Press, Milling Machine, PCB CNC), confirm below:

- [ ] I have read Schedule A of the Terms & Conditions and will complete all required safety training before using listed Tier 2/3 equipment.

---

## Risk Assessment
| Risk | Likelihood (H/M/L) | Impact (H/M/L) | Mitigation Strategy |
|---|---|---|---|
| GitHub API Rate Limiting | M | H | Utilize unauthenticated `raw.githubusercontent.com` for markdown fetching; use authenticated API only for commit history. |
| Malformed `project.md` submissions | H | M | Build robust AST parser with strict validation; reject submissions automatically with detailed error reports. |
| SSE Connection limits on VPS | L | M | Configure Nginx reverse proxy with appropriate timeout and connection limits; optimize SSE queue logic. |

---

## Success Metrics
| Metric | Target Value | Measurement Method |
|---|---|---|
| 1. Submission Processing Time | < 5 seconds | Backend API latency logging |
| 2. File Storage Overhead | 0 MB (excluding SQLite db) | Server disk usage monitoring |
| 3. Parser Accuracy | 100% on valid formats | Automated unit tests (`test_parser.py`) |

---

## Project Updates
### Update Log

#### 2026-05-10 — Initial Architecture and Phase 1 Complete
Successfully completed Phase 1 of the V3 reimplementation. The database is initialized, the AST parser correctly handles complex markdown tables, and the core routing is in place. Addressed an environment bug involving passlib/bcrypt conflicts and resolved Jinja2 TemplateResponse signature changes. The platform is now ready for webhook integration.

---

## Data & Documentation Plan
- All source code hosted in this repository (`BasilSaeedBari/HOIISP`).
- Architecture decisions documented in `README_V3.md` and `IntegrationV3.md`.
- Database schemas detailed in `app/db.py`.

**Repo structure commitment:** I understand that the HOIISP project page links directly to this repository. The repo should be organised and have a readable top-level README.

- [x] Confirmed.

---

## Budget Estimate
| Item | Source | Estimated Cost (PKR) |
|---|---|---|
| DigitalOcean Basic Droplet | Cloud Provider | 1,500 / month |
| Domain Name Registration | Namecheap | 3,000 / year |
| | **Total Estimated:** | 4,500 |

---

## References
[1] FastAPI Documentation, *FastAPI*, 2026. [Online]. Available: https://fastapi.tiangolo.com.
[2] "Mistune: A fast yet powerful Python Markdown parser with renderers and custom directives," 2026. [Online]. Available: https://mistune.readthedocs.io/.
[3] GitHub Developer, *REST API endpoints for Repositories*, 2026. [Online]. Available: https://docs.github.com/en/rest/repos/repos.

---

## Declaration
- [x] I confirm that the information in this `project.md` is accurate and complete.
- [x] I have read and agree to the HOIISP Terms & Conditions in full.
- [x] I confirm that all listed team members are aware of this submission and have agreed to participate.
- [x] I confirm that at least one team member has committed to this repository using a `@st.habib.edu.pk` Git email address.
- [x] I understand that approval of this submission grants access only to the resources explicitly listed in the Resource Management Matrix.
- [x] I understand that I must push a `project.md` update at least once every two weeks to maintain Active project status and lab access.
- [x] I accept that all content parsed from this repository will be publicly visible on the HOIISP platform.
- [x] I confirm this repository is set to **Public** visibility on GitHub (HOIISP cannot read private repositories).

---

## For Office Use Only
| Field | Value |
|---|---|
| HOIISP Submission ID | |
| GitHub Verification Status | |
| Assigned Project Slug | |
| Review Outcome | Approved / Rejected / Revisions Required |
| Review Notes | |
| Admin | |
| Date of Decision | |
| Resource Request Forwarded | |
| Lab Access Activated | |
