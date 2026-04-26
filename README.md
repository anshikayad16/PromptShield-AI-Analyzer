# ShieldAI Analyzer

ShieldAI Analyzer is a browser extension designed to detect and prevent malicious prompts and prompt injection attacks in real time. It acts as a security layer between users and large language models (LLMs) such as ChatGPT, Gemini, and Claude, ensuring safer and more reliable AI interactions.

---

## Overview

With the rapid adoption of AI tools, prompt injection and jailbreak attacks have become a major concern. Malicious prompts can manipulate AI behavior, override instructions, or expose sensitive information.

ShieldAI Analyzer solves this problem by analyzing user prompts before they are submitted and classifying them as safe or harmful using a hybrid detection system.

---

## Features

- Real-time prompt scanning  
- Prompt injection detection  
- AI-based threat classification  
- Safe / Warning / Blocked output  
- Browser-level protection  
- Logs and analytics tracking  
- Lightweight and fast performance  
- Privacy-focused (local processing)

---

## Tech Stack

### Frontend
- Chrome Extension (HTML, CSS, JavaScript)

### Backend
- Flask (Python)
- Flask-CORS

### Database
- SQLite

### AI Engine
- Machine Learning model for prompt classification  
- Rule-based detection for known attack patterns  

---

## Architecture

The system follows a client-server model:

1. User enters a prompt in the browser  
2. Chrome extension captures the prompt  
3. Prompt is sent to Flask API  
4. Backend analyzes using AI detection engine  
5. Risk score is generated  
6. Response returned to extension  
7. Action taken (Allow / Warn / Block)  

---

## How It Works

- The extension monitors input fields on supported AI platforms  
- Before submission, the prompt is scanned  
- The backend evaluates the prompt for:
  - Injection patterns  
  - Malicious intent  
  - Suspicious instructions  
- Based on the analysis, the system:
  - Allows safe prompts  
  - Warns for medium-risk prompts  
  - Blocks high-risk prompts  

---

## Installation

### Backend Setup

```bash
cd project
pip install -r requirements.txt
python app.py
