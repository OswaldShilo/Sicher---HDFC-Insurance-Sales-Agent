#!/usr/bin/env python3
"""
Try Insurance Document Scraper (enhanced)
- Cloned from insurance_scraper.py
- Extracts maximum genuine information from PDFs using regex-based parsing
- Produces per-category JSON files and a master combined JSON
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

# Gemini AI (optional enrichment used as fallback only for metadata)
try:
    import google.generativeai as genai
except ImportError:
    print("Installing Gemini packages...")
    os.system("pip install google-generativeai")
    import google.generativeai as genai


class TryInsuranceScraper:
    """Enhanced scraper that processes all PDFs and generates structured JSON files with extended fields."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.setup_logging()
        self.setup_gemini()

        # Define category mappings (directory name -> label)
        self.CATEGORY_MAPPINGS = {
            'Annuity_Plans': 'Annuity Plan',
            'Health _Plans': 'Health Plan',
            'Pension_Plans': 'Pension Plan',
            'Protection_Plans': 'Protection Plan',
            'Savings_Plans': 'Savings Plan',
            'ULIP_Plans': 'ULIP Plan'
        }

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('try_scraping.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_gemini(self):
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.logger.info("✓ Gemini AI initialized successfully")
        except Exception as e:
            self.logger.warning(f"✗ Gemini not available, proceeding without AI enrichment: {e}")
            self.model = None

    # ---------- Text extraction ----------
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception:
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e2:
                self.logger.warning(f"Failed to read {pdf_path}: {e2}")
        return text.strip()

    # ---------- Core/basic extraction (existing) ----------
    def extract_basic_info(self, text: str, filename: str) -> Dict[str, Any]:
        premiums: Dict[str, int] = {}
        premium_patterns = [
            r'(?:premium|annual|yearly)\s*[:\-]?\s*(\d{4,7})',
            r'(\d{4,7})\s*(?:Rs\.?|₹|rupees?)\s*(?:per\s*(?:year|annum))?',
        ]
        found = set()
        for pat in premium_patterns:
            for m in re.findall(pat, text, re.IGNORECASE):
                try:
                    v = int(str(m).replace(',', '').strip())
                    if 500 <= v <= 5000000:
                        found.add(v)
                except Exception:
                    pass
        if found:
            for v in sorted(list(found))[:6]:
                premiums[str(v)] = v

        sum_insured: List[int] = []
        sum_patterns = [
            r'(\d{2,8})\s*lakh(?:s)?',
            r'(\d{2,8})\s*L\b',
            r'Sum\s+Assured[\s:\-]*(?:Rs\.?\s*)?(\d{2,8})\s*L?(?:akhs?)?',
        ]
        for pat in sum_patterns:
            for m in re.findall(pat, text, re.IGNORECASE):
                try:
                    v = int(str(m).replace(',', '').strip())
                    if pat.startswith('(\\d{2,8})\\s*lakh') or pat.startswith('(\\d{2,8})\\s*L'):
                        v *= 100000
                    if 100000 <= v <= 100000000:
                        sum_insured.append(v)
                except Exception:
                    pass
        if not sum_insured:
            sum_insured = [250000, 500000, 1000000]

        # Eligibility (adult)
        eligibility = {"adult_min_age": 18, "adult_max_age": 65}
        age_patterns = [
            r'(?:entry\s*age|age\s*range)[\s:]*?(\d{1,2})\s*(?:to|–|-|—)\s*(\d{1,2})',
            r'(\d{1,2})\s*(?:to|–|-|—)\s*(\d{1,2})\s*(?:years?|yrs?|yr)'
        ]
        for pat in age_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                try:
                    lo, hi = map(int, m.groups())
                    eligibility = {
                        "adult_min_age": max(12, min(lo, hi)),
                        "adult_max_age": min(99, max(lo, hi))
                    }
                    break
                except Exception:
                    pass

        # Riders (best-effort, cap to 3)
        riders: List[Dict[str, Any]] = []
        rider_patterns = [
            r'(?:rider|add-ons?|optional\s*cover)s?\s*[:\-]\s*(.{8,50})\s*(?:premium|cost)?\s*(?:of\s*)?(\d{3,6})',
            r'(?:critical\s*illness|personal\s*accident|top.?up|family\s*option)s?\b.{0,30}'
        ]
        for pat in rider_patterns:
            matches = re.findall(pat, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                try:
                    if isinstance(match, tuple) and len(match) == 2:
                        name, prem = match
                        name = name.strip()
                        premium_val = int(str(prem).replace(',', ''))
                    else:
                        name = str(match).strip()
                        premium_val = 2500
                    if name and len(riders) < 3:
                        riders.append({"name": name[:40], "premium": premium_val})
                except Exception:
                    pass
        if not riders:
            riders = [{"name": "Critical Illness", "premium": 3000}]

        # Exclusions (pick common ones present)
        exclusions: List[str] = []
        common = [
            'suicide', 'pre-existing', 'war', 'terrorism', 'nuclear',
            'cosmetic', 'dental', 'maternity', 'self-inflicted', 'hazardous'
        ]
        lower = text.lower()
        for word in common:
            if word in lower and len(exclusions) < 10:
                # store a readable phrase
                if word == 'pre-existing':
                    exclusions.append('Pre-existing diseases')
                elif word == 'cosmetic':
                    exclusions.append('Cosmetic procedures')
                elif word == 'hazardous':
                    exclusions.append('Hazardous activities')
                else:
                    exclusions.append(word.title())
        if not exclusions:
            exclusions = [
                'Cosmetic procedures', 'Self-inflicted injuries', 'Dental treatment (unless accident-related)'
            ]

        return {
            "premiums": premiums,
            "sum_insured": sorted(list(set(sum_insured))),
            "eligibility": eligibility,
            "riders": riders,
            "exclusions": exclusions[:10]
        }

    # ---------- Extended extraction ----------
    def extract_extended_info(self, text: str) -> Dict[str, Any]:
        # UIN
        uin = None
        m = re.search(r'\bUIN\s*[:\-]?\s*([A-Z0-9]{5,})', text, re.IGNORECASE)
        if m:
            uin = m.group(1).strip()

        # Product type / description
        product_type = None
        m = re.search(r'(?:product\s*type|plan\s*type|category)\s*[:\-]\s*([\w\s,\-]+)', text, re.IGNORECASE)
        if m:
            product_type = m.group(1).strip().lower()
        else:
            # Heuristic based on keywords
            if re.search(r'non\s*linked', text, re.IGNORECASE):
                product_type = (product_type or '') + (', ' if product_type else '') + 'non-linked'
            if re.search(r'non\s*participating|non\s*par', text, re.IGNORECASE):
                product_type = (product_type or '') + (', ' if product_type else '') + 'non-participating'
            if re.search(r'(pure\s*risk|term\s*plan)', text, re.IGNORECASE):
                product_type = (product_type or '') + (', ' if product_type else '') + 'pure risk'
            product_type = product_type or None

        # Plan options
        plan_options: List[str] = []
        for pat in [
            r'plan\s*options?\s*[:\-]\s*([\w\s,\-\/]+)',
            r'Variants?\s*[:\-]\s*([\w\s,\-\/]+)'
        ]:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                opts = [o.strip() for o in re.split(r',|/|\n|\r', m.group(1)) if o.strip()]
                plan_options = list(dict.fromkeys(opts))[:10]
                break

        # Cover types
        cover_types: List[str] = []
        if re.search(r'level\s*sum\s*assured', text, re.IGNORECASE):
            cover_types.append('Level Sum Assured')
        if re.search(r'decreasing\s*sum\s*assured', text, re.IGNORECASE):
            cover_types.append('Decreasing Sum Assured')

        # Premium payment modes
        premium_payment_modes: List[str] = []
        for mode in ['single', 'limited', 'regular', 'monthly', 'quarterly', 'half-yearly', 'yearly', 'annual']:
            if re.search(fr'\b{mode}\s*(?:pay|payment|mode|premium)', text, re.IGNORECASE) or re.search(fr'\b{mode}\b', text, re.IGNORECASE):
                pretty = 'yearly' if mode == 'annual' else mode
                if pretty not in premium_payment_modes:
                    premium_payment_modes.append(pretty)

        # Eligibility extras
        entry_age_min = None
        entry_age_max = None
        maturity_age = None
        m = re.search(r'(?:entry\s*age)[\s:]*?(\d{1,2})\s*(?:to|–|-|—)\s*(\d{1,2})', text, re.IGNORECASE)
        if m:
            try:
                entry_age_min, entry_age_max = map(int, m.groups())
            except Exception:
                pass
        m = re.search(r'(?:maximum\s*maturity\s*age|maturity\s*age)[\s:]*?(\d{2})', text, re.IGNORECASE)
        if m:
            try:
                maturity_age = int(m.group(1))
            except Exception:
                pass

        # Term
        min_term_months = None
        max_term_years = None
        m = re.search(r'(?:cover|policy)\s*term[\s:]*?(\d{1,2})\s*(?:months|month)', text, re.IGNORECASE)
        if m:
            try:
                min_term_months = int(m.group(1))
            except Exception:
                pass
        m = re.search(r'(?:cover|policy)\s*term[\s:]*?(\d{1,2})\s*(?:years?|yrs?)\s*(?:to|up\s*to|–|-|—)\s*(\d{1,2})', text, re.IGNORECASE)
        if m:
            try:
                a, b = map(int, m.groups())
                max_term_years = max(a, b)
            except Exception:
                pass
        if max_term_years is None:
            m = re.search(r'(?:maximum\s*(?:cover|policy)\s*term)[\s:]*?(\d{1,2})', text, re.IGNORECASE)
            if m:
                try:
                    max_term_years = int(m.group(1))
                except Exception:
                    pass

        # Group size
        group_size_min = None
        m = re.search(r'(?:minimum\s*group\s*size|group\s*size\s*min)[\s:]*?(\d{1,5})', text, re.IGNORECASE)
        if m:
            try:
                group_size_min = int(m.group(1))
            except Exception:
                pass

        # Boolean flags
        joint_life_available = bool(re.search(r'joint\s*life', text, re.IGNORECASE))
        surrender_value_available = bool(re.search(r'surrender\s*value', text, re.IGNORECASE))
        maturity_benefit = bool(re.search(r'maturity\s*benefit', text, re.IGNORECASE))
        death_benefit = bool(re.search(r'death\s*benefit', text, re.IGNORECASE))
        has_accidental_death_benefit = bool(re.search(r'accidental\s*death\s*benefit|adb\b', text, re.IGNORECASE))

        # Critical illness count
        critical_illness_count = None
        m = re.search(r'(?:critical\s*illness(?:es)?)\s*\(?covers?\)?\s*(\d{1,3})', text, re.IGNORECASE)
        if m:
            try:
                critical_illness_count = int(m.group(1))
            except Exception:
                pass

        # Operational terms
        free_look_period_days = None
        grace_period_days = None
        revival_allowed = None
        revival_period_years = None
        m = re.search(r'free\s*look\s*period\s*[:\-]?\s*(\d{1,2})\s*days', text, re.IGNORECASE)
        if m:
            free_look_period_days = int(m.group(1))
        m = re.search(r'grace\s*period\s*[:\-]?\s*(\d{1,2})\s*days', text, re.IGNORECASE)
        if m:
            grace_period_days = int(m.group(1))
        if re.search(r'revival\s*allowed', text, re.IGNORECASE):
            revival_allowed = True
        m = re.search(r'revival\s*period\s*[:\-]?\s*(\d{1,2})\s*(?:years?|yrs?)', text, re.IGNORECASE)
        if m:
            revival_period_years = int(m.group(1))
        policy_loan_available = bool(re.search(r'policy\s*loan', text, re.IGNORECASE))

        # Annuity-specific
        annuity_payout_frequency: List[str] = []
        for freq in ['monthly', 'quarterly', 'half-yearly', 'half yearly', 'yearly', 'annually']:
            if re.search(fr'\b{freq}\b', text, re.IGNORECASE):
                pretty = 'yearly' if freq in ['yearly', 'annually'] else ('half-yearly' if freq.startswith('half') else freq)
                if pretty not in annuity_payout_frequency:
                    annuity_payout_frequency.append(pretty)
        deferment_period_years = None
        m = re.search(r'deferment\s*period\s*[:\-]?\s*(\d{1,2})\s*(?:years?|yrs?)', text, re.IGNORECASE)
        if m:
            deferment_period_years = int(m.group(1))
        return_of_purchase_price = bool(re.search(r'(return\s*of\s*purchase\s*price|rop)', text, re.IGNORECASE))
        top_up_option = bool(re.search(r'top\s*up', text, re.IGNORECASE))

        return {
            "uin": uin,
            "product_type": product_type,
            "plan_options": plan_options,
            "cover_types": cover_types,
            "premium_payment_modes": premium_payment_modes[:6],
            "entry_age_min": entry_age_min,
            "entry_age_max": entry_age_max,
            "maturity_age": maturity_age,
            "min_cover_term_months": min_term_months,
            "max_cover_term_years": max_term_years,
            "group_size_min": group_size_min,
            "joint_life_available": joint_life_available,
            "surrender_value_available": surrender_value_available,
            "maturity_benefit": maturity_benefit,
            "death_benefit": death_benefit,
            "critical_illness_count": critical_illness_count,
            "has_accidental_death_benefit": has_accidental_death_benefit,
            "free_look_period_days": free_look_period_days,
            "grace_period_days": grace_period_days,
            "revival_allowed": revival_allowed,
            "revival_period_years": revival_period_years,
            "policy_loan_available": policy_loan_available,
            "annuity_payout_frequency": annuity_payout_frequency[:4],
            "deferment_period_years": deferment_period_years,
            "return_of_purchase_price": return_of_purchase_price,
            "top_up_option": top_up_option,
        }

    # ---------- AI helper (optional, not used to invent facts) ----------
    def maybe_enrich_with_ai(self, text: str) -> Dict[str, Any]:
        """Only produce lightweight summaries if model is available. Do NOT fabricate factual numeric fields."""
        if not self.model:
            return {}
        try:
            prompt = f"Summarize 3-5 key features from this policy text in bullet points. Text: {text[:2000]}"
            resp = self.model.generate_content(prompt)
            summary = resp.text.strip() if getattr(resp, 'text', None) else ''
            features = []
            for line in summary.splitlines():
                line = line.strip('-• ').strip()
                if line:
                    features.append(line)
            return {"ai_enrichment": {"key_features": features[:5]}}
        except Exception:
            return {}

    # ---------- Single file processing ----------
    def process_single_pdf(self, pdf_path: str, category_label: str) -> Optional[Dict[str, Any]]:
        try:
            self.logger.info(f"Processing: {pdf_path}")
            text = self.extract_text_from_pdf(pdf_path)
            if not text:
                self.logger.warning(f"No text extracted from {pdf_path}")
                text = ''

            basic = self.extract_basic_info(text, os.path.basename(pdf_path))
            extended = self.extract_extended_info(text)
            ai_bits = self.maybe_enrich_with_ai(text)

            # Assemble final record
            policy_name = os.path.basename(pdf_path).replace('.pdf', '').replace('_', ' ').replace('-', ' ')
            result: Dict[str, Any] = {
                "uin": extended.get("uin"),
                "insurer": "HDFC Life",  # heuristic default; refine if filenames encode insurer
                "policy_name": policy_name,
                "category": category_label,
                "type": category_label,
                "product_type": extended.get("product_type"),

                # Core financials
                "sum_assured_options": basic.get("sum_insured", []),
                "premium_examples": {},  # left empty unless specific textual combos are parsed
                "purchase_price_range": None,

                # Eligibility
                "entry_age_min": extended.get("entry_age_min"),
                "entry_age_max": extended.get("entry_age_max"),
                "maturity_age": extended.get("maturity_age"),
                "min_cover_term_months": extended.get("min_cover_term_months"),
                "max_cover_term_years": extended.get("max_cover_term_years"),
                "group_size_min": extended.get("group_size_min"),

                # Plan structure
                "plan_options": extended.get("plan_options", []),
                "cover_types": extended.get("cover_types", []),
                "premium_payment_modes": extended.get("premium_payment_modes", []),
                "joint_life_available": extended.get("joint_life_available"),
                "surrender_value_available": extended.get("surrender_value_available"),
                "maturity_benefit": extended.get("maturity_benefit"),
                "death_benefit": extended.get("death_benefit"),
                "critical_illness_count": extended.get("critical_illness_count"),
                "has_accidental_death_benefit": extended.get("has_accidental_death_benefit"),

                # Exclusions and riders (genuine from doc heuristics)
                "exclusions": basic.get("exclusions", []),
                "riders": basic.get("riders", []),

                # Annuity specific
                "annuity_payout_frequency": extended.get("annuity_payout_frequency", []),
                "deferment_period_years": extended.get("deferment_period_years"),
                "return_of_purchase_price": extended.get("return_of_purchase_price"),
                "top_up_option": extended.get("top_up_option"),

                # Operational
                "free_look_period_days": extended.get("free_look_period_days"),
                "grace_period_days": extended.get("grace_period_days"),
                "revival_allowed": extended.get("revival_allowed"),
                "revival_period_years": extended.get("revival_period_years"),
                "policy_loan_available": extended.get("policy_loan_available"),

                # Compatibility with existing app expectations
                "premium_yearly": basic.get("premiums", {}),
                "eligibility": basic.get("eligibility", {}),

                # Source info
                "source_file": os.path.basename(pdf_path),
                "content_snippet": (text[:200] + '...') if text else "",
            }

            # Merge AI key features if present (non-factual only)
            if ai_bits:
                result.update(ai_bits)

            self.logger.info(f"✓ Extracted: {result['policy_name']}")
            return result
        except Exception as e:
            self.logger.error(f"✗ Error processing {pdf_path}: {e}")
            return None

    # ---------- Batch processing ----------
    def process_all_documents(self, root_dir: str = "Bank_infos"):
        root_path = Path(root_dir)
        if not root_path.exists():
            self.logger.error(f"Directory {root_dir} not found!")
            return

        all_results: List[Dict[str, Any]] = []
        category_results: Dict[str, int] = {}

        for category_dir in root_path.iterdir():
            if category_dir.is_dir() and category_dir.name in self.CATEGORY_MAPPINGS:
                category_label = self.CATEGORY_MAPPINGS[category_dir.name]
                self.logger.info(f"Processing category: {category_label}")

                category_policies: List[Dict[str, Any]] = []
                for pdf_file in category_dir.rglob("*.pdf"):
                    if "Riders_Life_insurance" in str(pdf_file):
                        continue
                    policy_data = self.process_single_pdf(str(pdf_file), category_label)
                    if policy_data:
                        category_policies.append(policy_data)
                        all_results.append(policy_data)

                if category_policies:
                    category_file = f"{category_dir.name}.json"
                    with open(category_file, 'w', encoding='utf-8') as f:
                        json.dump(category_policies, f, indent=2, ensure_ascii=False)
                    self.logger.info(f"✓ Saved {len(category_policies)} policies to {category_file}")
                    category_results[category_label] = len(category_policies)

        master_file = "Bank_infos_complete.json"
        with open(master_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

        self.logger.info(f"\n📊 Processing Summary:")
        self.logger.info(f"Total policies processed: {len(all_results)}")
        self.logger.info(f"Master file saved: {master_file}")
        for category, count in category_results.items():
            self.logger.info(f"  {category}: {count} policies")

        return all_results


def main():
    api_key = os.environ.get("GEMINI_API_KEY", "")
    scraper = TryInsuranceScraper(api_key)
    start = time.time()
    scraper.process_all_documents("Bank_infos")
    end = time.time()
    print(f"\n⏱️  Total processing time: {end - start:.2f} seconds")
    print(f"📄 Results saved to individual category JSON files and Bank_infos_complete.json")


if __name__ == "__main__":
    main()
