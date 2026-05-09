# Integration Specification
## Open Innovation & Independent Study Platform (OIISP)
### Habib University — Engineering & Computer Science Division

**Document Version:** 1.0  
**Status:** Draft — Technical Implementation Guide  
**Audience:** Developer / Platform Maintainer  
**Last Revised:** May 2026

---

## 1. Overview

This document describes the full integration architecture of the OIISP platform. It covers three primary integration concerns:

1. **The Markdown Ingest Pipeline** — How an uploaded `.md` proposal file becomes a structured project entry in the database and on the leaderboard.
2. **The Microsoft Teams Notification Engine** — How platform events are pushed to the university Teams channel automatically.
3. **The Auth Layer** — How students and faculty authenticate using existing Habib University credentials.

The guiding constraint for all integrations is **zero new infrastructure dependency**. Every system here either runs on the same self-hosted server as the platform, or connects to systems the university already operates (Microsoft 365, Azure AD).

---

## 2. System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        OIISP PLATFORM SERVER                         │
│                                                                      │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐   │
│  │  Next.js     │    │  Node.js API     │    │   PostgreSQL DB  │   │
│  │  Frontend    │◄──►│  /api/*          │◄──►│  (Projects,      │   │
│  │  (SSR/Static)│    │                  │    │  Milestones,     │   │
│  └──────────────┘    └────────┬─────────┘    │  Endorsements,   │   │
│                               │              │  Users, Logs)    │   │
│                        ┌──────┴──────┐       └──────────────────┘   │
│                        │  Services   │                               │
│                        │  Layer      │       ┌──────────────────┐   │
│                        │             │       │  MinIO (S3)      │   │
│                        │ ┌─────────┐ │◄─────►│  File Storage    │   │
│                        │ │MD Parser│ │       │  (.md, images,   │   │
│                        │ └─────────┘ │       │  reports, CSVs)  │   │
│                        │ ┌─────────┐ │       └──────────────────┘   │
│                        │ │Teams    │ │                               │
│                        │ │Webhook  │ │                               │
│                        │ │Service  │ │                               │
│                        │ └────┬────┘ │                               │
│                        └──────┼──────┘                               │
└───────────────────────────────┼──────────────────────────────────────┘
                                │
                    ────────────┼────────────────
                    External    │   Integrations
                    ────────────┼────────────────
                                │
          ┌─────────────────────┼───────────────────────┐
          │                     │                       │
          ▼                     ▼                       ▼
  ┌───────────────┐   ┌──────────────────┐   ┌──────────────────┐
  │  Microsoft    │   │  Azure Active    │   │  (Future)        │
  │  Teams        │   │  Directory       │   │  GitHub API      │
  │  Incoming     │   │  (Habib SSO)     │   │  (Code commit    │
  │  Webhook      │   │                  │   │  integration)    │
  └───────────────┘   └──────────────────┘   └──────────────────┘
```

---

## 3. The Markdown Ingest Pipeline

### 3.1 Purpose

When a student uploads a `proposal.md` file, the platform must:
1. Parse the file and extract structured data from each section.
2. Validate that all required sections are present and non-empty.
3. Store the raw file.
4. Create a database record for the project.
5. Pre-populate the milestone tracker from the WBS table.
6. Pre-populate the resource request queue from the Resource Management Matrix.
7. Assign a project slug and queue the project for admin review.

### 3.2 Parsing Strategy

The parser uses `gray-matter` for YAML front-matter and `remark` with `remark-parse` for Markdown AST traversal.

Each section is identified by its **exact H2 heading text** (case-insensitive). The H1 heading at the top of the document maps to the project title.

**Required section map:**

```javascript
const REQUIRED_SECTIONS = {
  'project-title':          { level: 1, dbField: 'title' },
  'team-members':           { level: 2, dbField: 'team', type: 'table' },
  'abstract':               { level: 2, dbField: 'abstract' },
  'problem-statement':      { level: 2, dbField: 'problem_statement' },
  'domain--ieee-alignment': { level: 2, dbField: 'domain_data', type: 'mixed' },
  'objectives':             { level: 2, dbField: 'objectives', type: 'list' },
  'methodology':            { level: 2, dbField: 'methodology' },
  'work-breakdown-structure-wbs': { level: 2, dbField: 'milestones', type: 'table' },
  'resource-management-matrix':   { level: 2, dbField: 'resources', type: 'table' },
  'success-metrics':        { level: 2, dbField: 'success_metrics', type: 'table' },
  'declaration':            { level: 2, dbField: 'declaration_checked', type: 'checkboxes' },
};
```

**Heading-to-slug conversion:** All heading text is lowercased, spaces replaced with hyphens, special characters removed. Example: `"Work Breakdown Structure (WBS)"` → `"work-breakdown-structure-wbs"`.

### 3.3 Parser Implementation (Node.js)

```javascript
// services/proposalParser.js
import matter from 'gray-matter';
import { unified } from 'unified';
import remarkParse from 'remark-parse';
import { visit } from 'unist-util-visit';

export async function parseProposal(markdownContent) {
  const { content } = matter(markdownContent);
  const tree = unified().use(remarkParse).parse(content);
  
  const sections = {};
  let currentHeading = null;
  let currentLevel = null;
  let currentNodes = [];

  visit(tree, (node) => {
    if (node.type === 'heading') {
      // Save previous section
      if (currentHeading) {
        sections[currentHeading] = {
          level: currentLevel,
          nodes: [...currentNodes]
        };
      }
      currentHeading = headingToSlug(node.children[0]?.value || '');
      currentLevel = node.depth;
      currentNodes = [];
    } else if (currentHeading) {
      currentNodes.push(node);
    }
  });

  // Save last section
  if (currentHeading) {
    sections[currentHeading] = { level: currentLevel, nodes: currentNodes };
  }

  return {
    title: extractTitle(tree),
    sections,
    validation: validateSections(sections),
  };
}

function headingToSlug(text) {
  return text.toLowerCase().replace(/[^a-z0-9\s-]/g, '').replace(/\s+/g, '-');
}
```

### 3.4 Table Parser (for WBS and Resource Matrix)

Markdown tables in the WBS and Resource Matrix sections are parsed into structured arrays:

```javascript
// services/tableParser.js
export function parseMarkdownTable(tableNode) {
  const rows = tableNode.children; // remark AST: table > tableRow > tableCell
  const headers = rows[0].children.map(cell =>
    cell.children.map(n => n.value || '').join('').trim()
  );
  return rows.slice(1).map(row => {
    const cells = row.children.map(cell =>
      cell.children.map(n => n.value || '').join('').trim()
    );
    return Object.fromEntries(headers.map((h, i) => [h, cells[i] || '']));
  });
}
```

**WBS table → Milestone records:**

Each row in the WBS table becomes one milestone record in the `milestones` database table:

```sql
INSERT INTO milestones (project_id, number, name, deliverables, start_date, end_date, status)
VALUES ($1, $2, $3, $4, $5, $6, 'Not Started');
```

**Resource Matrix table → Resource request records:**

```sql
INSERT INTO resource_requests (project_id, resource_name, lab_location, estimated_hours, purpose, required_from, required_until, approved)
VALUES ($1, $2, $3, $4, $5, $6, $7, false);
```

### 3.5 Validation Rules

Validation runs before the proposal is saved. All failures are returned to the frontend for display to the student. The upload is **blocked** until all required-section validations pass.

```javascript
// services/proposalValidator.js
export function validateSections(sections) {
  const errors = [];
  const warnings = [];

  for (const [slug, config] of Object.entries(REQUIRED_SECTIONS)) {
    if (!sections[slug]) {
      errors.push({ section: slug, message: `Required section "${slug}" is missing.` });
      continue;
    }
    if (isEffectivelyEmpty(sections[slug].nodes)) {
      errors.push({ section: slug, message: `Required section "${slug}" has no content.` });
    }
  }

  // Abstract word count check
  const abstractWords = extractText(sections['abstract']?.nodes).split(/\s+/).length;
  if (abstractWords < 150) {
    errors.push({ section: 'abstract', message: `Abstract is too short (${abstractWords} words). Minimum: 150.` });
  }
  if (abstractWords > 350) {
    warnings.push({ section: 'abstract', message: `Abstract may be too long (${abstractWords} words). Target: 200–300.` });
  }

  // WBS: at least 3 milestones
  // Declaration: all checkboxes must be checked
  // Team: at least 1 member with all fields filled

  return { errors, warnings, valid: errors.length === 0 };
}
```

### 3.6 Proposal Ingest API Route

```javascript
// pages/api/proposals/submit.js (Next.js API Route)
// POST /api/proposals/submit
// Content-Type: multipart/form-data
// Body: { file: <.md file> }
// Auth: Required (Azure AD session)

export default async function handler(req, res) {
  if (req.method !== 'POST') return res.status(405).end();

  const session = await getServerSession(req, res, authOptions);
  if (!session) return res.status(401).json({ error: 'Unauthorized' });

  const { file } = await parseMultipartForm(req); // multer or formidable
  const content = file.buffer.toString('utf-8');

  const parsed = await parseProposal(content);
  if (!parsed.validation.valid) {
    return res.status(422).json({ errors: parsed.validation.errors });
  }

  // Store raw .md file in MinIO
  const fileKey = `proposals/${session.user.id}/${Date.now()}-proposal.md`;
  await minioClient.putObject('oiisp', fileKey, file.buffer);

  // Create project record in DB
  const project = await db.projects.create({
    title: parsed.title,
    abstract: extractText(parsed.sections['abstract'].nodes),
    problem_statement: extractText(parsed.sections['problem-statement'].nodes),
    domain: extractDomain(parsed.sections['domain--ieee-alignment']),
    methodology: extractText(parsed.sections['methodology'].nodes),
    status: 'pending_review',
    submitted_by: session.user.id,
    file_key: fileKey,
    slug: generateSlug(parsed.title),
  });

  // Create milestone records
  await createMilestones(project.id, parsed.sections);

  // Create resource request records
  await createResourceRequests(project.id, parsed.sections);

  // Notify admin via Teams
  await sendTeamsNotification('NEW_PROPOSAL', { project });

  return res.status(201).json({ projectId: project.id, slug: project.slug });
}
```

---

## 4. Microsoft Teams Integration

### 4.1 Architecture

The Teams integration uses a single **Incoming Webhook** on a dedicated, owner-only channel named `#OIISP — Innovation Feed`. The channel is configured so that **only the webhook bot can post** — students and faculty are members but cannot write messages. This keeps the feed clean and trustworthy.

### 4.2 Setting Up the Webhook

1. In Microsoft Teams, navigate to the `#OIISP — Innovation Feed` channel.
2. Click **⋯ (More options)** → **Connectors**.
3. Search for and configure **Incoming Webhook**.
4. Name it `OIISP Bot`, upload the university or OIISP logo.
5. Copy the generated webhook URL and store it as the environment variable `TEAMS_WEBHOOK_URL` on the server. **Never expose this URL publicly.**

### 4.3 Notification Events & Card Templates

The platform fires a Teams notification on the following events:

| Event | Trigger | Teams Card Type |
|---|---|---|
| `NEW_PROPOSAL` | A proposal is submitted and enters admin review | Info card — project title, team, domain, link |
| `PROPOSAL_APPROVED` | Admin approves a proposal | Success card — project live announcement |
| `MILESTONE_COMPLETE` | Student marks a milestone as Complete | Update card — project, milestone name, link to update |
| `FACULTY_ENDORSE` | Faculty posts an endorsement | Highlight card — faculty name, project, endorsement quote |
| `PROJECT_COMPLETE` | Final report submitted | Celebration card — project title, team, summary |
| `WEEKLY_DIGEST` | Every Monday at 09:00 | Summary card — all active projects, last week's activity |

### 4.4 Teams Card Format (Adaptive Card — JSON)

All notifications use Microsoft Adaptive Cards (v1.4) for rich display. Example for `PROPOSAL_APPROVED`:

```json
{
  "type": "message",
  "attachments": [
    {
      "contentType": "application/vnd.microsoft.card.adaptive",
      "content": {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
          {
            "type": "TextBlock",
            "size": "Medium",
            "weight": "Bolder",
            "text": "✅ New Project Approved"
          },
          {
            "type": "FactSet",
            "facts": [
              { "title": "Project", "value": "{{project.title}}" },
              { "title": "Team", "value": "{{project.team_names}}" },
              { "title": "Domain", "value": "{{project.domain}}" },
              { "title": "Duration", "value": "{{project.estimated_weeks}} weeks" }
            ]
          },
          {
            "type": "TextBlock",
            "text": "{{project.abstract_short}}",
            "wrap": true
          }
        ],
        "actions": [
          {
            "type": "Action.OpenUrl",
            "title": "View Project",
            "url": "https://oiisp.habib.edu.pk/projects/{{project.slug}}"
          }
        ]
      }
    }
  ]
}
```

### 4.5 Teams Notification Service (Node.js)

```javascript
// services/teamsNotifier.js
const TEAMS_WEBHOOK_URL = process.env.TEAMS_WEBHOOK_URL;

const CARD_TEMPLATES = {
  NEW_PROPOSAL: buildNewProposalCard,
  PROPOSAL_APPROVED: buildApprovedCard,
  MILESTONE_COMPLETE: buildMilestoneCard,
  FACULTY_ENDORSE: buildEndorsementCard,
  PROJECT_COMPLETE: buildCompletionCard,
  WEEKLY_DIGEST: buildWeeklyDigestCard,
};

export async function sendTeamsNotification(eventType, data) {
  const buildCard = CARD_TEMPLATES[eventType];
  if (!buildCard) throw new Error(`Unknown event type: ${eventType}`);

  const card = buildCard(data);

  const response = await fetch(TEAMS_WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(card),
  });

  if (!response.ok) {
    // Log failure but do NOT block the main operation
    console.error(`Teams notification failed for event ${eventType}:`, await response.text());
  }
}
```

> **Critical Design Principle:** Teams notification failures must **never** cause the main API operation to fail. Always run the notification in a non-blocking manner (`await` is fine but must be wrapped in its own try/catch). A student's proposal should not fail to submit because the Teams webhook is temporarily down.

### 4.6 Weekly Digest (Cron Job)

A scheduled job runs every Monday at 09:00 PKT to send a digest of the previous week's activity:

```javascript
// jobs/weeklyDigest.js — run via node-cron or system cron
import cron from 'node-cron';

cron.schedule('0 9 * * 1', async () => {
  const stats = await db.getWeeklyStats(); // custom query
  await sendTeamsNotification('WEEKLY_DIGEST', stats);
}, {
  timezone: 'Asia/Karachi'
});
```

The digest card includes:
- New proposals this week (count + names)
- Milestones completed
- New faculty endorsements
- Active project count
- A link to the leaderboard

---

## 5. Authentication (Azure AD / Microsoft SSO)

### 5.1 Strategy

Authentication uses **NextAuth.js** with the **Azure AD provider**, connecting to the same Microsoft 365 tenant that Habib University uses for email and Teams. Students and faculty log in with their `@habib.edu.pk` account — no new passwords, no new accounts.

### 5.2 NextAuth Configuration

```javascript
// pages/api/auth/[...nextauth].js
import NextAuth from 'next-auth';
import AzureADProvider from 'next-auth/providers/azure-ad';

export default NextAuth({
  providers: [
    AzureADProvider({
      clientId: process.env.AZURE_AD_CLIENT_ID,
      clientSecret: process.env.AZURE_AD_CLIENT_SECRET,
      tenantId: process.env.AZURE_AD_TENANT_ID, // Habib University tenant
    }),
  ],
  callbacks: {
    async session({ session, token }) {
      session.user.id = token.sub;
      session.user.role = await getUserRole(token.email); // 'student' | 'faculty' | 'admin' | 'technician'
      return session;
    },
  },
});
```

### 5.3 Azure AD App Registration (Required Setup)

A one-time setup by the IT administrator:

1. In Azure Portal → **App registrations** → **New registration**.
2. Name: `OIISP Platform`.
3. Supported account types: `Accounts in this organizational directory only (Habib University only)`.
4. Redirect URI: `https://oiisp.habib.edu.pk/api/auth/callback/azure-ad`.
5. Under **API permissions**: add `User.Read` (Microsoft Graph — Delegated).
6. Copy `Application (client) ID`, `Directory (tenant) ID`, and generate a `Client secret`. Store as environment variables.

### 5.4 Role Assignment

User roles are determined from the Azure AD user profile. A role lookup table in the database maps email addresses to roles:

```sql
CREATE TABLE user_roles (
  email       TEXT PRIMARY KEY,
  role        TEXT NOT NULL CHECK (role IN ('student', 'faculty', 'admin', 'technician')),
  created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

Initial population: the OIISP Admin imports the university's student and faculty roster.

---

## 6. Database Schema (Abbreviated)

```sql
-- Core tables

CREATE TABLE projects (
  id              SERIAL PRIMARY KEY,
  slug            TEXT UNIQUE NOT NULL,
  title           TEXT NOT NULL,
  abstract        TEXT,
  problem_statement TEXT,
  domain          TEXT,
  sub_field       TEXT,
  ieee_society    TEXT,
  methodology     TEXT,
  status          TEXT DEFAULT 'pending_review',
  submitted_by    TEXT REFERENCES user_roles(email),
  file_key        TEXT,          -- MinIO object key for raw .md
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  approved_at     TIMESTAMPTZ,
  completed_at    TIMESTAMPTZ
);

CREATE TABLE milestones (
  id              SERIAL PRIMARY KEY,
  project_id      INT REFERENCES projects(id) ON DELETE CASCADE,
  number          INT,
  name            TEXT,
  deliverables    TEXT,
  start_date      DATE,
  end_date        DATE,
  actual_end_date DATE,
  status          TEXT DEFAULT 'Not Started'
);

CREATE TABLE team_members (
  project_id  INT REFERENCES projects(id) ON DELETE CASCADE,
  email       TEXT REFERENCES user_roles(email),
  role        TEXT,
  PRIMARY KEY (project_id, email)
);

CREATE TABLE resource_requests (
  id              SERIAL PRIMARY KEY,
  project_id      INT REFERENCES projects(id) ON DELETE CASCADE,
  resource_name   TEXT,
  lab_location    TEXT,
  estimated_hours NUMERIC,
  purpose         TEXT,
  required_from   DATE,
  required_until  DATE,
  approved        BOOLEAN DEFAULT FALSE,
  approved_by     TEXT,
  approved_at     TIMESTAMPTZ
);

CREATE TABLE project_updates (
  id          SERIAL PRIMARY KEY,
  project_id  INT REFERENCES projects(id) ON DELETE CASCADE,
  posted_by   TEXT REFERENCES user_roles(email),
  update_type TEXT,   -- 'milestone' | 'photo' | 'data' | 'general'
  body        TEXT,
  file_keys   TEXT[], -- Array of MinIO keys for attached files
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE endorsements (
  id          SERIAL PRIMARY KEY,
  project_id  INT REFERENCES projects(id) ON DELETE CASCADE,
  faculty_email TEXT REFERENCES user_roles(email),
  type        TEXT CHECK (type IN ('star', 'vouch', 'endorse')),
  comment     TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (project_id, faculty_email, type)
);

CREATE TABLE lab_session_logs (
  id          SERIAL PRIMARY KEY,
  project_id  INT REFERENCES projects(id),
  student_email TEXT REFERENCES user_roles(email),
  resource_name TEXT,
  checked_in  TIMESTAMPTZ,
  checked_out TIMESTAMPTZ,
  notes       TEXT,
  technician_signoff TEXT
);
```

---

## 7. Environment Variables

All secrets are stored as environment variables and **never** committed to version control.

```bash
# .env.local (never commit this file)

# Microsoft / Azure AD
AZURE_AD_CLIENT_ID=
AZURE_AD_CLIENT_SECRET=
AZURE_AD_TENANT_ID=

# Teams Webhook
TEAMS_WEBHOOK_URL=

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/oiisp

# MinIO
MINIO_ENDPOINT=localhost
MINIO_PORT=9000
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
MINIO_BUCKET=oiisp

# App
NEXTAUTH_SECRET=
NEXTAUTH_URL=https://oiisp.habib.edu.pk
NEXT_PUBLIC_BASE_URL=https://oiisp.habib.edu.pk
```

---

## 8. Deployment (Pilot)

For the pilot phase, the entire stack runs on a single server using Docker Compose.

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "3000:3000"
    env_file: .env.local
    depends_on:
      - db
      - minio

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: oiisp
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - miniodata:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs

volumes:
  pgdata:
  miniodata:
```

---

## 9. Future Integrations (Post-Pilot Roadmap)

| Integration | Purpose | Complexity |
|---|---|---|
| **GitHub API** | Auto-pull latest commit message into project updates when a linked repo is updated | Low |
| **Power Automate** | Allow faculty who prefer Power Automate over direct Teams webhooks to subscribe to domain-tag triggers | Low |
| **Habib ERP / SIS** | Auto-verify student enrollment status at proposal time | Medium |
| **ORCID API** | Allow faculty to link their ORCID profile to their OIISP endorsements for academic credibility | Low |
| **DOI / Zenodo** | Archive completed final reports with a permanent DOI for academic citation | Medium |

---

*This document is maintained by the OIISP platform developer. For questions, contact the OIISP Administrator.*
