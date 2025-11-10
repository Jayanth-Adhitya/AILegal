# Git & Docker Compatibility for Chatbot Features

## ✅ What Works Automatically

### Git
- **All new files are trackable** - No Git configuration changes needed
- **.gitignore is already configured** - Excludes .env, data files, etc.
- **New components ready to commit**:
  - `src/services/groq_service.py`
  - `frontend/components/chatbot/*`
  - Updated `requirements.txt` with groq==0.33.0
  - Updated API endpoints in `src/api.py`

### Docker
- **Dockerfile.backend** - Already copies requirements.txt, so groq==0.33.0 is included
- **Frontend Dockerfile** - No changes needed (uses native Web APIs for voice)
- **Volume mounts** - Data directories already configured

## ⚠️ Updates Applied

### 1. Docker Compose Environment Variables
**Updated `docker-compose.yml`** to include:
```yaml
environment:
  - GROQ_API_KEY=${GROQ_API_KEY}  # Added for TTS/STT
```

### 2. Environment Example File
**Updated `.env.example`** to include:
```env
# Groq API Configuration (for TTS and STT)
GROQ_API_KEY=your_groq_api_key_here
```

## 📋 Deployment Checklist

### For Local Development
✅ All features work with current setup after running:
```bash
pip install -r requirements.txt
npm install  # in frontend directory
```

### For Docker Deployment

1. **Before building Docker images:**
   ```bash
   # Make sure .env has GROQ_API_KEY
   echo "GROQ_API_KEY=your_actual_key_here" >> .env
   ```

2. **Build and run:**
   ```bash
   docker-compose build
   docker-compose up
   ```

3. **Verify services:**
   ```bash
   # Check backend health
   curl http://localhost:8080/health

   # Check voice features
   curl http://localhost:8080/api/voice/voices
   ```

### For Production Deployment

1. **Environment Variables** - Set in your deployment platform:
   - `GOOGLE_API_KEY` (existing)
   - `GROQ_API_KEY` (new) ⚠️

2. **Optional: Disable Voice Features**
   If you don't have a Groq API key, the app still works:
   - Chat functions normally (text only)
   - TTS/STT buttons will show "Voice features unavailable"

## 🔄 Version Control

### To commit all changes:
```bash
# Add all new and modified files
git add .

# Commit with descriptive message
git commit -m "feat: Add AI chatbot with TTS/STT voice capabilities

- Integrated Groq API for speech synthesis and recognition
- Added conversational chatbot for contract analysis Q&A
- Implemented floating chat UI with voice recording
- Added RAG-based context retrieval for policy questions"

# Push to repository
git push origin main
```

### Files to Review Before Commit:
- ✅ `.env` should NOT be committed (already in .gitignore)
- ✅ `requirements.txt` includes groq==0.33.0
- ✅ `docker-compose.yml` includes GROQ_API_KEY
- ✅ `.env.example` documents GROQ_API_KEY

## 🚀 Quick Start After Clone

For someone cloning your repo:

```bash
# Clone repository
git clone [your-repo-url]
cd Legal-Agent

# Setup environment
cp .env.example .env
# Edit .env and add your API keys

# Option 1: Docker
docker-compose up

# Option 2: Local
pip install -r requirements.txt
cd frontend && npm install
python -m uvicorn src.api:app --reload  # Terminal 1
cd frontend && npm run dev               # Terminal 2
```

## 🔧 Troubleshooting

### Docker Issues:
- **"GROQ_API_KEY not found"** - Add to .env file
- **Voice features not working** - Check GROQ_API_KEY is valid
- **Port conflicts** - Modify ports in docker-compose.yml

### Git Issues:
- **Large file warnings** - ChromaDB data should be in .gitignore
- **Merge conflicts in .env** - Use .env.example as reference

## 📝 Summary

**The chatbot features are fully compatible with your existing Git and Docker setup!**

Only minor updates were needed:
1. ✅ Added GROQ_API_KEY to docker-compose.yml
2. ✅ Updated .env.example for documentation

Everything else works out of the box!