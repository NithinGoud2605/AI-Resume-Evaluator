# AI Resume Evaluator

Advanced AI-powered resume evaluation system with industry-standard scoring and comprehensive analysis.

## 🏗️ **System Architecture**

### **Agent Flow Overview**

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
                                                    │ (Supabase/MySQL) │
                                                    └──────────────────┘
```

### **Data Flow Architecture**

```
1. INPUT LAYER
   ├── File Upload (Flask)
   ├── Text Extraction (PyMuPDF/docx)
   └── Session Management

2. AI PROCESSING LAYER
   ├── CrewAI Orchestration
   ├── OpenRouter API Integration
   ├── Agent Sequential Processing
   └── JSON Output Validation

3. DATA VALIDATION LAYER
   ├── Schema Validation
   ├── Cross-Agent Consistency
   ├── Data Quality Checks
   └── Error Recovery

4. STORAGE LAYER
   ├── Supabase (Primary)
   ├── MySQL (Fallback)
   ├── File System (Uploads)
   └── Session Storage

5. PRESENTATION LAYER
   ├── Results Dashboard
   ├── Export Functionality
   ├── Real-time Monitoring
   └── Error Reporting
```

## 🤖 **Agent Specifications**

### **1. Resume Analyzer Agent**
- **Role**: Senior Resume Analyst
- **Goal**: Extract comprehensive information from resumes
- **Output**: Structured JSON with candidate details
- **Validation**: Name extraction, experience calculation, skills categorization

### **2. Job Requirements Analyzer Agent**
- **Role**: Job Requirements Specialist
- **Goal**: Parse job descriptions into structured requirements
- **Output**: Prioritized requirements (Critical/Important/Preferred)
- **Validation**: Requirement completeness, priority classification

### **3. Advanced Evaluator Agent**
- **Role**: Senior Talent Evaluation Specialist
- **Goal**: Comprehensive candidate assessment
- **Output**: Detailed scoring and recommendations
- **Validation**: Score consistency, bias detection, fairness checks

### **4. Interview Strategist Agent**
- **Role**: Interview Strategy Expert
- **Goal**: Generate targeted interview questions
- **Output**: Categorized interview questions and logistics
- **Validation**: Question relevance, coverage completeness

### **5. Quality Assurance Agent**
- **Role**: Quality Assurance Specialist
- **Goal**: Ensure evaluation consistency and accuracy
- **Output**: Final validated evaluation
- **Validation**: Schema compliance, data integrity, bias removal

## 🔄 **Data Flow Validation**

### **Input Validation**
- File format verification (PDF, DOCX, TXT)
- File size limits (16MB max)
- Text extraction success
- Content quality assessment

### **Processing Validation**
- Agent output schema compliance
- Cross-agent data consistency
- Name extraction accuracy
- Score range validation (0-100)

### **Output Validation**
- Database insertion success
- Result completeness
- Export functionality
- Error handling

## 📊 **Monitoring & Analytics**

### **Performance Metrics**
- Processing time per resume
- API call success rates
- Agent completion rates
- Data quality scores

### **Error Tracking**
- API failures and retries
- Data validation failures
- Agent communication issues
- Database connection problems

### **Quality Assurance**
- Name extraction accuracy
- Score distribution analysis
- Bias detection
- Consistency checks

## 🛠️ **Configuration**

### **Environment Variables**
```bash
   # Database Configuration
DATABASE_TYPE=supabase  # or mysql
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
   
   # AI Configuration
OPENROUTER_API_KEY_1=your_api_key_1
OPENROUTER_API_KEY_2=your_api_key_2
# ... up to OPENROUTER_API_KEY_5
   
   # Flask Configuration
FLASK_SECRET_KEY=your_secret_key
```

### **API Key Management**
- Automatic key rotation
- Failure detection and fallback
- Load balancing across multiple keys
- Credit monitoring

## 🚀 **Deployment**

### **Requirements**
   ```bash
pip install -r requirements.txt
```

### **Running the Application**
   ```bash
   python main_test.py
   ```

### **Access Points**
- **Main Interface**: http://localhost:8000
- **Results Dashboard**: http://localhost:8000/results
- **API Endpoints**: /api/export/{format}

## 📈 **Performance Optimization**

### **Current Optimizations**
- API key rotation for reliability
- Reduced token limits for cost efficiency
- Sequential processing for consistency
- Comprehensive error handling

### **Future Enhancements**
- Parallel processing for independent tasks
- Batch processing for multiple resumes
- Caching for repeated evaluations
- Advanced load balancing

## 🔒 **Security & Privacy**

### **Data Protection**
- Secure file handling
- Session management
- Database encryption
- API key security

### **Compliance**
- Bias detection and mitigation
- Fair evaluation practices
- Data retention policies
- Privacy protection measures

## 📝 **Usage Examples**

### **Basic Evaluation**
1. Upload job description
2. Upload candidate resumes
3. Start evaluation
4. View results dashboard

### **Batch Processing**
1. Upload multiple resumes
2. Use retained job description
3. Process all candidates
4. Export results

### **Advanced Features**
1. Detailed candidate analysis
2. Interview question generation
3. Comparative analysis
4. Export in multiple formats

## 🐛 **Troubleshooting**

### **Common Issues**
- API key exhaustion
- File upload failures
- Database connection issues
- Agent communication problems

### **Debug Information**
- Comprehensive logging
- Data flow monitoring
- Error tracking
- Performance metrics

## 📞 **Support**

For issues and questions:
1. Check the logs in the `logs/` directory
2. Review data flow monitoring output
3. Verify configuration settings
4. Test with sample files

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Production Ready