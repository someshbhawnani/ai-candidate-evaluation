# 🤖 AI-Powered Automated Candidate Evaluation System

An intelligent, AI-driven technical interview platform that evaluates candidates using DeepSeek AI, featuring real-time voice interaction, automated scoring, and comprehensive performance analytics.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.29.0-red.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.1.0-green.svg)
![DeepSeek](https://img.shields.io/badge/DeepSeek-AI-purple.svg)

## 🌟 Features

### Core Functionality
- ✅ **AI-Powered Question Generation** - Dynamic technical questions tailored to role and skills
- 🎯 **Smart Evaluation** - AI-based answer scoring with detailed feedback
- 💻 **Mixed Question Types** - Conceptual (60%) + Coding (40%) questions
- ⏱️ **Timed Assessment** - 10 minutes per question, 50 minutes total
- 🔊 **Voice Assistant** - Text-to-speech for questions, speech-to-text for answers
- 📊 **Real-time Scoring** - Instant feedback after each answer
- 🎓 **Final Recommendation** - AI-generated hiring decision with rationale

### User Management
- 🔐 **Secure Authentication** - User registration and login with password hashing
- 👤 **User Profiles** - Track candidate information and experience level
- 📜 **Evaluation History** - Complete record of past assessments
- 💾 **Persistent Storage** - JSON-based database for users and evaluations

### Technical Capabilities
- 🌐 **Multi-language Support** - Questions in English, Hindi, Spanish, German, French
- 🎨 **Modern UI** - Beautiful gradient design with glassmorphism effects
- 📱 **Responsive Layout** - Works on desktop and tablet devices
- 🔄 **Auto-save** - Evaluations saved automatically on completion

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- DeepSeek API key ([Get one here](https://platform.deepseek.com/))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/ai-candidate-evaluation.git
cd ai-candidate-evaluation
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
Create a `.env` file in the root directory:
```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

4. **Run the application**
```bash
streamlit run eval.py
```

5. **Open in browser**
Navigate to `http://localhost:8501`

## 📋 Usage Guide

### For Candidates

1. **Register/Login**
   - Create account with username and password
   - Or login with existing credentials

2. **Start Evaluation**
   - Navigate to "New Evaluation"
   - Select role (e.g., Python Developer, Java Developer)
   - Choose language preference
   - Enter technical skills (comma-separated)

3. **Complete Assessment**
   - Answer 5 questions (mix of conceptual and coding)
   - Use voice mode for audio questions/answers (optional)
   - Get instant feedback after each answer
   - 10 minutes per question timer

4. **View Results**
   - See detailed score breakdown
   - Read AI-generated hiring recommendation
   - Export evaluation report
   - Review past evaluations in history

### Voice Mode Features

- 🔊 **Listen to Questions**: AI reads questions aloud
- 🎤 **Voice Answers**: Record answers using microphone
- 🧪 **Test TTS**: Verify text-to-speech functionality
- 💬 **Browser-based**: No additional software required

## 🛠️ Technology Stack

- **Framework**: Streamlit 1.29.0
- **AI/LLM**: DeepSeek Chat API via LangChain
- **Authentication**: SHA256 password hashing
- **Database**: JSON file storage
- **Voice**: Web Speech API (TTS), audio-recorder-streamlit (STT)
- **Styling**: Custom CSS with gradient backgrounds

## 📁 Project Structure

```
ai-candidate-evaluation/
├── eval.py                      # Main application
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (create this)
├── .gitignore                   # Git ignore rules
├── README.md                    # This file
├── VOICE_SETUP.md              # Voice feature documentation
├── .streamlit/
│   └── config.toml             # Streamlit theme configuration
├── users.json                   # User database (auto-created)
└── evaluation_history.json     # Evaluation records (auto-created)
```

## 🎯 Question Distribution

- **Question 1-2**: Conceptual/Theoretical (💭)
- **Question 3**: Coding Challenge (💻)
- **Question 4**: Conceptual/Theoretical (💭)
- **Question 5**: Coding Challenge (💻)

## 📊 Scoring System

Each question scored 0-20 points based on:
- **Conceptual Questions**: Accuracy, completeness, depth
- **Coding Questions**: 
  - Correctness (8 pts)
  - Code Quality (4 pts)
  - Efficiency (4 pts)
  - Edge Cases (4 pts)

### Final Recommendation
- **80%+**: Strong Hire ✅
- **60-79%**: Recommended with upskilling 👍
- **40-59%**: Not Recommended ⚠️
- **<40%**: Not Recommended ❌

## 🔧 Configuration

### Supported Roles
- Java Developer
- Database Administrator
- Frontend Developer
- DevOps Engineer
- Data Engineer
- Python Developer

### Customization

Edit `eval.py` to customize:
- Question generation prompts
- Scoring criteria
- Timer durations
- Available roles and languages
- UI styling

## 🐛 Troubleshooting

### TTS Not Working
1. Ensure you're using Chrome, Edge, or Firefox
2. Check browser isn't muted
3. Allow microphone/audio permissions
4. Try the "Test TTS" button

### API Errors
- Verify DeepSeek API key is correct
- Check API key has sufficient credits
- Ensure `.env` file is in the correct location

### Installation Issues
```bash
# Upgrade pip first
pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- DeepSeek for the powerful AI API
- Streamlit for the amazing framework
- LangChain for LLM orchestration
- The open-source community

## 📧 Contact

For questions or support, please open an issue on GitHub.

## 🔮 Future Enhancements

- [ ] Video recording support
- [ ] Multi-language UI
- [ ] Advanced analytics dashboard
- [ ] Custom question banks
- [ ] Interview scheduling
- [ ] Email notifications
- [ ] Admin dashboard
- [ ] REST API
- [ ] Docker deployment
- [ ] Database migration (PostgreSQL)

---

Made with ❤️ using DeepSeek AI and Streamlit
