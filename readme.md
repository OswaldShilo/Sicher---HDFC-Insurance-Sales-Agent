
<div align="center">

<!-- Project Logo -->
<img src="https://github.com/user-attachments/assets/41b80d3e-5636-49c9-b59a-4f01a3a8e7dd" alt="Sicher Logo" width="200" />
&nbsp;&nbsp;&nbsp;
<img width="200" alt="image" src="https://github.com/user-attachments/assets/2b0fbc4c-b0e4-4af1-b5e3-68baac15a201" />


<h1>Sicher - HDFC Insurance Sales Agent</h1>

<!-- Badges -->
<a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white" alt="Python"></a>
<a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.100.0-teal?logo=fastapi&logoColor=white" alt="FastAPI"></a>
<a href="https://git-scm.com/"><img src="https://img.shields.io/badge/Git-F05032?logo=git&logoColor=white" alt="Git"></a>
<a href="https://render.com/"><img src="https://img.shields.io/badge/Render-FF3E00?logo=render&logoColor=white" alt="Render"></a>
<a href="https://swagger.io/tools/swagger-ui/"><img src="https://img.shields.io/badge/Swagger-85EA2D?logo=swagger&logoColor=white" alt="Swagger"></a>
<a href="https://www.postman.com/"><img src="https://img.shields.io/badge/Postman-FF6C37?logo=postman&logoColor=white" alt="Postman"></a>
<a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License"></a>
<a href="https://developers.google.com/gemini"><img src="https://img.shields.io/badge/Gemini-AI-blueviolet" alt="Gemini AI"></a>

</div>

---

Sicher is an **AI-powered insurance sales agent** specifically trained on **HDFC Life brochures** to provide quick, simplified policy answers and intelligent quote recommendations.  
The system processes PDF documents, extracts structured data, and serves it through a **FastAPI-based REST API**.

We obtained product data from the official HDFC Life website:  
👉 [HDFC Life – All Insurance Plans](https://www.hdfclife.com/all-insurance-plans)

---

## 🎥 Project Video

[Watch on YouTube](https://www.youtube.com/watch?v=ekKt-cU8tYI)

---

## 🚀 Live Demo

You can try Sicher right now through our hosted demos:

- 🌐 **Web Chat Demo:** [Chat with Sicher](https://app.inya.ai/chat-demo/f7cd900d-18fb-4927-8844-d44a98ba2062)  
- 🎙️ **Voice/Widget Demo:** [Voice & Widget](https://app.inya.ai/demo/75e24529-f42b-4a01-9e98-1d3698cfeaca)

---

## 💡 How to Use Sicher

Visit either of the live demo links above and chat with Sicher, your **AI-powered HDFC Life advisor**.

### What You Can Ask

Sicher understands queries about all major HDFC Life plans, including:

- ✅ **Protection Plans**  
  *HDFC Life Group Poorna Credit Suraksha (UIN: 101N138V03)* → Covers death + 29 critical illnesses for loan borrowers  

- ✅ **Pension & Annuity Plans**  
  *HDFC Life Pension Guaranteed Plan (UIN: 101N118V13)* → Lifelong monthly income with Joint Life & Return of Purchase Price options  

- ✅ **ULIP Plans**  
  e.g., *HDFC Life Click 2 Wealth, Click 2 Invest*  

- ✅ **Savings Plans**  
  e.g., *HDFC Life Sampoorna Jeevan, Guaranteed Savings Plan*  

- ✅ **Health Riders**  
  e.g., *Critical Illness Plus Rider, Accident Death Benefit*  

---

## 🗣️ Sample Queries to Try

- “I have a home loan of ₹50 lakhs. Which plan protects my family?”  
- “What’s the monthly payout for ₹1 Cr in HDFC Pension Guaranteed Plan at age 50?”  
- “Does Poorna Credit Suraksha cover cancer?”  
- “Explain surrender benefits for Pension Guaranteed Plan.”  
- “Compare Protection vs Pension plans for retirement.”  

---

## 📋 Prerequisites

- Python 3.8 or higher  
- pip (Python package manager)  
- Git  

---

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/OswaldShilo/Sicher---HDFC-Insurance-Sales-Agent.git
   cd Sicher---HDFC-Insurance-Sales-Agent
   ```

2. **Navigate to Backend directory**
   ```bash
   cd Backend
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables (optional)**
   ```bash
   # For Gemini AI enrichment
   export GEMINI_API_KEY="your_gemini_api_key_here"
   ```

---

## ⚡ Quick Start

### Option 1: Use Pre-generated Data (Recommended)
```bash
python app.py
```
* API will be available at `http://localhost:8001`
* Uses pre-processed JSON files from `Scraped_Json/` directory

### Option 2: Process PDFs from Scratch
```bash
python try_ins_scraper.py
```
* Scrapes PDFs from `Bank_infos/` directory
* Generates structured JSON files
* Uses Gemini AI for data enrichment (if API key provided)

Then run:
```bash
python app.py
```

---

## 🌐 Production Deployment

### Deploy to Render (Recommended)

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Configure settings:
   - Root Directory: `Backend`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
4. Set Environment Variables:
   ```ini
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   ALLOWED_ORIGINS=https://your-frontend-domain.com,https://localhost:3000
   ```
5. Deploy and get your production URL (e.g., `https://your-app-name.onrender.com`)

---

## 📚 API Documentation

### Base URLs
- **Local Development**: `http://localhost:8001`  
- **Production**: `https://your-app-name.onrender.com`

### Interactive Documentation
- **Swagger UI**: `http://localhost:8001/docs`  
- **ReDoc**: `http://localhost:8001/redoc`

---

## 🔌 API Endpoints

### Health Check
```http
GET /
GET /health
```

### 1. Get All Policies
```http
GET /policies
```

### 2. Generate Insurance Quotes
```http
POST /quote
Content-Type: application/json
```
**Request Example:**
```json
{
  "age_band": "25-35",
  "dependents_count": 2,
  "annual_income_band": "5L-10L",
  "preferred_premium_band": "10k-25k",
  "risk_tolerance": "balanced",
  "health_flags": ["diabetes"],
  "city_state": "Mumbai, Maharashtra",
  "contact_channel": "online"
}
```

### 3. Customer Service Handoff
```http
POST /handoff
Content-Type: application/json
```

---

## 🧪 Testing with Postman

**GET Request:**
- Method: `GET`
- URL: `http://localhost:8001/policies`

**POST Quote Request:**
- Method: `POST`
- URL: `http://localhost:8001/quote`
- Headers: `Content-Type: application/json`
- Body Example:
```json
{
  "age_band": "30-40",
  "dependents_count": 1,
  "preferred_premium_band": "15k-30k",
  "risk_tolerance": "conservative"
}
```

---

## 🐛 Troubleshooting

- **Port already in use**
```bash
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```
- **PDF processing errors**: Ensure PDFs are not password-protected, readable, and not corrupted  
- **Missing dependencies**: `pip install -r requirements.txt`  
- **CORS issues in production**: Include your frontend domain in `ALLOWED_ORIGINS`

---

## 🤝 Contributing

1. Fork the repository  
2. Create a feature branch (`git checkout -b feature/amazing-feature`)  
3. Commit your changes (`git commit -m 'Add some amazing feature'`)  
4. Push to the branch (`git push origin feature/amazing-feature`)  
5. Open a Pull Request  

---

## 📝 License

MIT License – see the [LICENSE](LICENSE) file for details.

---

**Note**: This project is for educational/demo purposes. Always verify insurance information with official HDFC Life sources.

