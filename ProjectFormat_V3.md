# HOIISP Project Format
## Habib Open Innovation & Independent Study Platform
### Habib University — Engineering & Computer Science Division

**Format Version:** 3.0  
**Aligned With:** IEEE Author Guidelines, PMI PMBOK 7th Edition WBS Standards  
**Last Revised:** May 2026

---

> **Instructions for Students**
>
> This file (`project.md`) lives in the **root of your GitHub repository**. It is the only file HOIISP reads from your repo. Everything else — your code, your data, your images, your reports — is yours to organise however you like.
>
> **How to submit your project to HOIISP:**
> 1. Copy this template into a file named exactly `project.md` at the root of your repo.
> 2. Fill in every **[REQUIRED]** section. Empty required sections will cause your submission to be rejected.
> 3. Make at least one Git commit from a `@st.habib.edu.pk` email address. This is how HOIISP verifies that the project belongs to a Habib student. Check your Git config: `git config user.email` — it must show your Habib email before you commit.
> 4. Go to `hoiisp.habib.edu.pk/submit`, paste your GitHub repo URL, and submit. No account needed.
> 5. An admin will review your submission within 48 hours. Once approved, your project page goes live automatically.
>
> **Keeping your project page current:**  
> Edit this file and push to your repo. HOIISP re-reads `project.md` on every push. Your project page will reflect the latest data within minutes. You never need to revisit the HOIISP website.
>
> **Rules:**
> - Do not remove any of the headings below.
> - Do not change heading levels (`#`, `##`, `###`).
> - Do not rename this file. It must be `project.md` in the repo root.
> - You may add sub-headings inside any section.
> - Table column names must not be changed — they are parsed by name.
> - Status values in the WBS table must be exactly: `Not Started`, `In Progress`, `Complete`, or `Delayed`.

---

# Project Title
> *[REQUIRED] Your full, specific project title.*  
> *Good: "Real-Time ECG Arrhythmia Detection Using a Convolutional Neural Network on Raspberry Pi 4"*  
> *Bad: "Health Monitoring Device"*

`Replace this line with your project title.`

---

## GitHub Repository
> *[REQUIRED] The canonical URL of this GitHub repository. Must match exactly what you submitted to HOIISP.*

`https://github.com/your-username/your-repo`

---

## Team Members
> *[REQUIRED] List all team members. Maximum 4 students. The GitHub username column is used to cross-reference commit history during verification — make sure each username is correct. The email column must use `@st.habib.edu.pk` addresses.*

| Full Name | Student ID | GitHub Username | Habib Email | Program | Year | Role |
|---|---|---|---|---|---|---|
| Full Name | HU-XXXXX | github-username | name@st.habib.edu.pk | EE / CS / CE | 2 / 3 / 4 | Lead |
| Full Name | HU-XXXXX | github-username | name@st.habib.edu.pk | | | Co-Investigator |

---

## Abstract
> *[REQUIRED] 200–300 words. Cover: what you are building, why it matters, what method you will use, and what a successful outcome looks like. A reader who only reads this section should understand your project completely.*

Write your abstract here.

---

## Problem Statement
> *[REQUIRED] 150–250 words. Define the specific problem or gap your project addresses. Be precise. State the problem directly — this is not background reading.*

Write your problem statement here.

---

## Domain & IEEE Alignment
> *[REQUIRED] HOIISP uses this section to categorise your project and route it to relevant faculty.*

**Primary Domain:** *(select one by replacing `[ ]` with `[x]`)*
- [ ] Electrical Engineering
- [ ] Computer Science
- [ ] Computer Engineering
- [ ] Mechatronics / Robotics
- [ ] Telecommunications
- [ ] Power Systems
- [ ] Signal Processing
- [ ] Other: _______________

**Sub-Field / Specialization:**  
`Write your sub-field here. e.g., "Embedded Systems", "Digital Signal Processing", "Machine Learning"`

**Relevant IEEE Technical Society:**  
`e.g., "IEEE Robotics and Automation Society", "IEEE Computer Society"`

**Applicable IEEE Standard(s), if any:**  
`e.g., IEEE 802.11 for WiFi. Write "None directly applicable" if not relevant.`

---

## Objectives
> *[REQUIRED] List 3–6 specific, measurable objectives. Format: "To [action verb] [measurable outcome] by [method/means]."*

1. Objective 1
2. Objective 2
3. Objective 3

---

## Methodology
> *[REQUIRED] 300–500 words. Describe your technical approach: tools, hardware, software, simulation strategy, and the flow from concept to prototype.*

### Design & Simulation Phase
Describe what simulations or models you will produce before building. List tools (MATLAB, Simulink, KiCad, Proteus, Python, Quartus, etc.).

### Hardware / Software Implementation Phase
Describe what you will build. Circuits, PCBs, firmware, software systems, ML pipelines — whatever applies.

### Testing & Validation Phase
Describe how you will verify your system meets the success metrics. What tests? What instruments or tools?

---

## Work Breakdown Structure (WBS)
> *[REQUIRED] This table is parsed to generate your milestone tracker on the HOIISP project page.*  
> *Do not change column names. Use status values exactly: `Not Started`, `In Progress`, `Complete`, `Delayed`.*  
> *Update this table and push to GitHub to keep your milestone progress current on HOIISP.*

| Milestone # | Milestone Name | Key Deliverables | Start Date | End Date | Status |
|---|---|---|---|---|---|
| M1 | Design & Simulation | Completed schematic / model / simulation results | YYYY-MM-DD | YYYY-MM-DD | Not Started |
| M2 | Component / Material Procurement | All components sourced and received | YYYY-MM-DD | YYYY-MM-DD | Not Started |
| M3 | Prototype Build | Assembled and functional prototype v1 | YYYY-MM-DD | YYYY-MM-DD | Not Started |
| M4 | Testing & Debugging | Test log, documented issues and fixes | YYYY-MM-DD | YYYY-MM-DD | Not Started |
| M5 | Final Build & Documentation | Final working system + project report | YYYY-MM-DD | YYYY-MM-DD | Not Started |

**Estimated Total Duration:** `X weeks`

---

## Resource Management Matrix
> *[REQUIRED] List every piece of university equipment you plan to use. Be specific — "Oscilloscope (2-channel, Tektronix TBS1052B) in Electronics Lab" not just "oscilloscope".*  
> *Lab Technicians review this table. Estimated hours must be realistic.*

| Resource | Lab / Location | Estimated Hours | Purpose in Project | Required From | Required Until |
|---|---|---|---|---|---|
| e.g., Oscilloscope (2-channel) | Electronics Lab | 10 hrs | Signal waveform verification | YYYY-MM-DD | YYYY-MM-DD |
| e.g., Basys 3 FPGA Board | DLD Lab | 20 hrs | Hardware FSM implementation | YYYY-MM-DD | YYYY-MM-DD |

> If you require access to Tier 2/3 equipment (Lathe, Drill Press, Milling Machine, PCB CNC), confirm below:

- [ ] I have read Schedule A of the Terms & Conditions and will complete all required safety training before using listed Tier 2/3 equipment.

---

## Risk Assessment
> *[RECOMMENDED] 3–5 most significant risks and your mitigation plan for each.*

| Risk | Likelihood (H/M/L) | Impact (H/M/L) | Mitigation Strategy |
|---|---|---|---|
| e.g., CNC booked during critical phase | M | H | Book 2 weeks in advance; identify off-campus PCB fab backup. |
| e.g., Specific IC not available locally | M | M | Order from LCSC/Digikey with 2-week buffer before hardware phase. |

---

## Success Metrics
> *[REQUIRED] 3–6 quantitative, measurable metrics that define project success. Vague metrics ("the system should work well") will cause your submission to be rejected.*

| Metric | Target Value | Measurement Method |
|---|---|---|
| 1. | | |
| 2. | | |
| 3. | | |

---

## Project Updates
> *[RECOMMENDED — but required to maintain Active status]*  
> *HOIISP reads this section to populate your project's update feed. Each update is a sub-heading with a date, followed by a short written entry. Push a new update at least once every two weeks to maintain Active project status and lab access.*  
> *You may link to files, issues, pull requests, or commits in your repo from here.*

### Update Log

#### YYYY-MM-DD — [Update Title]
Brief description of what was done this week. What worked, what didn't, what's next.  
Links to relevant commits, PRs, or issues: [commit abc123](https://github.com/...)

---

## Data & Documentation Plan
> *[RECOMMENDED] Describe what data you will collect and how you will store it in this repo.*

- e.g., Oscilloscope screenshots at each test point, stored as `.png` in `/data/scope/`
- e.g., Sensor readings at 1 Hz, exported as `.csv` in `/data/logs/`
- e.g., All code version-controlled in this repository
- e.g., Build-stage photos in `/docs/photos/`

**Repo structure commitment:** I understand that the HOIISP project page links directly to this repository. The repo should be organised and have a readable top-level README.

- [ ] Confirmed.

---

## Budget Estimate
> *[RECOMMENDED] Rough breakdown of anticipated out-of-pocket costs. For planning purposes only.*

| Item | Source | Estimated Cost (PKR) |
|---|---|---|
| e.g., ESP32 Development Board (×2) | Local market | 2,400 |
| e.g., Resistors, Capacitors (assorted) | University Lab (at cost) | 500 |
| | **Total Estimated:** | |

---

## References
> *[RECOMMENDED] IEEE citation format.*

[1] A. Author, "Title of paper," *IEEE Transactions on [Journal Name]*, vol. X, no. X, pp. XX–XX, Month Year.  
[2] Component Manufacturer, *[Part Name] Datasheet*, Rev. X.X, Year. [Online]. Available: URL.

---

## Declaration
> *[REQUIRED] Check all boxes before submitting the GitHub URL to HOIISP. Unchecked declarations will block approval.*

- [ ] I confirm that the information in this `project.md` is accurate and complete.
- [ ] I have read and agree to the HOIISP Terms & Conditions in full.
- [ ] I confirm that all listed team members are aware of this submission and have agreed to participate.
- [ ] I confirm that at least one team member has committed to this repository using a `@st.habib.edu.pk` Git email address.
- [ ] I understand that approval of this submission grants access only to the resources explicitly listed in the Resource Management Matrix.
- [ ] I understand that I must push a `project.md` update at least once every two weeks to maintain Active project status and lab access.
- [ ] I accept that all content parsed from this repository will be publicly visible on the HOIISP platform.
- [ ] I confirm this repository is set to **Public** visibility on GitHub (HOIISP cannot read private repositories).

---

## For Office Use Only
> *Do not fill in this section.*

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

---

*HOIISP — Habib University | Questions? Contact the HOIISP Administrator through the designated Teams channel or email `hoiisp@habib.edu.pk`.*
