# 🤖 AI Resume Evaluator

> **Advanced AI-powered resume evaluation system with industry-standard scoring, comprehensive analysis, and detailed feedback for better hiring decisions.**

## 🎯 Overview

The AI Resume Evaluator is a sophisticated web application that leverages multiple AI agents to analyze resumes against job descriptions, providing comprehensive evaluations with detailed scoring, interview questions, and actionable insights. Built with modern technologies and best practices, it's designed for HR professionals and hiring managers who need efficient, accurate, and bias-free candidate assessment.

## 🚀 How It Works

### **Step-by-Step Process**

1. **Upload Job Description** 📋
   - Upload a PDF, DOCX, or TXT file containing the job requirements
   - Or paste the job description directly into the text area
   - The system extracts and analyzes the requirements

2. **Upload Resume Files** 📄
   - Upload multiple resume files (up to 50 per batch)
   - Supported formats: PDF, DOCX, TXT
   - Drag & drop functionality available

3. **AI Processing** 🤖
   - **5 AI Agents** work sequentially to analyze each resume:
     - **Resume Analyzer**: Extracts candidate information
     - **Job Requirements Analyzer**: Parses job description
     - **Advanced Evaluator**: Comprehensive candidate assessment
     - **Interview Strategist**: Generates targeted questions
     - **Quality Assurance**: Ensures accuracy and consistency

4. **Results Dashboard** 📊
   - View comprehensive results with analytics
   - Individual candidate cards with detailed scores
   - Filter and sort capabilities
   - Export options for reports

### **AI Agent Workflow**

```
┌─────────────────┐    ┌─────────────────────┐    ┌──────────────────┐
│   File Upload   │───▶│   Text Extraction   │───▶│  Resume Analyzer  │
│   (PDF/DOCX)    │    │   (PyMuPDF/docx)    │    │     Agent        │
└─────────────────┘    └─────────────────────┘    └──────────────────┘
                                                           │
                                                           ▼
┌─────────────────┐    ┌─────────────────────┐    ┌──────────────────┐
│ Job Description │───▶│   Text Extraction   │───▶│ Job Requirements │
│   Upload        │    │   (PyMuPDF/docx)    │    │   Analyzer       │
└─────────────────┘    └─────────────────────┘    └──────────────────┘
                                                           │
                                                           ▼
                                                    ┌──────────────────┐
                                                    │  Advanced        │
                                                    │  Evaluator       │
                                                    │  Agent           │
                                                    └──────────────────┘
                                                           │
                                                           ▼
                                                    ┌──────────────────┐
                                                    │ Interview        │
                                                    │ Strategist       │
                                                    │ Agent            │
                                                    └──────────────────┘
                                                           │
                                                           ▼
                                                    ┌──────────────────┐
                                                    │ Quality          │
                                                    │ Assurance        │
                                                    │ Agent            │
                                                    └──────────────────┘
                                                           │
                                                           ▼
                                                    ┌──────────────────┐
                                                    │ Database         │
                                                    │ Storage          │
                                                    │ (Supabase)       │
                                                    └──────────────────┘
```

## 🛠️ Technology Stack

### **Backend**
- **Python 3.10+** - Core programming language
- **Flask 2.3+** - Web framework for API and routing
- **CrewAI 0.28+** - Multi-agent orchestration framework
- **LangChain** - LLM integration and prompt management

### **AI & Machine Learning**
- **OpenRouter API** - Access to multiple LLM providers
- **GPT-3.5 Turbo** - Primary AI model for evaluation
- **Custom Prompt Engineering** - Optimized prompts for each agent
- **JSON Schema Validation** - Structured output validation

### **Database**
- **Supabase (PostgreSQL)** - Primary database with real-time capabilities
- **SQLAlchemy** - Database ORM and connection management
- **Connection Pooling** - Optimized database performance

### **File Processing**
- **PyMuPDF (fitz)** - PDF text extraction
- **python-docx** - DOCX file processing
- **Text Processing** - Natural language processing utilities

### **Frontend**
- **HTML5/CSS3** - Modern, responsive web interface
- **JavaScript (ES6+)** - Interactive client-side functionality
- **Chart.js** - Data visualization and analytics
- **Font Awesome** - Icon library for UI elements

## 📦 Installation & Setup

### **Prerequisites**
- Python 3.10 or higher
- Supabase account (recommended)
- OpenRouter API key(s)

### **Quick Setup**

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-resume-evaluator.git
   cd ai-resume-evaluator
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   
   Create a `.env` file with your configuration:
   ```env
   # Database Configuration (Supabase)
   DATABASE_TYPE=supabase
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   
   # AI Configuration
   OPENROUTER_API_KEY_1=your_openrouter_api_key_1
   OPENROUTER_API_KEY_2=your_openrouter_api_key_2
   OPENROUTER_API_KEY_3=your_openrouter_api_key_3
   OPENROUTER_API_KEY_4=your_openrouter_api_key_4
   OPENROUTER_API_KEY_5=your_openrouter_api_key_5
   
   # Flask Configuration
   FLASK_SECRET_KEY=your_super_secret_key_here
   FLASK_ENV=development
   ```

5. **Database Setup**
   
   **For Supabase:**
   - Create a new Supabase project
   - Run the SQL schema in your Supabase SQL Editor
   - Update your `.env` file with project credentials

6. **Run the application**
   ```bash
   python main_test.py
   ```

7. **Access the application**
   Open your browser and navigate to `http://localhost:8000`

## 🎯 Usage Guide

### **Basic Evaluation Process**

1. **Upload Job Description**
   - Click the job description upload area
   - Select a PDF, DOCX, or TXT file containing the job requirements
   - The system will extract and analyze the requirements

2. **Upload Resume Files**
   - Click the resume upload area
   - Select multiple resume files (up to 50 per batch)
   - Supported formats: PDF, DOCX, TXT

3. **Start Evaluation**
   - Click "Start AI Evaluation"
   - The system will process each resume using advanced AI analysis
   - Processing time varies based on file size and complexity

4. **View Results**
   - Comprehensive results dashboard with analytics
   - Individual candidate cards with detailed scores
   - Filter and sort capabilities
   - Export options for reports

### **Advanced Features**

#### **Analytics Dashboard**
- **Score Distribution**: Visual representation of candidate performance
- **Qualification Breakdown**: Pie chart of qualification statuses
- **Statistics Overview**: Key metrics and insights
- **Filtering Options**: Filter by score range, qualification status

#### **Export Capabilities**
- **CSV Export**: Raw data for external analysis
- **JSON Export**: Structured data for API integration
- **Excel Export**: Multi-sheet analysis with charts

#### **Candidate Management**
- **Detailed Profiles**: Comprehensive candidate information
- **Evaluation History**: Track multiple evaluations
- **Interview Questions**: Auto-generated relevant questions
- **Recommendation Engine**: Hiring recommendations

## 📊 Evaluation Methodology

### **Scoring Algorithm**

The system uses a weighted scoring approach:

- **Experience (35%)**: Years and relevance of work experience
- **Skills (25%)**: Technical and soft skills matching
- **Education (15%)**: Degree relevance and academic achievements
- **Achievements (15%)**: Quantifiable accomplishments and impact
- **Cultural Fit (10%)**: Company and role alignment

### **Score Ranges**

- **90-100**: Exceptional fit, exceeds requirements
- **80-89**: Strong fit, meets all critical requirements
- **70-79**: Good fit, meets most requirements
- **60-69**: Moderate fit, some gaps in requirements
- **50-59**: Weak fit, significant gaps
- **Below 50**: Poor fit, major misalignment

### **Qualification Tags**

- **QUALIFIED**: Score ≥ 75, meets job requirements
- **NOT QUALIFIED**: Score < 75, significant gaps
- **OVERQUALIFIED**: Exceeds requirements significantly

## 🔧 Configuration

### **AI Model Configuration**

The system supports multiple AI providers:

**OpenRouter (Recommended)**
```env
OPENROUTER_API_KEY_1=your_key_here
OPENROUTER_API_KEY_2=your_key_here
# ... up to 5 keys for rotation
```

**Advanced Settings**
```env
# AI Configuration
AI_TEMPERATURE=0.1
AI_MAX_TOKENS=4000
AI_TIMEOUT=300

# File Upload Limits
MAX_FILE_SIZE_MB=16
MAX_RESUMES_PER_BATCH=50

# Database Performance
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

## 🔒 Security & Privacy

### **Data Protection**
- Secure file handling with validation
- Session management with secure cookies
- Database encryption and access controls
- API key security and rotation

### **Compliance**
- Bias detection and mitigation algorithms
- Fair evaluation practices implementation
- Data retention policies
- Privacy protection measures

## 🚀 Performance Optimization

### **Database Optimization**
- Indexed columns for fast queries
- Optimized schema with proper relationships
- Connection pooling for concurrent requests
- Automatic cleanup of old data

### **AI Processing**
- Batch processing for multiple resumes
- Caching of job description analysis
- Parallel processing where possible
- Error handling and retry mechanisms

## 🧪 Testing

### **Run Tests**
```bash
# Unit tests
python -m pytest tests/

# Integration tests
python -m pytest tests/integration/

# Load testing
python tests/load_test.py
```

## 📈 Monitoring & Analytics

### **System Metrics**
- Processing time per resume
- Accuracy rates and confidence scores
- Error rates and failure analysis
- Resource utilization

### **Business Metrics**
- Qualification rates by job type
- Score distributions over time
- Popular skills and requirements
- Hiring funnel analytics

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### **Development Setup**
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### **Code Standards**
- PEP 8 compliance
- Type hints for Python functions
- Comprehensive docstrings
- Unit test coverage > 80%

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### **Documentation**
- [API Documentation](docs/api.md)
- [Configuration Guide](docs/configuration.md)
- [Troubleshooting](docs/troubleshooting.md)

### **Community**
- [GitHub Issues](https://github.com/yourusername/ai-resume-evaluator/issues)
- [Discussions](https://github.com/yourusername/ai-resume-evaluator/discussions)

## 🗺️ Roadmap

### **Version 2.0 (Q2 2024)**
- [ ] Multi-language support
- [ ] Advanced ML models
- [ ] Real-time collaboration
- [ ] Mobile application

### **Version 2.1 (Q3 2024)**
- [ ] Video interview analysis
- [ ] Skill gap analysis
- [ ] Automated scheduling
- [ ] Advanced reporting

### **Version 3.0 (Q4 2024)**
- [ ] AI-powered job matching
- [ ] Candidate sourcing
- [ ] Predictive analytics
- [ ] Enterprise integrations

## 🙏 Acknowledgments

- **CrewAI Team** for the multi-agent framework
- **OpenRouter** for API access and infrastructure
- **Flask Community** for the excellent web framework
- **Supabase** for the powerful database platform
- **Contributors** who helped improve this project

---

**Made with ❤️ by the AI Resume Evaluator Team**

*Transforming recruitment with AI-powered insights*
