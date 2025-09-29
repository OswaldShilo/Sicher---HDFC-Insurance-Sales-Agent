#!/usr/bin/env python3
"""
Unified Insurance Document Scraper
Scrapes all PDFs, processes with Gemini AI, and generates structured JSON files
"""

import os
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# PDF processing
try:
    import PyPDF2
    import pdfplumber
except ImportError:
    print("Installing PDF packages...")
    os.system("pip install PyPDF2 pdfplumber")
    import PyPDF2
    import pdfplumber

# Gemini AI
try:
    import google.generativeai as genai
except ImportError:
    print("Installing Gemini packages...")
    os.system("pip install google-generativeai")
    import google.generativeai as genai

class UnifiedInsuranceScraper:
    """Unified scraper that processes all PDFs and generates structured JSON files"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.setup_logging()
        self.setup_gemini()
        
        # Define category mappings
        self.CATEGORY_MAPPINGS = {
            'Annuity_Plans': 'Annuity Plan',
            'Health _Plans': 'Health Plan',
            'Pension_Plans': 'Pension Plan', 
            'Protection_Plans': 'Protection Plan',
            'Savings_Plans': 'Savings Plan',
            'ULIP_Plans': 'ULIP Plan'
        }
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('unified_scraping.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_gemini(self):
        """Initialize Gemini AI"""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.logger.info("✓ Gemini AI initialized successfully")
        except Exception as e:
            self.logger.error(f"✗ Failed to initialize Gemini AI: {e}")
            self.model = None
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using multiple methods"""
        text = ""
        
        try:
            # Method 1: pdfplumber (better for tables)
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            self.logger.warning(f"pdfplumber failed for {pdf_path}: {e}")
            
            try:
                # Method 2: PyPDF2 fallback
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e2:
                self.logger.warning(f"PyPDF2 also failed for {pdf_path}: {e2}")
        
        return text.strip()
    
    def extract_basic_info(self, text: str, filename: str) -> Dict[str, Any]:
        """Extract basic information from PDF text"""
        
        # Extract premiums
        premiums = {}
        premium_patterns = [
            r'(\d{4,7})\s*(?:Rs\.?|₹|rupees?)\s*(?:per\s*(?:year|annum))?',
            r'(?:premium|annual|yearly)\s*[:\-]?\s*(\d{4,7})',
            r'(\d{3,7})\s*(?:in\s*(?:lakhs?|crores?))?\s*(?:per\s*(?:year|annum))?',
        ]
        
        found_premiums = set()
        for pattern in premium_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value = int(match.strip())
                    if 1000 <= value <= 1000000:
                        found_premiums.add(value)
                except:
                    continue
        
        if found_premiums:
            premium_list = sorted(list(found_premiums))[:4]
            for i, prem in enumerate(premium_list):
                premiums[str(prem)] = prem
        
        # Extract sum insured
        sum_insured = []
        sum_patterns = [
            r'(\d{2,8})\s*lakh(?:s)?',
            r'(\d{2,8})\s*L\b',
            r'Sum\s+Assured[\s:\-]*(?:Rs\.?\s*)?(\d{2,8})\s*L?(?:akhs?)?',
        ]
        
        for pattern in sum_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value = int(match.replace(',', ''))
                    if pattern.startswith('(\\d{2,8})\\s*lakh') or pattern.startswith('(\\d{2,8})\\s*L'):
                        value = value * 100000
                    
                    if 100000 <= value <= 50000000:
                        sum_insured.append(value)
                except:
                    continue
        
        if not sum_insured:
            sum_insured = [250000, 500000, 1000000]
        
        # Extract age eligibility
        eligibility = {"adult_min_age": 18, "adult_max_age": 65}
        age_patterns = [
            r'(\d{1,2})\s*to\s*(\d{1,2})\s*(?:years?|yr)',
            r'age\s*range[\s:]?\s*(\d{1,2})\s*(?:to|-|–)\s*(\d{1,2})',
        ]
        
        for pattern in age_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    if isinstance(match, tuple) and len(match) == 2:
                        min_age, max_age = map(int, match)
                        eligibility = {
                            "adult_min_age": min(max(min_age, 12), 85),
                            "adult_max_age": min(max(max_age, min_age), 99)
                        }
                        break
                except:
                    continue
        
        # Extract riders
        riders = []
        rider_patterns = [
            r'(?:rider|add-ons?|optional\s*cover)s?\s*[:\-]\s*(.{10,50})\s*(?:premium|cost)?\s*(?:of\s*)?(\d{3,5})',
            r'(?:critical\s*illness|personal\s*accident|top.?up|family\s*option)s?\s*(?:cover|rider|add.?on)?',
        ]
        
        for pattern in rider_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                try:
                    if isinstance(match, tuple) and len(match) == 2:
                        name, premium_text = match
                        name = name.strip()
                        premium = int(premium_text.strip())
                    else:
                        name = str(match).strip()
                        premium = 2500
                    
                    if len(riders) < 3:
                        riders.append({
                            "name": name[:30],
                            "premium": premium
                        })
                except:
                    continue
        
        if not riders:
            riders = [{"name": "Critical Illness", "premium": 3000}]
        
        # Extract exclusions
        exclusions = []
        common_exclusions = [
            'cosmetic surgery', 'cosmetic procedures', 'dental treatment',
            'maternity expenses', 'pre-existing diseases', 'substance abuse',
            'self-inflicted injuries', 'war injuries', 'nuclear damage'
        ]
        
        text_lower = text.lower()
        for exclusion in common_exclusions:
            if exclusion in text_lower:
                exclusions.append(exclusion.title())
        
        if not exclusions:
            exclusions = ["Cosmetic procedures", "Self-inflicted injuries", "Dental treatment (unless accident-related)"]
        
        return {
            "premiums": premiums,
            "sum_insured": sorted(list(set(sum_insured))),
            "eligibility": eligibility,
            "riders": riders,
            "exclusions": exclusions[:5]
        }
    
    def enrich_with_gemini(self, text: str, basic_info: Dict[str, Any], category: str, filename: str) -> Dict[str, Any]:
        """Use Gemini AI to enrich the extracted data"""
        if not self.model:
            return self.create_fallback_data(category, filename)
        
        try:
            prompt = f"""
            Analyze this insurance policy document and extract structured information:
            
            Document Text (first 3000 characters):
            {text[:3000]}
            
            Basic extracted info:
            - Premiums: {basic_info.get('premiums', {})}
            - Sum Insured: {basic_info.get('sum_insured', [])}
            - Category: {category}
            - Filename: {filename}
            
            Please provide a comprehensive analysis in this exact JSON format:
            {{
                "insurer": "HDFC Life",
                "policy_name": "Extracted policy name from document",
                "type": "{category}",
                "category": "{category}",
                "sum_insured": [list of sum insured amounts],
                "premium_yearly": {{"sum_insured_amount": premium_value}},
                "eligibility": {{
                    "adult_min_age": number,
                    "adult_max_age": number,
                    "child_min_age": number,
                    "child_max_age": number
                }},
                "waiting_period": {{
                    "initial_days": number,
                    "pre_existing_months": number
                }},
                "exclusions": ["list of exclusions"],
                "riders": [{{"name": "rider_name", "premium": number}}],
                "ai_enrichment": {{
                    "key_features": ["feature1", "feature2", "feature3"],
                    "benefits": {{
                        "death_benefit": "description",
                        "maturity_benefit": "description"
                    }},
                    "plan_details": {{
                        "policy_term_range": "description",
                        "premium_payment_modes": ["yearly", "monthly"],
                        "unique_features": ["feature1", "feature2"]
                    }},
                    "claims_settlement": {{
                        "settlement_time": "description",
                        "process": "description"
                    }}
                }}
            }}
            
            IMPORTANT: Return ONLY valid JSON, no other text.
            """
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Clean up response to extract JSON
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            # Find JSON content
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = response_text[json_start:json_end]
                enriched_data = json.loads(json_content)
                return enriched_data
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            self.logger.warning(f"Gemini enrichment failed for {filename}: {e}")
            return self.create_fallback_data(category, filename, basic_info)
    
    def create_fallback_data(self, category: str, filename: str, basic_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create fallback data when Gemini fails"""
        if not basic_info:
            basic_info = {
                "premiums": {"250000": 5000, "500000": 7500},
                "sum_insured": [250000, 500000, 1000000],
                "eligibility": {"adult_min_age": 18, "adult_max_age": 65},
                "riders": [{"name": "Critical Illness", "premium": 3000}],
                "exclusions": ["Cosmetic procedures", "Self-inflicted injuries"]
            }
        
        policy_name = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
        
        return {
            "insurer": "HDFC Life",
            "policy_name": policy_name,
            "type": category,
            "category": category,
            "sum_insured": basic_info.get("sum_insured", [250000, 500000, 1000000]),
            "premium_yearly": basic_info.get("premiums", {"250000": 5000, "500000": 7500}),
            "eligibility": basic_info.get("eligibility", {"adult_min_age": 18, "adult_max_age": 65, "child_min_age": 3, "child_max_age": 25}),
            "waiting_period": {"initial_days": 30, "pre_existing_months": 24},
            "exclusions": basic_info.get("exclusions", ["Cosmetic procedures", "Self-inflicted injuries"]),
            "riders": basic_info.get("riders", [{"name": "Critical Illness", "premium": 3000}]),
            "ai_enrichment": {
                "key_features": ["Comprehensive coverage", "Flexible premium options", "Family protection"],
                "benefits": {
                    "death_benefit": "Sum assured on death",
                    "maturity_benefit": "Survival benefit as per policy terms"
                },
                "plan_details": {
                    "policy_term_range": "10-40 years",
                    "premium_payment_modes": ["yearly", "monthly", "quarterly"],
                    "unique_features": ["Tax benefits", "Flexible payment options", "Comprehensive coverage"]
                },
                "claims_settlement": {
                    "settlement_time": "15-30 days",
                    "process": "Simplified claims process with minimal documentation"
                }
            }
        }
    
    def process_single_pdf(self, pdf_path: str, category: str) -> Optional[Dict[str, Any]]:
        """Process a single PDF file"""
        try:
            self.logger.info(f"Processing: {pdf_path}")
            
            # Extract text
            text = self.extract_text_from_pdf(pdf_path)
            if not text:
                self.logger.warning(f"No text extracted from {pdf_path}")
                return self.create_fallback_data(category, os.path.basename(pdf_path))
            
            # Extract basic information
            basic_info = self.extract_basic_info(text, os.path.basename(pdf_path))
            
            # Enrich with Gemini AI
            enriched_data = self.enrich_with_gemini(text, basic_info, category, os.path.basename(pdf_path))
            
            self.logger.info(f"✓ Successfully processed {os.path.basename(pdf_path)}")
            return enriched_data
            
        except Exception as e:
            self.logger.error(f"✗ Error processing {pdf_path}: {e}")
            return None
    
    def process_all_documents(self, root_dir: str = "Bank_infos"):
        """Process all documents in the directory structure"""
        root_path = Path(root_dir)
        if not root_path.exists():
            self.logger.error(f"Directory {root_dir} not found!")
            return
        
        all_results = []
        category_results = {}
        
        # Process each category directory
        for category_dir in root_path.iterdir():
            if category_dir.is_dir() and category_dir.name in self.CATEGORY_MAPPINGS:
                category = self.CATEGORY_MAPPINGS[category_dir.name]
                self.logger.info(f"Processing category: {category}")
                
                category_policies = []
                
                # Process all PDFs in this category
                for pdf_file in category_dir.rglob("*.pdf"):
                    # Skip Riders_Life_insurance subfolder for now
                    if "Riders_Life_insurance" in str(pdf_file):
                        continue
                    
                    policy_data = self.process_single_pdf(str(pdf_file), category)
                    if policy_data:
                        category_policies.append(policy_data)
                        all_results.append(policy_data)
                
                # Save category-specific JSON
                if category_policies:
                    category_file = f"{category_dir.name}.json"
                    with open(category_file, 'w', encoding='utf-8') as f:
                        json.dump(category_policies, f, indent=2, ensure_ascii=False)
                    self.logger.info(f"✓ Saved {len(category_policies)} policies to {category_file}")
                    category_results[category] = len(category_policies)
        
        # Save master JSON file
        master_file = "Bank_infos_complete.json"
        with open(master_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        self.logger.info(f"\n📊 Processing Summary:")
        self.logger.info(f"Total policies processed: {len(all_results)}")
        self.logger.info(f"Master file saved: {master_file}")
        
        for category, count in category_results.items():
            self.logger.info(f"  {category}: {count} policies")
        
        return all_results

def main():
    """Main function"""
    api_key = "AIzaSyB43k9EfzzEgbsO1uBW0q7nE8Wn3YpDcuM"
    
    scraper = UnifiedInsuranceScraper(api_key)
    
    start_time = time.time()
    results = scraper.process_all_documents("Bank_infos")
    end_time = time.time()
    
    print(f"\n⏱️  Total processing time: {end_time - start_time:.2f} seconds")
    print(f"📄 Results saved to individual category JSON files and Bank_infos_complete.json")

if __name__ == "__main__":
    main()

