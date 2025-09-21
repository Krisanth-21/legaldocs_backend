# Document Analyzer API

FastAPI backend for AI-powered document analysis using Google Gemini.

## Features

- Upload PDF and DOCX documents
- AI-powered analysis using Google Gemini
- Extract key clauses, risks, and recommendations
- RESTful API with automatic documentation

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variable:
```bash
export GEMINI_API_KEY=your_api_key_here
```

3. Run the server:
```bash
uvicorn main:app --reload
```

## Deployment on Render

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set the build command: `pip install -r requirements.txt`
4. Set the start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variable: `GEMINI_API_KEY`

## API Endpoints

- `POST /analyze/` - Upload and analyze a document
- `GET /` - API documentation

## Environment Variables

- `GEMINI_API_KEY` - Your Google Gemini API key
- `PORT` - Port number (automatically set by Render)