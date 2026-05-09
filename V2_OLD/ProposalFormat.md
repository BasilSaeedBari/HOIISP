# OIISP Project Proposal — Standard Format
## Open Innovation & Independent Study Platform (OIISP)
### Habib University — Engineering & Computer Science Division

**Format Version:** 1.0  
**Aligned With:** IEEE Author Guidelines, PMI PMBOK 7th Edition Work Breakdown Structure Standards  
**Last Revised:** May 2026

---

> **Instructions for Students:**
> This document is your proposal template. Fill in every section. Sections marked **[REQUIRED]** are parsed by the platform and will cause submission to fail if absent or empty. Sections marked **[RECOMMENDED]** are strongly encouraged and will significantly improve your chances of faculty engagement.
>
> When complete, save this file as `proposal.md` and upload it through the OIISP portal at `/submit`. The system will auto-generate your project page from this file.
>
> Do not remove any of the headings. Do not change heading levels (`#`, `##`, `###`). You may add sub-headings under any section as needed.

---

# Project Title
> *[REQUIRED] Your full project title. Be specific. "Smart Irrigation System Using Soil Moisture Sensors and ESP32 Microcontroller" is better than "IoT Plant Watering Thing."*

`Replace this line with your project title.`

---

## Team Members
> *[REQUIRED] List all team members. Maximum 4 students per project. Each person must have their own Habib University account.*

| Name | Student ID | Program | Year | Role |
|---|---|---|---|---|
| Full Name | HU-XXXXX | EE / CS / CE | 2 / 3 / 4 | Lead / Co-Investigator |
| Full Name | HU-XXXXX | | | |

---

## Abstract
> *[REQUIRED] A concise summary of the entire project in 200–300 words. Must cover: what you are building, why it matters, what method you will use, and what a successful outcome looks like. A reader who only reads this section should understand your project completely.*

Write your abstract here. 200–300 words.

---

## Problem Statement
> *[REQUIRED] In 150–250 words, define the specific problem or gap your project addresses. Be precise. Cite a real-world need, a gap in existing technology, or a domain challenge. This is not a history lesson — state the problem directly.*

Write your problem statement here.

---

## Domain & IEEE Alignment
> *[REQUIRED] Select your primary domain and list the most relevant IEEE Technical Society or IEEE standard that governs your field. This helps faculty in your field discover your project.*

**Primary Domain:** *(select one)*
- [ ] Electrical Engineering
- [ ] Computer Science
- [ ] Computer Engineering
- [ ] Mechatronics / Robotics
- [ ] Telecommunications
- [ ] Power Systems
- [ ] Signal Processing
- [ ] Other: _______________

**Sub-Field / Specialization:** *(e.g., "Digital Signal Processing", "Embedded Systems", "VLSI Design")*

`Write your sub-field here.`

**Relevant IEEE Technical Society:** *(e.g., "IEEE Circuits and Systems Society", "IEEE Robotics and Automation Society")*

`Write the relevant society here.`

**Applicable IEEE Standard(s), if any:** *(e.g., IEEE 802.11 for WiFi, IEEE 754 for floating-point)*

`List applicable standards, or write "None directly applicable."`

---

## Objectives
> *[REQUIRED] List 3–6 specific, measurable objectives. Each objective should describe a concrete outcome, not an activity. Use the format: "To [action verb] [measurable outcome] by [method/means]."*

**Example format:**
- To implement a real-time FFT algorithm on an STM32 microcontroller achieving a processing latency of under 10 ms for a 1024-point sample.

1. Objective 1
2. Objective 2
3. Objective 3
4. *(add more as needed)*

---

## Methodology
> *[REQUIRED] Describe your technical approach in 300–500 words. Explain: what tools, software, hardware, and techniques you will use; how you will validate your design before building it; and the general flow from concept to final prototype. This section must justify your resource requests.*

**5.1 Design & Simulation Phase**

Describe what simulations you will run before touching hardware. List the software tools you will use (e.g., MATLAB, Simulink, Proteus, KiCad, LTspice, Quartus, ModelSim, Python, etc.).

**5.2 Hardware Implementation Phase**

Describe the hardware you will build. What circuits, PCBs, mechanical components, or embedded systems will be developed?

**5.3 Testing & Validation Phase**

Describe how you will verify that your system meets the success metrics. What tests will you run? What instruments will you use?

---

## Work Breakdown Structure (WBS)
> *[REQUIRED] This table is parsed by the platform to generate your milestone tracker. Do not change the column names. Use the status values exactly as shown: `Not Started`, `In Progress`, `Complete`, `Delayed`.*

| Milestone # | Milestone Name | Key Deliverables | Start Date | End Date | Status |
|---|---|---|---|---|---|
| M1 | Design & Simulation | Completed schematic, simulation results | YYYY-MM-DD | YYYY-MM-DD | Not Started |
| M2 | Component Procurement | All components sourced and received | YYYY-MM-DD | YYYY-MM-DD | Not Started |
| M3 | Prototype v1 Build | Assembled prototype on breadboard/PCB | YYYY-MM-DD | YYYY-MM-DD | Not Started |
| M4 | Testing & Debugging | Test log, identified issues | YYYY-MM-DD | YYYY-MM-DD | Not Started |
| M5 | Final Build & Documentation | Final working prototype + milestone report | YYYY-MM-DD | YYYY-MM-DD | Not Started |

> Add or remove milestones as needed. Most projects should have 4–6 milestones. Very short projects (under 4 weeks) may have 3. All projects must include a final documentation milestone.

**Estimated Total Duration:** `X weeks`

---

## Resource Management Matrix
> *[REQUIRED] This table is parsed by the platform to generate your resource request and the resource dashboard. List every piece of university equipment you plan to use. Be specific — "CNC machine in Electronics Lab" not just "CNC." Estimated hours must be realistic; Lab Technicians will review this.*

| Resource | Lab / Location | Estimated Hours | Purpose in Project | Required From | Required Until |
|---|---|---|---|---|---|
| e.g., Oscilloscope (2-channel) | Electronics Lab | 10 hrs | Signal waveform verification | YYYY-MM-DD | YYYY-MM-DD |
| e.g., FPGA Development Board (Basys 3) | DLD Lab | 20 hrs | Hardware implementation of FSM | YYYY-MM-DD | YYYY-MM-DD |
| | | | | | |

> If you need access to the Lathe, Drill Press, Milling Machine, or PCB CNC, you must also complete the relevant Safety Training Module (Schedule A of the Terms & Conditions) before your first session. Confirm below:

- [ ] I have read Schedule A of the Terms & Conditions and will complete all required safety training before first use of listed Tier 2/3 equipment.

---

## Risk Assessment
> *[RECOMMENDED] Identify the 3–5 most significant risks to your project's success and describe your mitigation strategy for each. Think about: equipment availability, component sourcing, technical complexity, time constraints, and safety.*

| Risk | Likelihood (H/M/L) | Impact (H/M/L) | Mitigation Strategy |
|---|---|---|---|
| e.g., CNC machine is booked during critical phase | M | H | Schedule sessions 2 weeks in advance; identify an off-campus PCB fabrication backup. |
| e.g., Specific IC not available locally | M | M | Order from LCSC/Digikey with 2-week buffer before hardware phase begins. |
| | | | |

---

## Success Metrics
> *[REQUIRED] Define 3–6 quantitative metrics that determine whether your project is successful. Every metric must be measurable and specific. Vague metrics like "the system should work well" are not acceptable.*

**Example format:**
- Signal reconstruction error (MSE) of the DSP filter must be ≤ 0.5% compared to the theoretical response.

| Metric | Target Value | Measurement Method |
|---|---|---|
| 1. | | |
| 2. | | |
| 3. | | |
| 4. *(add more as needed)* | | |

---

## Data & Documentation Plan
> *[RECOMMENDED] Describe what data you will collect and record throughout the project, and how you will store it. This helps establish scientific rigor and makes your final report much easier to write.*

**Data to be recorded:**
- *(e.g., Oscilloscope screenshots at each test point, exported as .png)*
- *(e.g., Python-generated CSV of sensor readings at 1 Hz for 10-minute test runs)*
- *(e.g., Photos of each build stage)*
- *(e.g., Version-controlled code on GitHub — link to repo)*

**Update cadence commitment:** I understand that I am required to post at least one project update every two weeks on the OIISP portal.

- [ ] Confirmed.

---

## Budget Estimate
> *[RECOMMENDED] Provide a rough breakdown of anticipated out-of-pocket expenses. This is for planning purposes only and does not need to be exact. It demonstrates that you have seriously thought through feasibility.*

| Item | Source | Estimated Cost (PKR) |
|---|---|---|
| e.g., ESP32 Development Board (×2) | Local market / AliExpress | 2,400 |
| e.g., Resistors, Capacitors (assorted kit) | University Lab (at cost) | 500 |
| | | |
| | **Total Estimated:** | |

---

## References
> *[RECOMMENDED] Cite any papers, datasheets, textbooks, or IEEE articles that informed your project design. Use IEEE citation format.*

[1] A. Author, "Title of paper," *IEEE Transactions on [Journal Name]*, vol. X, no. X, pp. XX–XX, Month Year.  
[2] Component Manufacturer, *[Part Name] Datasheet*, Rev. X.X, Year. [Online]. Available: URL.

---

## Declaration
> *[REQUIRED] Read carefully and check all boxes before submitting.*

- [ ] I confirm that the information in this proposal is accurate and complete.
- [ ] I have read and agree to the OIISP Terms & Conditions in full.
- [ ] I confirm that all listed team members are aware of this proposal and have agreed to participate.
- [ ] I understand that approval of this proposal grants access only to the resources explicitly listed in the Resource Management Matrix.
- [ ] I understand that I must post updates at least once every two weeks to maintain active project status and lab access.
- [ ] I accept that all project content posted on the OIISP platform will be publicly visible.

---

## For Office Use Only

> *Do not fill in this section. It is completed by the OIISP Admin upon review.*

| Field | Value |
|---|---|
| Proposal Received | |
| Assigned Project ID | |
| Review Outcome | Approved / Rejected / Revisions Required |
| Review Notes | |
| Admin Signature | |
| Date of Decision | |
| Resource Request Sent To | |
| Lab Access Activated | |

---

*OIISP — Habib University | Questions? Contact the OIISP Administrator through the platform or the designated Teams channel.*
