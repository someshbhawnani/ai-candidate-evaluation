# Voice Assistant Setup Guide

## Overview
The evaluation system now includes voice capabilities for a more interactive interview experience.

## Features Implemented

### 1. Text-to-Speech (AI Agent Speaks Questions)
- ✅ **Browser-based TTS**: Uses Web Speech API (built-in, no additional setup needed)
- ✅ **Listen Button**: Appears next to each question when voice mode is enabled
- ✅ **Customizable**: Adjustable voice rate and pitch

### 2. Speech-to-Text (Candidate Voice Input)
- 🎤 **Microphone Recording**: Click to record your answer
- 🔄 **Real-time Conversion**: Automatically converts speech to text
- ⚠️ **Note**: Basic implementation included, requires API integration for production

## How to Use

### Enable Voice Mode
1. Start an evaluation
2. Toggle "🎤 Voice Mode" switch at the top of the evaluation page
3. Listen to AI reading questions
4. Click microphone to record your answers

### Voice Controls
- **🔊 Listen to Question**: AI reads the question aloud
- **🎙️ Start Recording**: Record your answer using microphone
- **⏹️ Stop Recording**: Stop recording and convert to text
- **🗑️ Clear Recording**: Delete current recording and start over

## Production Setup (Recommended)

For accurate speech-to-text in production, integrate one of these APIs:

### Option 1: OpenAI Whisper API
```python
import openai

def transcribe_audio(audio_file):
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    return transcript['text']
```

### Option 2: Google Cloud Speech-to-Text
```bash
pip install google-cloud-speech
```

```python
from google.cloud import speech

def transcribe_audio(audio_data):
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=audio_data)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code="en-US"
    )
    response = client.recognize(config=config, audio=audio)
    return response.results[0].alternatives[0].transcript
```

### Option 3: Deepgram API
```bash
pip install deepgram-sdk
```

```python
from deepgram import Deepgram

async def transcribe_audio(audio_file):
    dg_client = Deepgram(DEEPGRAM_API_KEY)
    source = {'buffer': audio_file, 'mimetype': 'audio/wav'}
    response = await dg_client.transcription.prerecorded(source)
    return response['results']['channels'][0]['alternatives'][0]['transcript']
```

## Browser Compatibility

### Text-to-Speech (Works in):
- ✅ Chrome/Edge (Recommended)
- ✅ Firefox
- ✅ Safari
- ⚠️ May have limited voice options in some browsers

### Speech-to-Text (Requires):
- 🎤 Microphone access permission
- 🌐 HTTPS connection (or localhost for testing)
- 📦 Additional API integration for production accuracy

## Troubleshooting

### Issue: TTS not working
- **Solution**: Check browser compatibility, ensure audio is not muted

### Issue: Microphone not recording
- **Solution**: Grant microphone permissions in browser settings

### Issue: Poor transcription accuracy
- **Solution**: Integrate production-grade STT API (Whisper, Google, or Deepgram)

## Configuration

You can customize voice settings in the code:

```javascript
msg.rate = 0.9;  // Speech rate (0.1 to 10)
msg.pitch = 1;   // Voice pitch (0 to 2)
msg.lang = 'en-US';  // Language
```

## Future Enhancements
- [ ] Multiple language support
- [ ] Voice profile selection
- [ ] Real-time transcription feedback
- [ ] Voice emotion analysis
- [ ] Pronunciation feedback for technical terms
