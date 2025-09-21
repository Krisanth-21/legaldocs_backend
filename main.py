from fastapi import FastAPI, UploadFile, File, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
import PyPDF2
import docx

app = FastAPI()

# Allow frontend to connect - more explicit CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://legaldocs-frontend.netlify.app",
        "*"
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Function to extract text from PDF
def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

# Function to extract text from Word (.docx)
def extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

import google.generativeai as genai

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY", "AIzaSyD16GBPxdHdFDkIyxi7iY_uzzi7-mKG5KE"))

def analyze_text(text: str) -> dict:
    try:
        # Try different model names that might be available
        model_names = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro', 'models/gemini-1.5-flash']
        model = None
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                break
            except:
                continue

        if not model:
            # List available models for debugging
            available_models = genai.list_models()
            model_list = [m.name for m in available_models if 'generateContent' in m.supported_generation_methods]
            if model_list:
                model = genai.GenerativeModel(model_list[0])
            else:
                raise Exception("No suitable models found")

        prompt = f"""Analyze the following document text and provide:
1. A brief summary (2-3 sentences)
2. Key clauses or important points (list 3-5 items)
3. Potential risks or concerns (list 2-4 items)
4. Recommended next steps (list 2-4 items)

Document text:
{text[:4000]}

Please provide a clear, structured analysis."""

        response = model.generate_content(prompt)

        # Parse the response and structure it
        response_text = response.text

        # Simple parsing to extract sections
        lines = response_text.split('\n')
        summary = ""
        key_clauses = []
        risks = []
        next_steps = []
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect sections
            if any(word in line.lower() for word in ['summary', 'overview']):
                current_section = 'summary'
                continue
            elif any(word in line.lower() for word in ['key', 'clause', 'point', 'important']):
                current_section = 'clauses'
                continue
            elif any(word in line.lower() for word in ['risk', 'concern', 'issue']):
                current_section = 'risks'
                continue
            elif any(word in line.lower() for word in ['next', 'step', 'recommend', 'action']):
                current_section = 'steps'
                continue

            # Add content to appropriate section
            if current_section == 'summary' and not summary:
                summary = line
            elif current_section == 'clauses' and (line.startswith('-') or line.startswith('•') or line.startswith('*') or line[0].isdigit()):
                key_clauses.append(line.lstrip('-•*0123456789. '))
            elif current_section == 'risks' and (line.startswith('-') or line.startswith('•') or line.startswith('*') or line[0].isdigit()):
                risks.append(line.lstrip('-•*0123456789. '))
            elif current_section == 'steps' and (line.startswith('-') or line.startswith('•') or line.startswith('*') or line[0].isdigit()):
                next_steps.append(line.lstrip('-•*0123456789. '))

        # Fallback if parsing didn't work well
        if not summary:
            summary = response_text[:200] + "..." if len(response_text) > 200 else response_text
        if not key_clauses:
            key_clauses = ["Document analysis completed successfully"]
        if not risks:
            risks = ["Please review the document carefully"]
        if not next_steps:
            next_steps = ["Review the analysis", "Consider professional consultation if needed"]

        return {
            "summary": summary,
            "key_clauses": key_clauses[:5],  # Limit to 5 items
            "risks": risks[:4],  # Limit to 4 items
            "next_steps": next_steps[:4]  # Limit to 4 items
        }

    except Exception as e:
        return {
            "summary": f"Error analyzing document: {str(e)}",
            "key_clauses": ["Analysis failed - please check your API key and internet connection"],
            "risks": ["Unable to process document with AI"],
            "next_steps": ["Verify Gemini API key is valid", "Check document format and try again"]
        }

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """<!DOCTYPE html>
<html>
<head>
    <title>Document Analyzer API</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .api-info { background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }
        .endpoint { background: #e9ecef; padding: 10px; border-radius: 3px; margin: 10px 0; }
        code { background: #f1f3f4; padding: 2px 4px; border-radius: 3px; }
    </style>
</head>
<body>
    <h1>📄 Document Analyzer API</h1>
    <p>FastAPI backend for AI-powered document analysis</p>
    
    <div class="api-info">
        <h2>Available Endpoints:</h2>
        <div class="endpoint">
            <strong>POST /analyze/</strong><br>
            Upload a document (PDF or DOCX) for AI analysis
        </div>
        <div class="endpoint">
            <strong>GET /</strong><br>
            This API documentation page
        </div>
    </div>
    
    <div class="api-info">
        <h2>Usage:</h2>
        <p>Send a POST request to <code>/analyze/</code> with a file in the request body.</p>
        <p>The API will return a JSON response with analysis results including summary, key clauses, risks, and next steps.</p>
    </div>
    
    <div class="api-info">
        <h2>Status:</h2>
        <p>✅ API is running and ready to analyze documents</p>
    </div>
</body>
</html>"""

@app.options("/analyze/")
async def analyze_options(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return {"message": "OK"}

@app.post("/analyze/")
async def analyze_document(file: UploadFile = File(...), response: Response = None):
    # Add explicit CORS headers
    if response:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Save uploaded file
    with open(file_path, "wb") as out_file:
        out_file.write(await file.read())
    
    # Extract text based on file type
    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif file.filename.endswith(".docx"):
        text = extract_text_from_docx(file_path)
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    
    # Run analysis
    result = analyze_text(text)
    
    return {"filename": file.filename, "analysis": result}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))