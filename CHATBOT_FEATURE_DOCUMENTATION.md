# Chatbot Feature Implementation Documentation

## Overview
Successfully implemented an AI-powered chatbot with voice capabilities (TTS and STT) for the Legal Agent contract analysis application. The chatbot appears as a floating button on the results page and helps users understand their contract analysis results.

## Features Implemented

### 1. **Backend Implementation**

#### Voice Services (Groq Integration)
- **Location**: `src/services/groq_service.py`
- **Features**:
  - Text-to-Speech using Groq PlayAI TTS
  - Speech-to-Text using Groq Whisper
  - Support for multiple voices (19 English, 4 Arabic)
  - Error handling and validation

#### API Endpoints
- **Location**: `src/api.py` (lines 701-953)

##### Chat Endpoint
- **POST** `/api/chat/{job_id}` - Server-Sent Events (SSE) streaming chat
- Uses existing Gemini LLM for responses
- RAG integration for policy retrieval
- Context-aware responses based on analysis results

##### Voice Endpoints
- **POST** `/api/voice/synthesize` - Text-to-Speech conversion
- **POST** `/api/voice/transcribe` - Speech-to-Text conversion
- **GET** `/api/voice/voices` - Get available voices

#### Chatbot Prompts
- **Location**: `src/core/prompts.py` (lines 218-280)
- **Templates**:
  - `CHATBOT_PROMPT` - Main chatbot system prompt
  - `CHATBOT_POLICY_SEARCH_PROMPT` - Policy retrieval prompt

### 2. **Frontend Implementation**

#### Components Created
All components are located in `frontend/components/chatbot/`:

1. **ChatbotFloatingButton.tsx**
   - Floating button in bottom-right corner
   - Toggle chat panel open/close
   - Clean animations

2. **ChatPanel.tsx**
   - Main chat interface (400x600px)
   - Real-time SSE streaming
   - Message history management
   - Voice input/output controls

3. **ChatMessage.tsx**
   - Message bubble component
   - User/Assistant differentiation
   - Timestamp display
   - TTS playback button

4. **VoiceRecorder.tsx**
   - Microphone recording interface
   - Visual recording feedback
   - 60-second auto-stop
   - WebM audio format

5. **AudioPlayer.tsx**
   - Audio playback controls
   - Progress bar
   - Volume controls
   - Play/pause functionality

#### API Client Methods
- **Location**: `frontend/lib/api.ts` (lines 175-263)
- Added `chatApi` and `voiceApi` objects with all necessary methods

#### TypeScript Types
- **Location**: `frontend/lib/types.ts` (lines 101-143)
- Added comprehensive types for chat and voice features

#### Integration
- **Location**: `frontend/app/results/[id]/page.tsx`
- Chatbot button appears when analysis is completed
- Automatically receives job ID for context

## Configuration Required

### 1. Backend Setup

#### Install Dependencies
```bash
cd /path/to/Legal Agent
pip install -r requirements.txt
```

#### Environment Variables
Add to `.env` file:
```env
GROQ_API_KEY=your_actual_groq_api_key_here
```

**Get your Groq API key from**: https://console.groq.com/keys

### 2. Frontend Setup

#### Install Dependencies
```bash
cd frontend
npm install
```

## How to Test

### 1. Start the Backend
```bash
cd /path/to/Legal Agent
python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start the Frontend
```bash
cd frontend
npm run dev
```

### 3. Testing Steps

1. **Upload and Analyze a Contract**
   - Navigate to http://localhost:3000
   - Upload a contract for analysis
   - Wait for analysis to complete

2. **Access Results Page**
   - Go to the results page after analysis
   - You should see a blue chat button in the bottom-right corner

3. **Test Text Chat**
   - Click the chat button to open the panel
   - Ask questions like:
     - "What are the main compliance issues?"
     - "Explain the liability clause problems"
     - "What policies were violated?"
     - "What's the overall risk level?"

4. **Test Voice Input (STT)**
   - Click the microphone button
   - Allow microphone permissions
   - Speak your question
   - Button will pulse red while recording
   - Click again to stop (or wait 60 seconds)
   - Transcribed text appears in input field

5. **Test Voice Output (TTS)**
   - Hover over assistant messages
   - Click the speaker icon that appears
   - Audio will play the message content

## Architecture Details

### Chat Flow
1. User sends message → Frontend
2. Frontend calls `/api/chat/{job_id}` with SSE
3. Backend loads analysis results for context
4. If policy question detected → RAG retrieval from ChromaDB
5. Gemini LLM generates response with context
6. Response streams back via SSE
7. Frontend displays in real-time

### Voice Flow (STT)
1. User clicks microphone → Browser MediaRecorder API
2. Records audio as WebM/Opus
3. Sends to `/api/voice/transcribe`
4. Groq Whisper transcribes audio
5. Text returned to frontend

### Voice Flow (TTS)
1. User clicks speaker icon on message
2. Frontend calls `/api/voice/synthesize`
3. Groq PlayAI generates WAV audio
4. Audio streams back to frontend
5. HTML5 Audio API plays the audio

## Key Features

### Context Awareness
- Chatbot has full access to:
  - Contract analysis results
  - Clause-by-clause compliance status
  - Policy violations and citations
  - Risk assessments
  - Redline suggestions

### RAG Integration
- Automatically detects policy-related questions
- Queries ChromaDB vector store
- Retrieves relevant policies
- Includes citations in responses

### Voice Capabilities
- **TTS**: 19 English voices, natural speech
- **STT**: Fast transcription with Whisper
- **Format Support**: WebM, WAV, MP3, and more
- **Limits**: 60-second recordings, 25MB files

## Troubleshooting

### Common Issues

1. **"GROQ_API_KEY not configured" error**
   - Solution: Add your Groq API key to the `.env` file
   - Get key from: https://console.groq.com/keys

2. **Microphone not working**
   - Check browser permissions for microphone
   - Ensure HTTPS or localhost (required for getUserMedia)
   - Try a different browser

3. **Chat not loading**
   - Ensure analysis is completed first
   - Check backend is running on port 8000
   - Verify job_id exists in the system

4. **TTS/STT errors**
   - Check Groq API key is valid
   - Verify internet connection
   - Check Groq service status

## Performance Notes

- **SSE Streaming**: Real-time responses, no buffering
- **Context Limit**: Uses top 20 clauses to avoid token limits
- **Policy Search**: Retrieves top 5 relevant policies
- **Voice Limits**:
  - TTS: 10,000 character limit
  - STT: 25MB file size limit
  - Recording: 60-second maximum

## Security Considerations

- Groq API key stored in environment variables
- HTTPS recommended for production
- Microphone permissions required for STT
- No chat history persistence (session-only)

## Future Enhancements

Consider adding:
- Chat history persistence to database
- Multi-language support (Arabic voices ready)
- Export chat conversation
- Voice commands for navigation
- Proactive suggestions based on analysis
- Integration with document editing

## Dependencies Added

### Python
- `groq==0.33.0` - Groq Python SDK

### JavaScript
- No new dependencies (uses native Web APIs)
- Existing: React, Next.js, Tailwind CSS

## Files Created/Modified

### Created (16 files)
1. `src/services/groq_service.py`
2. `src/services/__init__.py`
3. `frontend/components/chatbot/ChatbotFloatingButton.tsx`
4. `frontend/components/chatbot/ChatPanel.tsx`
5. `frontend/components/chatbot/ChatMessage.tsx`
6. `frontend/components/chatbot/VoiceRecorder.tsx`
7. `frontend/components/chatbot/AudioPlayer.tsx`

### Modified (7 files)
1. `requirements.txt` - Added groq==0.33.0
2. `.env` - Added GROQ_API_KEY
3. `src/core/config.py` - Added groq_api_key setting
4. `src/core/prompts.py` - Added chatbot prompts
5. `src/api.py` - Added chat and voice endpoints
6. `frontend/lib/api.ts` - Added chat and voice API methods
7. `frontend/lib/types.ts` - Added chat types
8. `frontend/app/results/[id]/page.tsx` - Integrated chatbot

## Summary

The chatbot feature is fully implemented and ready for testing. It provides an intuitive way for users to interact with their contract analysis results through both text and voice. The implementation leverages:

- **Gemini 2.5 Flash** for intelligent responses
- **Groq APIs** for fast TTS and STT
- **ChromaDB RAG** for policy retrieval
- **SSE streaming** for real-time chat
- **Modern React** components with TypeScript

The feature enhances the user experience by making complex legal analysis more accessible and interactive.