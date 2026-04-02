# DocForge Hub

> AI-powered enterprise document generation system. Generate, manage and publish industry-ready documents using LLM prompting, structured templates and Notion as a living document library.

---

## 1. What It Is

Enterprise teams waste hundreds of hours writing SOPs, policies, handbooks and compliance documents from scratch. DocForge Hub solves this by letting any admin describe their company once, answer a structured set of questions section by section, and receive a fully generated, professionally formatted enterprise document in minutes.

The system supports 10 departments, 100+ document templates across industries like SaaS, Telecom, Healthcare, Finance and more. Every document is versioned, scored for quality, exportable as PDF or DOCX, and publishable directly to a Notion database with full metadata.

---

## 2. Architecture

```
User (Streamlit UI)
       |
       v
FastAPI Backend  <-->  PostgreSQL (documents, templates, sections, versions)
       |
       |---> LangChain + Azure OpenAI (generation, scoring, suggestions, chat)
       |---> Redis (caching, rate limiting, job tracking, deduplication)
       |---> Notion API (publish documents with metadata)
       |---> ReportLab + python-docx (PDF and DOCX export)
```

- **Streamlit** serves 4 pages: Dashboard, Generator (4-step flow), Library, Notion
- **FastAPI** exposes 13 modular route files, each handling one domain
- **LangChain** orchestrates all LLM calls with PromptTemplates, memory and retry logic
- **Redis** handles generation job tracking, deduplication, rate limiting and response caching
- **PostgreSQL** stores all documents, sections, versions, company context and quality scores
- **Notion** acts as the external document store and publishing target

---

## 3. Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI |
| LLM Orchestration | LangChain + Azure OpenAI |
| Database | PostgreSQL |
| Caching and Rate Limiting | Redis |
| Document Export | ReportLab (PDF), python-docx (DOCX) |
| External Publishing | Notion API |
| Validation | Pydantic |
| API Docs | Swagger / OpenAPI (auto-generated) |
| Package Manager | uv (Python 3.10) |
| Version Control | Git with feature branch workflow |

---

## 4. Setup and Run

### Prerequisites

- Python 3.10+
- PostgreSQL running locally
- Redis running locally
- Azure OpenAI account with a deployed model
- Notion account with an integration token and database

### Clone the repository

```bash
git clone https://github.com/riteshturabit/Docforge_Hub.git
cd Docforge_Hub
```

### Create virtual environment

```bash
python -m venv DocForge_Hub
source DocForge_Hub/bin/activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Environment variables

Create a `.env` file in the root directory:

```env
# Azure OpenAI
AZURE_OPENAI_LLM_KEY=your_azure_openai_key
AZURE_LLM_ENDPOINT=your_azure_endpoint
AZURE_LLM_API_VERSION=2024-02-01
AZURE_LLM_DEPLOYMENT_41_MINI=your_deployment_name

# Notion
NOTION_TOKEN=your_notion_integration_token
NOTION_DB_ID=your_notion_database_id

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# PostgreSQL
DB_HOST=localhost
DB_NAME=DocForge_Hub
DB_USER=postgres
DB_PASSWORD=your_db_password
DB_PORT=5432
```

### Database setup

```bash
# Create the database
psql -U postgres -c "CREATE DATABASE DocForge_Hub;"

# Run all schema files in order
psql -U postgres -d DocForge_Hub -f database/schema/01_departments.sql
psql -U postgres -d DocForge_Hub -f database/schema/02_document_types.sql
psql -U postgres -d DocForge_Hub -f database/schema/03_document_templates.sql
psql -U postgres -d DocForge_Hub -f database/schema/04_template_sections.sql
psql -U postgres -d DocForge_Hub -f database/schema/05_template_questions.sql
psql -U postgres -d DocForge_Hub -f database/schema/06_company_context.sql
psql -U postgres -d DocForge_Hub -f database/schema/07_documents.sql
psql -U postgres -d DocForge_Hub -f database/schema/08_document_sections.sql
psql -U postgres -d DocForge_Hub -f database/schema/09_seed_data.sql
```

### Start Redis

```bash
sudo service redis-server start
```

### Run the backend

```bash
uvicorn backend.main:app --reload
```

### Run the frontend

```bash
cd frontend
streamlit run app.py
```

### API documentation

Once the backend is running, open:

```
http://localhost:8000/docs
```

This gives you the full interactive Swagger UI for all 13 route groups.

---

## 5. How to Use

### Main flow

**Dashboard**
- View document metrics (total, published, drafts)
- Use Smart Template Suggestions: describe your company and get AI-recommended templates
- Quick access to Generator, Library and Notion pages

**Generator (4-step flow)**

Step 1 - Select department and template from 100+ options

Step 2 - Fill in company information (name, location, size, stage, mission, vision)

Step 3 - Answer AI-generated questions section by section (2-3 questions per section)

Step 4 - Preview the generated document, view quality score, download PDF or DOCX, publish to Notion, view version history per section and chat with the document using AI

**Library**
- Browse all generated documents filtered by department, type or publish status
- Download any document as PDF or DOCX
- Publish unpublished documents to Notion
- View quality score badge on each document card

**Notion**
- View all documents published to Notion
- Direct link to each Notion page

### Key URLs

| URL | Description |
|---|---|
| `http://localhost:8501` | Streamlit frontend |
| `http://localhost:8000/docs` | Swagger API docs |
| `http://localhost:8000/health` | API health check |
| `http://localhost:8000/job/{job_id}` | Check generation job status |

### Supported departments and document types

| Department | Example Templates |
|---|---|
| HR | Employee Handbook, Leave Policy, Code of Conduct |
| Engineering | API Documentation, SOP, Incident Response Plan |
| Finance | Budget Policy, Expense Policy, Audit Report |
| Legal | Privacy Policy, Terms of Service, NDA |
| Marketing | Content Plan, Brand Guidelines, Campaign SOP |
| Operations | Business Continuity Plan, Vendor Policy |
| Product | PRD, Feature Spec, Roadmap Document |
| Security | Security Policy, Access Control SOP |
| Customer Success | Onboarding Guide, Escalation Policy |
| Compliance | GDPR Policy, ISO Checklist, Risk Register |

---

## 6. Limits and Next Steps

### Current limits

- Document generation requires Azure OpenAI — no fallback to other LLM providers yet
- Notion publishing is one-way only — edits in Notion are not synced back to DocForge
- Multi-language document generation is not supported yet — English only
- Docker setup not yet included — requires manual local environment setup
- No user authentication — single admin mode only, no multi-user support

### Next steps

- Add Docker support for one-command local run with all services
- Add user authentication and role-based access (admin, viewer, editor)
- Support multiple LLM providers (OpenAI, Anthropic, Gemini) with fallback
- Add multi-language document generation
- Two-way Notion sync — pull edits back from Notion into DocForge
- Add email or Slack alerts for document review reminders
- Postman collection for full API testing coverage
