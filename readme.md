# Sicher - HDFC Insurance Sales Agent

Sicher is an AI-powered insurance sales agent specifically trained on HDFC Life insurance brochures to provide quick, simplified policy answers and intelligent quote recommendations. The system processes PDF documents, extracts structured data, and serves it through a FastAPI-based REST API.

## 🚀 Features

- **Intelligent PDF Processing**: Extracts structured data from HDFC Life insurance PDFs
- **AI-Enhanced Data Extraction**: Uses Gemini AI for data enrichment and validation
- **Smart Quote Engine**: Provides personalized insurance recommendations based on customer profiles
- **RESTful API**: FastAPI-based endpoints for easy integration
- **Multi-Category Support**: Handles Health, Pension, Protection, Savings, ULIP, and Annuity plans
- **Enhanced Data Fields**: Extracts UIN, product types, eligibility criteria, and operational details

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/OswaldShilo/Sicher---HDFC-Insurance-Sales-Agent.git
   cd Sicher---HDFC-Insurance-Sales-Agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables (optional)**
   ```bash
   # For Gemini AI enrichment (optional)
   export GEMINI_API_KEY="your_gemini_api_key_here"
   ```

## 🚀 Quick Start

### Option 1: Use Pre-generated Data (Recommended)

1. **Run the enhanced API with existing data**
   ```bash
   python app_todelete.py
   ```
   - API will be available at `http://localhost:8001`
   - Uses pre-processed JSON files from `todelete/` directory

### Option 2: Process PDFs from Scratch

1. **Process PDF documents**
   ```bash
   python try_ins_scraper.py
   ```
   - Scrapes PDFs from `Bank_infos/` directory
   - Generates structured JSON files
   - Uses Gemini AI for data enrichment (if API key provided)

2. **Run the API**
   ```bash
   python app_todelete.py
   ```

## 📚 API Documentation

### Base URLs
- **Enhanced API**: `http://localhost:8001`
- **Original API**: `http://localhost:8000`

### Interactive Documentation
- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`

## 🔌 API Endpoints

### 1. Get All Policies
```http
GET /policies
```

### 2. Generate Insurance Quotes
```http
POST /quote
Content-Type: application/json
```

**Request Body:**
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

## 🧪 Testing with Postman

**GET Request:**
- Method: `GET`
- URL: `http://localhost:8001/policies`

**POST Quote Request:**
- Method: `POST`
- URL: `http://localhost:8001/quote`
- Headers: `Content-Type: application/json`
- Body (JSON):
```json
{
  "age_band": "30-40",
  "dependents_count": 1,
  "preferred_premium_band": "15k-30k",
  "risk_tolerance": "conservative"
}
```

## 📊 Data Processing

### Enhanced Data Fields Extracted
- **Identifiers**: UIN, policy name, insurer
- **Financials**: Sum assured options, premium examples, purchase price range
- **Eligibility**: Entry age, maturity age, term ranges, group size requirements
- **Plan Structure**: Plan options, cover types, payment modes, joint life availability
- **Benefits**: Death benefit, maturity benefit, critical illness count, accidental death benefit
- **Operational**: Free look period, grace period, revival terms, policy loan availability
- **Annuity Specific**: Payout frequency, deferment period, return of purchase price
- **AI Enrichment**: Key features, benefits summary, unique selling points

### Supported PDF Categories
- **Health Plans**: Medical insurance and health coverage
- **Pension Plans**: Retirement and pension products
- **Protection Plans**: Term life and credit protection
- **Savings Plans**: Endowment and savings products
- **ULIP Plans**: Unit-linked insurance products
- **Annuity Plans**: Retirement income products

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Kill process using port 8001
   netstat -ano | findstr :8001
   taskkill /PID <PID> /F
   ```

2. **PDF processing errors**
   - Ensure PDFs are not password protected
   - Check file permissions
   - Verify PDF files are not corrupted

3. **Missing dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- HDFC Life for providing insurance product information
- Google Gemini AI for data enrichment capabilities
- FastAPI framework for the REST API
- The open-source community for various Python libraries

---

**Note**: This project is for educational and demonstration purposes. Always verify insurance information with official HDFC Life sources before making any financial decisions.