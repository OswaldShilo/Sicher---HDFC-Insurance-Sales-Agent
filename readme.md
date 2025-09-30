<div align="center">

<!-- Project Logo -->
<img src="https://github.com/user-attachments/assets/41b80d3e-5636-49c9-b59a-4f01a3a8e7dd" alt="Sicher Logo" width="200" />

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

Sicher is an AI-powered insurance sales agent specifically trained on HDFC Life insurance brochures to provide quick, simplified policy answers and intelligent quote recommendations. The system processes PDF documents, extracts structured data, and serves it through a FastAPI-based REST API.

## 🚀 Features

- **Intelligent PDF Processing**: Extracts structured data from HDFC Life insurance PDFs  
- **AI-Enhanced Data Extraction**: Uses Gemini AI for data enrichment and validation  
- **Smart Quote Engine**: Provides personalized insurance recommendations based on customer profiles  
- **RESTful API**: FastAPI-based endpoints for easy integration  
- **Multi-Category Support**: Handles Health, Pension, Protection, Savings, ULIP, and Annuity plans  
- **Enhanced Data Fields**: Extracts UIN, product types, eligibility criteria, and operational details  
- **Production Ready**: Deployable to cloud platforms with health monitoring  

## 📋 Prerequisites

- Python 3.8 or higher  
- pip (Python package manager)  
- Git  

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/OswaldShilo/Sicher---HDFC-Insurance-Sales-Agent.git
   cd Sicher---HDFC-Insurance-Sales-Agent

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

## 🚀 Quick Start

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

   * Root Directory: `Backend`
   * Environment: `Python 3`
   * Build Command: `pip install -r requirements.txt`
   * Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`

4. Set Environment Variables:

```
GEMINI_API_KEY=your_actual_gemini_api_key_here
ALLOWED_ORIGINS=https://your-frontend-domain.com,https://localhost:3000
```

5. Deploy and get your production URL (e.g., `https://your-app-name.onrender.com`)

---

## 📚 API Documentation

### Base URLs

* **Local Development**: `http://localhost:8001`
* **Production**: `https://your-app-name.onrender.com`

### Interactive Documentation

* **Swagger UI**: `http://localhost:8001/docs`
* **ReDoc**: `http://localhost:8001/redoc`

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

**Request Body Example:**

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

* Method: `GET`
* URL: `http://localhost:8001/policies`

**POST Quote Request:**

* Method: `POST`
* URL: `http://localhost:8001/quote`
* Headers: `Content-Type: application/json`
* Body Example:

```json
{
  "age_band": "30-40",
  "dependents_count": 1,
  "preferred_premium_band": "15k-30k",
  "risk_tolerance": "conservative"
}
```

---

## 📊 Data Processing

### Enhanced Data Fields Extracted

* **Identifiers**: UIN, policy name, insurer
* **Financials**: Sum assured options, premium examples, purchase price range
* **Eligibility**: Entry age, maturity age, term ranges, group size requirements
* **Plan Structure**: Plan options, cover types, payment modes, joint life availability
* **Benefits**: Death benefit, maturity benefit, critical illness count, accidental death benefit
* **Operational**: Free look period, grace period, revival terms, policy loan availability
* **Annuity Specific**: Payout frequency, deferment period, return of purchase price
* **AI Enrichment**: Key features, benefits summary, unique selling points

### Supported PDF Categories

* Health Plans
* Pension Plans
* Protection Plans
* Savings Plans
* ULIP Plans
* Annuity Plans

---

## 🐛 Troubleshooting

1. **Port already in use**

```bash
netstat -ano | findstr :8001
taskkill /PID <PID> /F
```

2. **PDF processing errors**: Ensure PDFs are not password-protected, readable, and not corrupted
3. **Missing dependencies**: `pip install -r requirements.txt`
4. **CORS issues in production**: Include your frontend domain in `ALLOWED_ORIGINS`

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

* HDFC Life for insurance product info
* Google Gemini AI for data enrichment
* FastAPI framework for REST API
* Open-source Python libraries

---

**Note**: For educational/demo purposes. Always verify insurance info with official HDFC Life sources.

