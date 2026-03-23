import requests

BASE_URL = "http://localhost:8000"

# Departments
def get_departments():
    res = requests.get(f"{BASE_URL}/departments")
    return res.json().get("departments", [])


# Templates
def get_templates(department_id: int):
    res = requests.get(f"{BASE_URL}/templates/{department_id}")
    return res.json().get("templates", [])


# Sections
def get_sections(template_id: int):
    res = requests.get(f"{BASE_URL}/sections/{template_id}")
    return res.json().get("sections", [])


# Company Context 
def save_company_context(data: dict):
    res = requests.post(f"{BASE_URL}/company-context", json=data)
    return res.json()

def get_company_context(company_id: int):
    res = requests.get(f"{BASE_URL}/company-context/{company_id}")
    return res.json()


# Document 
def create_document(template_id: int, company_id: int):
    res = requests.post(
        f"{BASE_URL}/create-document",
        params={"template_id": template_id, "company_id": company_id}
    )
    return res.json()

def get_document(document_id: str):
    res = requests.get(f"{BASE_URL}/document/{document_id}")
    return res.json()

def get_all_documents(department_id: int = None):
    params = {}
    if department_id:
        params["department_id"] = department_id
    res = requests.get(f"{BASE_URL}/documents", params=params)
    return res.json()


# Questions 
def generate_questions(template_id: int):
    res = requests.post(
        f"{BASE_URL}/generate_questions",
        params={"template_id": template_id}
    )
    return res.json()

def get_next_questions(document_id: str, section_order: int):
    res = requests.get(
        f"{BASE_URL}/next_questions",
        params={"document_id": document_id, "section_order": section_order}
    )
    return res.json()


# Generate Section 
def generate_section(document_id: str, section_order: int, answers: list):
    payload = {
        "document_id": document_id,
        "section_order": section_order,
        "answers": answers
    }
    res = requests.post(f"{BASE_URL}/generate_section", json=payload)
    return res.json()


# Progress
def get_progress(document_id: str):
    res = requests.get(f"{BASE_URL}/progress/{document_id}")
    return res.json()


# Enhance
def enhance_section(document_id: str, section_order: int, action: str, custom_instruction: str = ""):
    payload = {
        "document_id": document_id,
        "section_order": section_order,
        "action": action,
        "custom_instruction": custom_instruction
    }
    res = requests.post(f"{BASE_URL}/enhance_section", json=payload)
    return res.json()

def save_enhanced_section(document_id: str, section_order: int, content: str):
    payload = {
        "document_id": document_id,
        "section_order": section_order,
        "content": content
    }
    res = requests.post(f"{BASE_URL}/save_enhanced_section", json=payload)
    return res.json()


# Download 
def get_pdf_url(document_id: str):
    return f"{BASE_URL}/download/pdf/{document_id}"

def get_docx_url(document_id: str):
    return f"{BASE_URL}/download/docx/{document_id}"


# Notion 
def push_to_notion(document_id: str):
    res = requests.post(
        f"{BASE_URL}/push_to_notion",
        params={"document_id": document_id}
    )
    return res.json()