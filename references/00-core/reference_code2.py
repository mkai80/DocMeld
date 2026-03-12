import os
import json
import uuid
import logging
import re
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import random
import string
import csv


# Add the parent directory to the path to import from core
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.tickers_map import tickers_map

# Load environment variables from .env.local
load_dotenv(".env.local")

DATA_ROOT = os.environ.get("DATA_ROOT")
if not DATA_ROOT:
    raise ValueError("DATA_ROOT environment variable not set. Please set it in .env.local file.")

BRONZE_PATH = os.path.join(DATA_ROOT, "lkhs/bronze/src")
SILVER_PATH = os.path.join(DATA_ROOT, "lkhs/silver")
GOLD_PATH = os.path.join(DATA_ROOT, "lkhs/gold")

TICKER_LIST = [
    'LLY'
]




SOURCE_FOLDER_LIST = [
    # "earnings_call_transcript",
    # "company_presentation",
    # "company_presentation_slides",
    # "earnings_slides",
    "research-ms",
    # "research-bcly",
    # "research-rbc",
    # "research-ubs",
    # "research-boa",
    # "research-db",
    # "research-wfgo",
    # "research-jfr",
    # "research-nham",
    # "research-bmo",
    # "research-roth",
    # "research-wbsh",
    # "research-jpm",
    # "research-opco",
    # "research-ppr",
    # "research-sig",
    # "research-tdc",
    # "research-isi",
    # "research-cs",
    # "expert-as"
]




def check_source_exists_in_silver(ticker, filing, silver_base_path):
    """
    Check if a source already exists in the silver path by comparing metadata.
    Uses a multi-tier matching approach with priority order:
    1. Primary: UUID match (most reliable - unique identifier)
    2. Secondary: Citation ID match (reliable - unique reference identifier)
    3. Tertiary: Accession number match (for SEC filings)
    4. Fallback: Filing date + form type match (when no unique identifiers available)
    
    Args:
        ticker: The ticker symbol
        filing: The filing metadata from bronze
        silver_base_path: Base path to silver directory
        
    Returns:
        Boolean indicating if source already exists
    """
    try:
        real_ticker = filing.get("primary_ticker", ticker)
        real_ticker = tickers_map.get(real_ticker, real_ticker)
        
        # Get the target directory structure - need to calculate dates first
        publish_date, report_date = _get_early_and_late_dates(filing)
        year_q_no = calculate_year_quarter(publish_date, report_date)
        
        time_str = generate_time_str(filing.get("form_type", ""))
        target_dir = os.path.join(silver_base_path, real_ticker, year_q_no + '_' + publish_date.replace("-", "") + time_str)
        source_dir = os.path.join(target_dir, "source")
        
        # Check if the source directory exists
        if not os.path.exists(source_dir):
            return False
            
        metadata_path = os.path.join(source_dir, "metadata.json")
        if not os.path.exists(metadata_path):
            return False
            
        # Load existing metadata
        with open(metadata_path, 'r', encoding='utf-8') as f:
            existing_metadata = json.load(f)
        
        # Check if this filing already exists by comparing key fields
        # Uses multi-tier matching: 1) UUID, 2) Citation ID, 3) Accession number, 4) Date+Type
        existing_filings = existing_metadata.get("filing_infos", [])
        current_uuid = filing.get("uuid", "")
        current_citation_id = filing.get("citation_id", "")
        current_accession = filing.get("accession_number", "")
        current_filing_date = publish_date  # Use calculated publish_date
        current_form_type = filing.get("form_type", "")
        
        logger.debug(f"Checking for duplicates - UUID: '{current_uuid}', Citation ID: '{current_citation_id}', Accession: '{current_accession}', Form: '{current_form_type}'")
        
        for existing_filing in existing_filings:
            existing_uuid = existing_filing.get("uuid", "")
            existing_citation_id = existing_filing.get("citation_id", "")
            existing_accession = existing_filing.get("accession_number", "")
            existing_filing_date = existing_filing.get("filing_date", "")
            existing_form_type = existing_filing.get("form_type", "")
            
            
            # Primary match: UUID (most reliable unique identifier)
            if current_uuid and existing_uuid and current_uuid == existing_uuid:
                logger.info(f"Source already exists in silver (UUID match): {current_uuid} ({current_form_type})")
                return True
            
            # Secondary match: Citation ID (reliable unique reference)
            if current_citation_id and existing_citation_id and current_citation_id == existing_citation_id:
                logger.info(f"Source already exists in silver (citation_id match): {current_citation_id} ({current_form_type})")
                return True
            
            # Tertiary match: accession number (for SEC filings)
            if current_accession and existing_accession and current_accession == existing_accession:
                logger.info(f"Source already exists in silver (accession match): {current_accession} ({current_form_type})")
                return True
            
            # Fallback match: filing date + form type
            if (current_filing_date == existing_filing_date and 
                current_form_type == existing_form_type and
                not current_uuid and not existing_uuid and
                not current_citation_id and not existing_citation_id and
                not current_accession and not existing_accession):
                logger.info(f"Source already exists in silver (date+type match): {current_form_type} ({current_filing_date})")
                return True
                
        return False
        
    except Exception as e:
        logger.error(f"Error checking if source exists in silver: {e}")
        return False


def get_duplicate_check_stats(ticker, silver_base_path):
    """
    Get statistics about duplicate checking for a ticker.
    
    Args:
        ticker: The ticker symbol
        silver_base_path: Base path to silver directory
        
    Returns:
        Dictionary with duplicate checking statistics
    """
    try:
        real_ticker = tickers_map.get(ticker, ticker)
        ticker_silver_path = os.path.join(silver_base_path, real_ticker)
        
        if not os.path.exists(ticker_silver_path):
            return {"total_sessions": 0, "total_filings": 0, "filings_with_highlights": 0}
            
        total_sessions = 0
        total_filings = 0
        filings_with_highlights = 0
        
        # Walk through all subdirectories to find metadata.json files
        for root, dirs, files in os.walk(ticker_silver_path):
            if os.path.basename(root) == "source":
                metadata_path = os.path.join(root, "metadata.json")
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        total_sessions += 1
                        filing_infos = metadata.get("filing_infos", [])
                        total_filings += len(filing_infos)
                        
                        for filing_info in filing_infos:
                            if filing_info.get("highlights"):
                                filings_with_highlights += 1
                                    
                    except Exception as e:
                        logger.warning(f"Error reading metadata at {metadata_path}: {e}")
                        continue
                        
        stats = {
            "total_sessions": total_sessions,
            "total_filings": total_filings,
            "filings_with_highlights": filings_with_highlights,
            "highlights_coverage": (filings_with_highlights / total_filings * 100) if total_filings > 0 else 0
        }
        
        logger.info(f"Duplicate check stats for {ticker}: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error getting duplicate check stats for {ticker}: {e}")
        return {"error": str(e)}


def _get_early_and_late_dates(doc):
    """
    Calculate the earliest and latest dates from document metadata.
    
    Args:
        doc: Document dictionary containing date fields
        
    Returns:
        Tuple of (publish_date, report_date) as strings or (None, None)
    """
    dates = []
    date_fields = ['report_date', 'filing_date', 'interview_date', 'publish_date']
    
    for field in date_fields:
        date_str = doc.get(field)
        if date_str and isinstance(date_str, str):
            try:
                # Attempt to parse date in "YYYY-MM-DD" format
                parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
                dates.append(parsed_date)
            except ValueError:
                # Ignore if the date string is not in the expected format
                continue
    
    if not dates:
        logger.warning(f"No dates found for {doc['primary_ticker']} {doc['primary_doc_description']}")
        print(f"No dates found for {doc['primary_ticker']} {doc['primary_doc_description']}")
        return None, None
    
    publish_date = max(dates).strftime("%Y-%m-%d")
    report_date = min(dates).strftime("%Y-%m-%d")
    return publish_date, report_date

def calculate_year_quarter(publish_date, report_date):
    """
    Calculate year and quarter from dates.
    
    Args:
        publish_date: Publish date string in "YYYY-MM-DD" format
        report_date: Report date string in "YYYY-MM-DD" format
        
    Returns:
        String in format "YYYYQX" (e.g., "2024Q3")
    """
    if report_date:
        try:
            date_obj = datetime.strptime(report_date, "%Y-%m-%d")
        except ValueError:
            date_obj = None
    elif publish_date:
        try:
            date_obj = datetime.strptime(publish_date, "%Y-%m-%d")
        except ValueError:
            date_obj = None
    else:
        return ""
    
    if not date_obj:
        return ""

    year = date_obj.year
    month = date_obj.month
    
    if month <= 3:
        quarter = 1
    elif month <= 6:
        quarter = 2
    elif month <= 9:
        quarter = 3
    else:
        quarter = 4
    
    return f"{year}Q{quarter}"


def setup_logging():
    """Setup logging to write to both console and log.txt file"""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(DATA_ROOT, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Define log file path
    log_file_path = os.path.join(logs_dir, "log.txt")
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Create file handler
    file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Get logger for this module
    logger = logging.getLogger(__name__)
    
    logger.info(f"Logging setup complete. Log file: {log_file_path}")
    return logger


# Setup logging
logger = setup_logging()


def convert_year_q_no_to_int(year_q_no_str):
    """
    Convert year_q_no from string format (e.g., "2024Q2") to integer format (e.g., 202402)
    
    Args:
        year_q_no_str: String in format "YYYYQX" (e.g., "2024Q2")
        
    Returns:
        Integer in format YYYYQX where Q is replaced with 0 followed by quarter number (e.g., 202402)
    """
    if not year_q_no_str or not isinstance(year_q_no_str, str):
        return 0
    
    try:
        # Extract year and quarter from format "2024Q2"
        if 'Q' in year_q_no_str:
            year_part, quarter_part = year_q_no_str.split('Q')
            year = int(year_part)
            quarter = int(quarter_part)
            # Convert to format YYYY0Q (e.g., 2024Q2 -> 202402)
            return year * 100 + quarter
        else:
            # If format is unexpected, try to return as int or 0
            return int(year_q_no_str) if year_q_no_str.isdigit() else 0
    except (ValueError, IndexError) as e:
        logger.warning(f"Error converting year_q_no '{year_q_no_str}' to int: {e}")
        return 0


def convert_date_to_timestamp(date_str):
    """
    Convert date string to UNIX timestamp integer.
    
    Args:
        date_str: Date string in format "YYYY-MM-DD" (e.g., "2024-05-31")
        
    Returns:
        Integer UNIX timestamp (e.g., 1717113600)
    """
    if not date_str or not isinstance(date_str, str):
        # Return current timestamp if no date provided
        return int(datetime.now().timestamp())
    
    try:
        # Parse date string and convert to timestamp
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return int(date_obj.timestamp())
    except (ValueError, TypeError) as e:
        logger.warning(f"Error converting date '{date_str}' to timestamp: {e}")
        # Return current timestamp as fallback
        return int(datetime.now().timestamp())



def load_src_metadatas(ticker):
    """Load source metadata file for a specific ticker"""
    metadata_path = os.path.join(BRONZE_PATH, ticker, "src_metadatas.json")
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return metadata
    except FileNotFoundError:
        logger.warning(f"Source metadata file not found for ticker {ticker}: {metadata_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading source metadata for {ticker}: {e}")
        return None


def load_src_metadata(source_dir):
    """Load source metadata file from source directory"""
    metadata_path = os.path.join(source_dir, "src_metadata.json")
    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return metadata
    except Exception as e:
        logger.error(f"Error loading source metadata for {source_dir}: {e}")
        return None


def generate_short_id(filing, src_metadata):
    """
    生成简短ID：form_type + institution + analysts + report_date + publish_date + [随机后缀]_ + filename（部分）
    """

    print(json.dumps(filing, indent=4))
    print("--------------------------------")

    # Handle None src_metadata
    if src_metadata is None:
        core_metadata = {}
    else:
        core_metadata = src_metadata.get("src_metadata", {})

    # derive report_date (earliest) and publish_date (latest) using existing helper
    publish_date, report_date = _get_early_and_late_dates(filing)
    report_date = report_date
    publish_date = publish_date
    short_id = "[filing_date]" + publish_date
    short_id += "[report_date]" + report_date


    short_id += "[report_type]" + core_metadata.get("form_type", "")
    
    # Add secondary document types if they exist
    secondary_types = core_metadata.get("secondary_doc_types", [])
    if secondary_types:
        short_id += "," + ",".join(secondary_types)

    institution = core_metadata.get("source_institution", "")
    institution = institution.lower()

    if "s_p_" in institution:
        institution.replace("s_p_", "sp_")
    elif "bloomberg" in institution:
        institution = "bloomberg"
    elif "wsj" in institution:
        institution = "wsj"

    short_id += "[source_institution]" + institution

    names = ""
    for analyst in filing.get("lead_analysts", []):
        analyst = analyst.lower()
        analyst = analyst.replace(" ", "_")
        analyst = analyst.replace("(", "_")
        analyst = analyst.replace(")", "_")
        analyst = analyst.replace("__", "_")

        if analyst.endswith("_cfa"):
            analyst = analyst[:-4]
        names += analyst + ","
    if names.endswith(","):
        names = names[:-1]
    # short_id += "[primary_analysts]" + names


    short_id += f"[{filing.get('citation_id', '')}]"

    logger.debug(f"Generated short ID: '{short_id}'")
    return short_id

    


def generate_time_str(form_type):
    """
    Generate time string based on when different form types typically occur.
    Times are in 24-hour format: _HHMMSS_
    
    Args:
        form_type: The form type string
        
    Returns:
        Time string in format _HHMMSS_
    """
    form_type_to_time_str = {
        # SEC Forms - Filed after market close or pre-market
        "10_k": "_203000_",        # 8:30 PM - Annual reports after market close
        "10_q": "_200000_",        # 8:00 PM - Quarterly reports after market close
        "8_k": "_163000_",         # 4:30 PM - Current reports after market close
        "6_k": "_210000_",         # 9:00 PM - Foreign company reports
        "20_f": "_213000_",        # 9:30 PM - Foreign annual reports
        "s_1": "_190000_",         # 7:00 PM - Registration statements
        "s_1a": "_190030_",        # 7:00:30 PM - Registration amendments
        "f_1": "_191000_",         # 7:10 PM - Foreign registration
        "f_1a": "_191030_",        # 7:10:30 PM - Foreign registration amendments
        "424b3": "_080000_",       # 8:00 AM - Prospectus before market open
        "424b4": "_080030_",       # 8:00:30 AM - Prospectus variants
        "424b5": "_081000_",       # 8:10 AM - Prospectus supplements
        "14a": "_090000_",         # 9:00 AM - Proxy statements in morning
        "form_3": "_183000_",      # 6:30 PM - Insider trading forms
        
        # Research Report Types - Based on typical publication timing
        "stock_research": "_070500_",      # 6:30 AM - Pre-market research
        "company_presentation": "_170500_",      # 5:05 PM - Pre-market research
        "company_presentation_slides": "_170501_",      # 5:05 PM - Pre-market research
        "industry_research": "_063000_",      # 6:30 AM - Pre-market research
        "initiation_report": "_070000_",      # 7:00 AM - Coverage initiation pre-market
        "meeting_update": "_173000_",         # 5:30 PM - After market close
        "quarterly_update": "_100500_",       # 10:05 AM - 1 hour after earnings as specified
        "rating_pt_change": "_093000_",       # 9:30 AM - Pre-market to impact trading
        "earnings_preview": "_073000_",       # 7:30 AM - Before earnings, pre-market
        "investor_presentation": "_170000_",  # 5:00 PM - After market close
        "strategy_session": "_140000_",       # 2:00 PM - During market hours
        "kpi_tracking": "_110000_",           # 11:00 AM - Mid-morning analysis
        "inter_quarter_comment": "_153000_",  # 3:30 PM - Late trading day
        "special_event_comment": "_160000_",  # 4:00 PM - Event-driven commentary
        "post_call_update": "_100500_",       # 10:05 AM - Post-earnings analysis
        "top_picker": "_180000_",             # 6:00 PM - After market analysis
        "earnings_call_transcript": "_183000_", # 6:30 PM - After earnings call
        "earnings_slides": "_171500_",        # 5:15 PM - With earnings presentation
        "earnings_release": "_090500_",       # 9:05 AM - Pre-market earnings
        "annual_report": "_200000_",          # 8:00 PM - Annual reports after close
        "quarterly_report": "_193000_",       # 7:30 PM - Quarterly reports after close
        "expert_network": "_120000_",       # 12:00 PM - Midday interviews
        "ma_call_transcript": "_183001_",  # 6:30 PM - After market close
        "special_call_transcript": "_183002_",  # 6:30 PM - After market close
        "shareholder_call_transcript": "_183003_",  # 6:30 PM - After market close
        "investor_day_slides": "_150000_",  # 3:00 PM - After market close
        "conference_presentation": "_160000_",  # 4:00 PM - Conference presentations
        
        # Generic/Other - Off-hours timing
        "misc": "_230000_",        # 11:00 PM - Miscellaneous late filing
        "unknown": "_235959_",      # 11:59:59 PM - Unknown types at end of day
        "missing": "_235959_"      # 11:59:59 PM - Missing types at end of day
    }
    
    # Clean and normalize form_type (same logic as get_form_type_code)
    if not form_type:
        return form_type_to_time_str["unknown"]
    
    form_type_clean = form_type.strip().lower().replace(" ", "_").replace("-", "_")
    
    # Direct lookup
    if form_type_clean in form_type_to_time_str:
        return form_type_to_time_str[form_type_clean]
    
    # Fallback to misc timing for unknown form types
    logger.debug(f"Using fallback time for unknown form_type '{form_type}'")
    return form_type_to_time_str["misc"]

def generate_fact_view_type(form_type):

    # Form type to 3-character code mapping
    form_type_codes = {
        # SEC Forms
        "10_k": "facts",
        "10_q": "facts",
        "8_k": "facts",
        "6_k": "facts",
        "20_f": "facts",
        "s_1": "facts",
        "s_1a": "facts",
        "f_1": "facts",
        "f_1a": "facts",
        "424b3": "facts",
        "424b4": "facts", 
        "424b5": "facts",
        "14a": "facts",
        "form_3": "facts",
        
        # Research Report Types
        "stock_research": "views",
        "company_presentation": "views",
        "company_presentation_slides": "views",
        "industry_research": "views",
        "initiation_report": "views",
        "meeting_update": "views",
        "quarterly_update": "views",
        "rating_pt_change": "views", 
        "earnings_preview": "views",
        "investor_presentation": "views",
        "strategy_session": "views",
        "kpi_tracking": "views",
        "inter_quarter_comment": "views",
        "special_event_comment": "views",
        "post_call_update": "views",
        "top_picker": "views",
        "earnings_call_transcript": "views",
        "earnings_slides": "views",
        "earnings_release": "views",
        "annual_report": "views",
        "quarterly_report": "views",
        "expert_network": "views",
        "ma_call_transcript": "views",  # Added from file_context_4
        "special_call_transcript": "views",  # Added from file_context_4
        "shareholder_call_transcript": "views",  # Added from file_context_4
        "investor_day_slides": "views",  # Added from file_context_4
        "conference_presentation": "views",  # Conference presentations
        
        # Generic/Other
        "misc": "views",
        "unknown": "views",
        "missing": "views"
    }

    if not form_type:
        return "views"
    
    form_type_clean = form_type.strip().lower().replace(" ", "_").replace("-", "_")
    
    if form_type_clean in form_type_codes:
        return form_type_codes[form_type_clean]
    
    # Fallback: create code from first 3 characters
    # Remove special characters and take first 3 alphanumeric chars
    clean_chars = ''.join(c for c in form_type_clean if c.isalnum())
    if len(clean_chars) >= 3:
        fallback_code = clean_chars[:3].upper()
    elif len(clean_chars) > 0:
        fallback_code = (clean_chars + "XX")[:3].upper()
    else:
        fallback_code = "UNK"
    
    logger.debug(f"Using fallback code '{fallback_code}' for form_type '{form_type}'")
    return "views"



def get_form_type_code(form_type):
    """
    Get unique 3-character code for each form type.
    
    Args:
        form_type: The form type string
        
    Returns:
        3-character code for the form type
    """
    # Form type to 3-character code mapping
    form_type_codes = {
        # SEC Forms
        "10_k": "10K",
        "10_q": "10Q",
        "8_k": "08K",
        "6_k": "06K",
        "20_f": "20F",
        "s_1": "S01",
        "s_1a": "S1A",
        "f_1": "F01",
        "f_1a": "F1A",
        "424b3": "B03",
        "424b4": "B04", 
        "424b5": "B05",
        "14a": "14A",
        "form_3": "F03",
        
        # Research Report Types
        "stock_research": "STR",
        "industry_research": "IDR",
        "initiation_report": "INI",
        "meeting_update": "MUP",
        "quarterly_update": "QUP",
        "rating_pt_change": "RPC", 
        "earnings_preview": "EPR",
        "investor_presentation": "IPR",
        "strategy_session": "SSN",
        "kpi_tracking": "KPI",
        "inter_quarter_comment": "IQC",
        "special_event_comment": "SPE",
        "post_call_update": "PCU",
        "top_picker": "TPK",
        "earnings_call_transcript": "ECT",
        "earnings_slides": "ESL",
        "earnings_release": "ERL",
        "annual_report": "ANN",
        "quarterly_report": "QTR",
        "expert_network": "EPT",
        "company_presentation": "CPR",
        "company_presentation_slides": "CPS",
        "investor_presentation_slides": "IPS",
        "investor_day_slides": "IDS",
        "ma_call_transcript": "MCT",
        "special_call_transcript": "SCT",
        "shareholder_call_transcript": "SCT",
        "conference_presentation": "CFP",
        
        # Generic/Other
        "misc": "MSC",
        "unknown": "MSC",
        "missing": "MSC"
    }
    
    # Clean and normalize form_type
    if not form_type:
        return "MSC"
    
    form_type_clean = form_type.strip().lower().replace(" ", "_").replace("-", "_")
    
    # Direct lookup
    for key, code in form_type_codes.items():
        if key == form_type_clean:
            return code
    
    # Fallback: create code from first 3 characters
    # Remove special characters and take first 3 alphanumeric chars
    clean_chars = ''.join(c for c in form_type_clean if c.isalnum())
    if len(clean_chars) >= 3:
        fallback_code = clean_chars[:3].upper()
    elif len(clean_chars) > 0:
        fallback_code = (clean_chars + "XX")[:3].upper()
    else:
        fallback_code = "UNK"
    
    logger.debug(f"Using fallback code '{fallback_code}' for form_type '{form_type}'")
    return fallback_code


def _table_meets_threshold(markdown_table: str) -> bool:
    """
    Check if a markdown table meets the threshold (more than 1 data row).
    
    Args:
        markdown_table: Markdown table string
        
    Returns:
        True if table has more than 1 data row, False otherwise
    """
    try:
        lines = [l.strip() for l in markdown_table.strip().split('\n') if l.strip()]
        
        # Count data rows (excluding header and separator)
        data_row_count = 0
        for i, line in enumerate(lines):
            if i == 0:
                # First line is header
                continue
            # Check if it's a separator line (contains only |, -, :, and spaces)
            if all(c in '-|: ' for c in line):
                # This is the separator, skip it
                continue
            # This is a data row
            data_row_count += 1
        
        # Threshold: more than 1 data row
        return data_row_count > 1
    except Exception as e:
        # If we can't parse it, assume it meets threshold to be safe
        logger.warning(f"Could not check table threshold: {e}")
        return True


def create_soft_link(source_path, target_path):
    """Create soft link from source to target"""
    try:
        # Check if source file exists and is a file
        if not os.path.exists(source_path):
            logger.warning(f"Source file does not exist: {source_path}")
            return False
        
        if not os.path.isfile(source_path):
            logger.warning(f"Source path is not a file: {source_path}")
            return False
        
        # Ensure target directory exists
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Remove existing link/file if it exists
        if os.path.exists(target_path) or os.path.islink(target_path):
            os.remove(target_path)
        
        # Create soft link
        os.symlink(source_path, target_path)
        logger.debug(f"Created soft link: {source_path} -> {target_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating soft link {source_path} -> {target_path}: {e}")
        return False


def create_readable_md(source_json_path, output_md_path, short_id):
    """Create readable MD file from JSON file"""
    try:
        with open(source_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        md_content = ""
        current_page_no = 1
        table_counter = 0

        for element in data:
            if element["page_no"] > current_page_no:
                md_content += "\n\nPage " + str(current_page_no) + "\n\n---\n\n"
                current_page_no = element["page_no"]

            if element["type"] == "title":
                md_content += "#" + "#" * element["level"] + " " + element["content"] + "\n"
            elif element["type"] == "text":
                md_content += element["content"] + "\n"
            elif element["type"] == "table":
                formatted_table = element["content"]
                summary = element.get("summary", "")
                # Check if table meets threshold
                if _table_meets_threshold(formatted_table):
                    # Output with table number
                    table_counter += 1
                    md_content += f"[[Table{table_counter}]]\n"
                    if summary:
                        md_content += summary + "\n"
                    md_content += formatted_table + f"\n[/Table{table_counter}]\n\n"
                else:
                    # Output small table without number
                    md_content += f"[[Table]]\n"
                    md_content += formatted_table + f"\n[/Table]\n\n"
            elif element["type"] == "image":
                image_name = element["image_name"]
                image_content = f"![image]({image_name})\n"
                if len(element["content"]) > 10:
                    image_content += f"{element['content']}\n"
                image_content += f"[/IMG]\n\n"
                
                md_content += image_content

        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        logger.info(f"Created readable MD file: {output_md_path}")
        return True

    except Exception as e:
        logger.error(f"Error creating readable MD file {output_md_path}: {e}")
        return False
    return True


def collapse_title_levels_file(file_path, data, level_limit=2, length_limit=2048, output_file=None, filing_metadata=None, src_metadata=None, short_id=None):
    """
    Collapse title levels and content into langchain-style documents/pages
    Based on collapse_titles_md.py logic
    """

    # short_id = generate_short_id(filing_metadata, src_metadata)
    fact_view_type = generate_fact_view_type(filing_metadata.get("form_type", ""))
    lead_analysts = filing_metadata.get("lead_analysts", ["issuer"])
    analysts = ''
    for analyst in lead_analysts:
        analyst = analyst.strip().lower().replace(" ", "_")
        analysts += analyst + ", "
    analysts = analysts[:-2]

    max_title_level = 12
    current_title_level = 0
    current_page_no = 0
    pages = []
    page_content = ""
    titles = ["" for _ in range(max_title_level)]
    
    logger.debug(f"Processing file for collapse: {file_path}")
    title_str = "# Start\n"

    current_date = datetime.now().strftime("%Y-%m-%d")
    table_counter = 0

    for element in data:
        if element["type"] == 'title':
            current_title_level = element["level"]

            if element["level"] >= max_title_level:
                logger.warning(f"Title level {element['level']} exceeds max_title_level {max_title_level} in file {file_path}")
                logger.warning(f"Title content: {element['content']}")
                current_title_level = max_title_level - 1
                element["level"] = current_title_level
                
            titles[element["level"]] = element["content"]

            for i in range(element["level"]+1, max_title_level):
                titles[i] = ""
                
        elif element["type"] == 'text' or element["type"] == "table" or element["type"] == "image":
            title_str = "\n".join(
                "#" * (i+1) + " " + title 
                for i, title in enumerate(titles) 
                if title
            )
            if title_str:
                title_str += "\n"

            if element["type"] == "image":
                image_content = f"\n![image]({element['image_name']})\n"
                if len(element["content"]) > 10:
                    logger.debug(f"Image content length: {len(element['content'])}")
                    image_content += f"{element['content']}\n"
                image_content += f"[/IMG]\n\n"
                page_content += title_str + image_content
            elif element["type"] == "table":
                summary = element.get("summary", "")
                # Check if table meets threshold
                if _table_meets_threshold(element["content"]):
                    table_counter += 1
                    # Output with table number
                    page_content += title_str + "\n\n"
                    page_content += f"[[Table{table_counter}]]\n"
                    if summary:
                        page_content += summary + "\n"
                    page_content += element["content"] + f"\n[/Table{table_counter}]\n\n"
                else:
                    # Output small table without number
                    page_content += title_str + "\n\n"
                    page_content += f"[[Table]]\n"
                    page_content += element["content"] + f"\n[/Table]\n\n"
            else:
                page_content += title_str + element["content"] + "\n\n"

            if len(page_content) > length_limit or (current_title_level < level_limit and current_title_level > 0 and len(page_content) > length_limit/2):
                if element["page_no"] > current_page_no:
                    current_page_no = element["page_no"]
                    page_no = 1
                else:
                    page_no += 1


                report_type = filing_metadata.get("form_type", "")
                year_q_no = convert_year_q_no_to_int(filing_metadata.get("year_q_no", ""))
                report_date = convert_date_to_timestamp(filing_metadata.get("report_date", current_date))
                # Handle cases where page_content exceeds 20000 characters
                if len(page_content) > 20000:
                    # Log the large content case with debug information
                    element_info = {
                        "type": element.get("type", ""),
                        "page_no": element.get("page_no", ""),
                        "level": element.get("level", ""),
                        "content_preview": element.get("content", "")[:200] + "..." if len(element.get("content", "")) > 200 else element.get("content", ""),
                        "is_remaining_content": False
                    }
                    
                    log_large_content_case(
                        file_path=file_path,
                        content_length=len(page_content),
                        context="main_loop",
                        filing_metadata=filing_metadata,
                        element_info=element_info,
                        output_file=output_file,
                        page_content=page_content,
                        current_titles=titles
                    )
                    
                    logger.info(f"Page content exceeds 20000 characters ({len(page_content)}), splitting into smaller chunks")
                    content_chunks = split_content_with_overlap(page_content)
                    
                    for i, chunk in enumerate(content_chunks):
                        
                        # Adjust page number for multiple chunks
                        chunk_page_no = f"page{element['page_no']}_{page_no+i}"
                        
                        page = {
                            "metadata": {
                                "uuid": str(uuid.uuid4()),
                                "source": output_file,
                                "report_type": report_type.lower().replace("-", "_"),
                                "fact_view_type": fact_view_type,
                                "source_institution": filing_metadata.get("source_institution", "sec_edgar"),
                                "primary_analysts": analysts,
                                "year_q_no": year_q_no,
                                "report_date": report_date,
                                "page_no": chunk_page_no,
                                "session_title": title_str
                            },
                            "page_content": chunk
                        }
                        pages.append(page)
                    
                    # Increment page_no for the multiple chunks created
                    page_no += len(content_chunks) - 1
                else:
                    page = {
                        "metadata": {
                            "uuid": str(uuid.uuid4()),
                            "source": output_file,
                            "report_type": report_type.lower().replace("-", "_"),
                            "fact_view_type": fact_view_type,
                            "source_institution": filing_metadata.get("source_institution", "sec_edgar"),
                            "primary_analysts": analysts,
                            "year_q_no": year_q_no,
                            "report_date": report_date,
                            "page_no": f"page{element['page_no']}_{page_no}",
                            "session_title": title_str
                        },
                        "page_content": page_content
                    }
                    pages.append(page)
                
                page_content = ""

    # Add remaining content if any
    if page_content.strip():
        if element["page_no"] > current_page_no:
            current_page_no = element["page_no"]
            page_no = 1
        else:
            page_no += 1
        
        # Handle large remaining content
        if len(page_content) > 20000:
            # Log the large content case with debug information
            element_info = {
                "type": element.get("type", ""),
                "page_no": element.get("page_no", ""),
                "level": element.get("level", ""),
                "content_preview": element.get("content", "")[:200] + "..." if len(element.get("content", "")) > 200 else element.get("content", ""),
                "is_remaining_content": True
            }
            
            log_large_content_case(
                file_path=file_path,
                content_length=len(page_content),
                context="remaining_content",
                filing_metadata=filing_metadata,
                element_info=element_info,
                output_file=output_file,
                page_content=page_content,
                current_titles=titles
            )
            
            logger.info(f"Final page content exceeds 20000 characters ({len(page_content)}), splitting into smaller chunks")
            content_chunks = split_content_with_overlap(page_content)
            
            for i, chunk in enumerate(content_chunks):
                report_type = filing_metadata.get("form_type", "")
                year_q_no = convert_year_q_no_to_int(filing_metadata.get("year_q_no", ""))
                report_date = convert_date_to_timestamp(filing_metadata.get("report_date", current_date))
                
                # Adjust page number for multiple chunks
                chunk_page_no = f"page{element['page_no']}_{page_no}"
                if len(content_chunks) > 1:
                    chunk_page_no += f"_{i+1}"
                
                page = {
                    "metadata": {
                        "uuid": str(uuid.uuid4()),
                        "source": output_file,
                        "report_type": report_type.lower().replace("-", "_"),
                        "fact_view_type": fact_view_type,
                        "source_institution": filing_metadata.get("source_institution", "sec_edgar"),
                        "primary_analysts": analysts,
                        "year_q_no": year_q_no,
                        "report_date": report_date,
                        "page_no": chunk_page_no,
                        "session_title": title_str
                    },
                    "page_content": chunk
                }
                pages.append(page)
        else:
            # Original logic for normal-sized remaining content
            report_type = filing_metadata.get("form_type", "")
            year_q_no = convert_year_q_no_to_int(filing_metadata.get("year_q_no", ""))
            report_date = convert_date_to_timestamp(filing_metadata.get("report_date", current_date))
            
            page = {
                "metadata": {
                    "uuid": str(uuid.uuid4()),
                    "source": output_file,
                    "report_type": report_type.lower().replace("-", "_"),
                    "fact_view_type": fact_view_type,
                    "source_institution": filing_metadata.get("source_institution", "sec_edgar"),
                    "primary_analysts": analysts,
                    "year_q_no": year_q_no,
                    "report_date": report_date,
                    "page_no": f"page{element['page_no']}_{page_no}",
                    "session_title": title_str
                },
                "page_content": page_content
            }
            pages.append(page)

    return pages


def collapse_title_levels_page(file_path, data, output_file=None, filing_metadata=None, src_metadata=None, short_id=None):
    """
    Collapse title levels and content into langchain-style documents/pages.
    Groups all elements from the same page_no into one page item.
    No length or level limits - each document page becomes one output page.
    
    Args:
        file_path: Source file path
        data: List of document elements with type, page_no, content, etc.
        output_file: Output filename for metadata
        filing_metadata: Filing metadata dictionary
        src_metadata: Source metadata dictionary
        short_id: Short ID for the document
    
    Returns:
        List of page dictionaries with metadata and page_content
    """
    # Prepare metadata
    fact_view_type = generate_fact_view_type(filing_metadata.get("form_type", ""))
    lead_analysts = filing_metadata.get("lead_analysts", ["issuer"])
    analysts = ''
    for analyst in lead_analysts:
        analyst = analyst.strip().lower().replace(" ", "_")
        analysts += analyst + ", "
    analysts = analysts[:-2] if analysts else ""

    max_title_level = 12
    current_page_no = 0
    pages = []
    page_content = ""
    titles = ["" for _ in range(max_title_level)]
    title_str = ""
    
    logger.debug(f"Processing file for page-based collapse: {file_path}")
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    report_type = filing_metadata.get("form_type", "")
    year_q_no = convert_year_q_no_to_int(filing_metadata.get("year_q_no", ""))
    report_date = convert_date_to_timestamp(filing_metadata.get("report_date", current_date))
    source_institution = filing_metadata.get("source_institution", "sec_edgar")

    table_counter = 0

    for element in data:
        element_page_no = element.get("page_no", 1)
        
        # Check if we've moved to a new document page
        if element_page_no > current_page_no and current_page_no > 0:
            # Save the current page content before moving to next page
            if page_content.strip():
                # Generate title string from current title hierarchy
                page = {
                    "metadata": {
                        "uuid": str(uuid.uuid4()),
                        "source": output_file,
                        "report_type": report_type.lower().replace("-", "_"),
                        "fact_view_type": fact_view_type,
                        "source_institution": source_institution,
                        "primary_analysts": analysts,
                        "year_q_no": year_q_no,
                        "report_date": report_date,
                        "page_no": f"page{current_page_no}",
                        "session_title": title_str
                    },
                    "page_content": page_content.strip()
                }

                # because one page is too long and cover multiple title levels, the title_str is no longer a good reference
                title_str = "\n".join(
                    "#" * (i+1) + " " + title 
                    for i, title in enumerate(titles) 
                    if title
                )
                if title_str:
                    title_str += "\n"


                pages.append(page)
                logger.debug(f"Created page for document page {current_page_no}, content length: {len(page_content)}")
            
            # Reset for new page
            page_content = ""
            current_page_no = element_page_no
        elif current_page_no == 0:
            # First element, initialize page number
            current_page_no = element_page_no
        
        # Process element based on type
        if element["type"] == 'title':
            # Update title hierarchy
            title_level = element.get("level", 0)
            
            if title_level >= max_title_level:
                logger.warning(f"Title level {title_level} exceeds max_title_level {max_title_level} in file {file_path}")
                logger.warning(f"Title content: {element.get('content', '')}")
                title_level = max_title_level - 1
            
            titles[title_level] = element.get("content", "")
            
            # Clear lower-level titles
            for i in range(title_level + 1, max_title_level):
                titles[i] = ""
        
            if page_content == "":
                title_str = "\n".join(
                    "#" * (i+1) + " " + title 
                    for i, title in enumerate(titles) 
                    if title
                )
                if title_str:
                    title_str += "\n"

                page_content += title_str + "\n"
            else:
                page_content += "#" * (title_level + 1) + " " + element.get("content", "") + "\n\n"

        elif element["type"] in ['text', 'table', 'image']:
            # Generate title string from current title hierarchy
            title_str = "\n".join(
                "#" * (i+1) + " " + title 
                for i, title in enumerate(titles) 
                if title
            )
            if title_str:
                title_str += "\n"
            
            # Process content based on element type
            if element["type"] == "image":
                image_name = element.get("image_name", "unknown.png")
                image_content = f"\n![image]({image_name})\n"
                if len(element.get("content", "")) > 10:
                    logger.debug(f"Image content length: {len(element.get('content', ''))}")
                    image_content += f"{element.get('content', '')}\n"
                image_content += f"[/IMG]\n\n"
                page_content += image_content
            
            elif element["type"] == "table":
                table_summary = element.get("summary", "")
                table_content = element.get("content", "")
                # Check if table meets threshold
                if _table_meets_threshold(table_content):
                    # Output with table number
                    table_counter += 1
                    page_content += f"[[Table{table_counter}]]\n"
                    if table_summary:
                        page_content += table_summary + "\n\n"
                    page_content += table_content + f"\n[/Table{table_counter}]\n\n"
                else:
                    # Output small table without number
                    page_content += f"[[Table]]\n"
                    page_content += table_content + f"\n[/Table]\n\n"
            
            else:  # text
                text_content = element.get("content", "")
                page_content += text_content + "\n\n"
    
    # Save the last page if there's remaining content
    if page_content.strip():
        
        page = {
            "metadata": {
                "uuid": str(uuid.uuid4()),
                "source": output_file,
                "report_type": report_type.lower().replace("-", "_"),
                "fact_view_type": fact_view_type,
                "source_institution": source_institution,
                "primary_analysts": analysts,
                "year_q_no": year_q_no,
                "report_date": report_date,
                "page_no": f"page{current_page_no}",
                "session_title": title_str
            },
            "page_content": page_content.strip()
        }
        pages.append(page)
        logger.debug(f"Created final page for document page {current_page_no}, content length: {len(page_content)}")
    
    logger.info(f"Created {len(pages)} pages from {len(data)} elements (page-based grouping)")
    return pages


def collapse_titles_md(source_json_path, output_jsonl_path, level_limit=2, length_limit=2048, filing_metadata=None, src_metadata=None, short_id=None):
    """
    Load JSON file, collapse title levels, and save as JSONL file
    Based on collapse_titles_md.py logic
    """
    try:
        # Load JSON data
        with open(source_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Use relative path for source metadata
        relative_source = source_json_path.replace(DATA_ROOT, "")
        
        output_file = os.path.splitext(os.path.basename(output_jsonl_path))[0] + ".pdf"
        # Process data using page-based collapse function
        pages = collapse_title_levels_page(relative_source, data, output_file=output_file, filing_metadata=filing_metadata, src_metadata=src_metadata, short_id=short_id)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_jsonl_path), exist_ok=True)
        
        # Write JSONL file
        with open(output_jsonl_path, 'w', encoding='utf-8') as f:
            for page in pages:
                f.write(json.dumps(page, ensure_ascii=False) + '\n')
        
        logger.info(f"Created JSONL file with {len(pages)} pages: {output_jsonl_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating JSONL from {source_json_path} to {output_jsonl_path}: {e}")
        return False

def create_metadata_file(output_dir, processed_files, filing_metadata, source_folder, src_metadata):
    """Create metadata.json file in the source directory with information about processed files"""
    try:
        # Calculate total size of all processed files
        total_size_bytes = 0
        filenames = []
        formats = set()
        
        for file_path in processed_files:
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                total_size_bytes += file_size
                filename = os.path.basename(file_path)
                filenames.append(filename)
                
                # Extract format from file extension
                ext = os.path.splitext(filename)[1][1:]  # Remove the dot
                if ext:
                    formats.add(ext)
        
        # Handle None src_metadata
        if src_metadata is None:
            core_metadata = {}
        else:
            core_metadata = src_metadata.get("src_metadata", {})
        
        # Create metadata structure
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "filenames": sorted(filenames),
            "formats": sorted(list(formats)),
            "total_size_bytes": total_size_bytes,
            "extraction_status": "completed",
            "filing_infos": [{
                "uuid": filing_metadata.get("uuid", ""),
                "citation_id": filing_metadata.get("citation_id", ""),
                "fiscal_quarter": filing_metadata.get("fiscal_quarter", ""),
                "ticker": filing_metadata.get("ticker", ""),
                "form_type": core_metadata.get("form_type", ""),
                "accession_number": filing_metadata.get("accession_number", ""),
                "filing_date": filing_metadata.get("publish_date", ""),
                "report_date": convert_date_to_timestamp(filing_metadata.get("report_date", "")),
                "company_name": filing_metadata.get("company_name", ""),
                "cik": filing_metadata.get("cik", ""),
                "year_q_no": convert_year_q_no_to_int(filing_metadata.get("year_q_no", "")),

                "classification_justification": core_metadata.get("classification_justification", ""),
                "secondary_labels": core_metadata.get("secondary_doc_types", []),
                "source_institution": core_metadata.get("source_institution", ""),
                "lead_analysts": core_metadata.get("lead_analysts", []),
                "highlights": core_metadata.get("highlights", [])
                
            }],
            "file_count": len(filenames),
            "processing_type": source_folder
        }
        
        # Write metadata file
        metadata_path = os.path.join(output_dir, "metadata.json")

        # if metadata.json already exists, load it to metadata_old
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata_old = json.load(f)
            
            # Check if new filing already exists based on accession_number
            new_filing_info = metadata["filing_infos"][0]  # Current filing info
            existing_accession_numbers = {filing["accession_number"] for filing in metadata_old.get("filing_infos", [])}
            
            # Only add if this filing doesn't already exist
            if new_filing_info["accession_number"] not in existing_accession_numbers:
                # Merge new filing with existing metadata
                metadata["filenames"] = metadata_old["filenames"] + metadata["filenames"]
                metadata["formats"] = metadata_old["formats"] + metadata["formats"]
                metadata["total_size_bytes"] = metadata_old["total_size_bytes"] + metadata["total_size_bytes"]
                metadata["file_count"] = metadata_old["file_count"] + metadata["file_count"]
                metadata["filing_infos"] = metadata_old["filing_infos"] + metadata["filing_infos"]
            else:
                # Filing already exists, keep the old metadata
                print(f"Filing {new_filing_info['accession_number']} already exists, skipping duplicate")
                metadata = metadata_old

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
        
        logger.info(f"Created metadata.json with {len(filenames)} files: {metadata_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating metadata.json in {output_dir}: {e}")
        return False


def log_large_content_case(file_path, content_length, context, filing_metadata=None, element_info=None, output_file=None, page_content=None, current_titles=None):
    """
    Log cases where page_content exceeds 20000 characters to a dedicated log file
    
    Args:
        file_path: Source file path being processed
        content_length: Length of the page_content
        context: Context where this occurred ("main_loop" or "remaining_content")
        filing_metadata: Metadata about the filing
        element_info: Information about the current element being processed
        output_file: Output file path
        page_content: The actual page content for preview
        current_titles: Current title hierarchy
    """
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "content_length": content_length,
            "context": context,
            "filing_metadata": filing_metadata or {},
            "element_info": element_info or {},
            "output_file": output_file,
            "threshold_exceeded_by": content_length - 20000,
            "current_titles": current_titles or [],
            "page_content_preview": page_content[:500] + "..." if page_content and len(page_content) > 500 else page_content or "N/A"
        }
        
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(DATA_ROOT, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Write to log.txt file
        log_file_path = get_large_content_log_path()
        
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False, indent=2) + "\n")
            f.write("-" * 80 + "\n")  # Separator for readability
        
        logger.info(f"Large content case logged: {content_length} chars in {file_path} ({context})")
        
    except Exception as e:
        logger.error(f"Error logging large content case: {e}")


def truncated_doc_name(filename, length=0, max_length=100):
    """
    Truncate the document name to 100 characters
    """

    # 替换空格为下划线
    filename = filename.replace("\\", "_")
    filename = filename.replace("/", "_")
    filename = filename.replace(":", "_")
    filename = filename.replace("*", "_")
    filename = filename.replace("?", "_")
    filename = filename.replace("\"", "_")
    filename = filename.replace("<", "_")
    filename = filename.replace(" ", "_")
    # 只保留字母数字、-、_
    filename = ''.join(c for c in filename if c.isalnum() or c in "-_")
    filename = filename.lower()

    # keep the len(filename) + length < 100
    if length > 0:
        if len(filename) + length < max_length:
            return filename
        else:
            return filename[:max_length - length]
    else:
        return filename[:max_length]

    return filename


def process_filing(ticker, filing, bronze_base_path, silver_base_path):
    """Process a single filing and create soft links + .jsonl file"""
    filename = filing["filename"]
    filepath = filing["filepath"]
    form_type = filing["form_type"]

    for source_folder in SOURCE_FOLDER_LIST:
        if ("/" + source_folder + "/") in filepath:
            source_folder = source_folder
            break
        else:
            source_folder = "unknown"
    
    logger.debug(f"Starting to process filing {filename} ({form_type}) for {ticker}")

    filing["publish_date"], filing["report_date"] = _get_early_and_late_dates(filing)
    filing["year_q_no"] = calculate_year_quarter(filing["publish_date"], filing["report_date"])
    
    # Check if this source already exists in silver path
    if check_source_exists_in_silver(ticker, filing, silver_base_path):
        logger.info(f"Skipping duplicate filing {filename} ({form_type}) for {ticker} - already exists in silver")
        print(f"SKIP: Duplicate filing {filename} ({form_type}) for {ticker} - already exists in silver")
        return True  # Return True to indicate successful skip
    
    # Find the source directory in bronze (absolute path)
    filing_dir = os.path.splitext(filepath)[0]
    source_dir = os.path.abspath(os.path.join(DATA_ROOT, filing_dir))

    src_metadata = load_src_metadata(source_dir)

    # Generate short ID
    short_id = generate_short_id(filing, src_metadata)
    
    if not os.path.exists(source_dir):
        print(f"Source directory not found for {ticker}/{filename}: {source_dir}")
        print(f"bronze_base_path: {bronze_base_path}")
        print(f"filing_dir: {filing_dir}")
        print(f"source_dir: {source_dir}")
        logger.warning(f"Source directory not found for {ticker}/{filename}: {source_dir}")
        return False
    
    # Create target directory in silver
    # Convert year_q_no to int format for directory naming
    real_ticker = filing.get("primary_ticker", ticker)
    real_ticker = tickers_map.get(real_ticker, real_ticker)

    time_str = generate_time_str(form_type)
    target_dir = os.path.join(silver_base_path, real_ticker, filing.get("year_q_no", "") + '_' + filing["publish_date"].replace("-", "") + time_str)
    output_dir = os.path.join(target_dir, "source")

    # doc_name 只保留文件名（不含后缀和前缀路径）
    doc_name = os.path.basename(os.path.splitext(filename)[0])
    # truncated_doc = truncated_doc_name(doc_name, length=len(short_id), max_length=100)
    
    # Track processed files for metadata
    processed_files = []
    success_count = 0
    file_operations = []


    source_file = os.path.abspath(os.path.join(source_dir, doc_name))   # files base name in lower level
    source_pdf_file = os.path.abspath(os.path.join(DATA_ROOT, filepath))
    output_file = os.path.join(output_dir, f"{short_id}.pdf")

    # Create output directory
    try:
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"Created output directory: {output_dir}")
    except Exception as e:
        logger.error(f"Failed to create output direcory {output_dir} for {ticker}/{filename}: {e}")
        return False

    # Process HTML file
    if create_soft_link(source_pdf_file, output_file):
        success_count += 1
        processed_files.append(output_file)
        file_operations.append("PDF soft link created")
        logger.debug(f"Created PDF soft link: {source_file} -> {output_file}")
    else:
        logger.warning(f"Failed to create PDF soft link for {ticker}/{filename}: {source_file}")
        file_operations.append("HTML soft link failed")

    # Process JSON file
    source_json = os.path.abspath(source_file + ".json")
    output_json = os.path.splitext(output_file)[0] + ".json"
    if create_soft_link(source_json, output_json):
        success_count += 1
        file_operations.append("JSON soft link created")
        logger.debug(f"Created JSON soft link: {source_json} -> {output_json}")
    else:
        logger.warning(f"Failed to create JSON soft link for {ticker}/{filename}: {source_json}")
        file_operations.append("JSON soft link failed")

    # Process XLSX file
    source_xlsx = os.path.abspath(source_file + ".xlsx")
    output_xlsx = os.path.splitext(output_file)[0] + ".xlsx"
    if create_soft_link(source_xlsx, output_xlsx):
        success_count += 1
        file_operations.append("XLSX soft link created")
        logger.debug(f"Created XLSX soft link: {source_xlsx} -> {output_xlsx}")
    else:
        logger.warning(f"Failed to create XLSX soft link for {ticker}/{filename}: {source_xlsx}")
        file_operations.append("XLSX soft link failed")

    # Create MD file
    source_md = os.path.abspath(source_file + ".md")
    output_md = os.path.splitext(output_file)[0] + ".md"
    if create_readable_md(source_json, output_md, short_id):
        success_count += 1
        file_operations.append("MD file created")
        logger.debug(f"Created MD file: {output_md}")
    else:
        logger.warning(f"Failed to create MD file for {ticker}/{filename}: {output_md}")
        file_operations.append("MD file failed")

    # Create JSONL file
    output_jsonl = output_json + 'l'
    try:
        if collapse_titles_md(source_json, output_jsonl, filing_metadata=filing, src_metadata=src_metadata, short_id=short_id):
            success_count += 1
            file_operations.append("JSONL file created")
            logger.debug(f"Created JSONL file: {output_jsonl}")
        else:
            logger.warning(f"Failed to create JSONL file for {ticker}/{filename}: {output_jsonl}")
            file_operations.append("JSONL file failed")
    except Exception as e:
        logger.error(f"Exception creating JSONL file for {ticker}/{filename}: {e}")
        file_operations.append(f"JSONL file exception: {str(e)}")

    # Create metadata.json file
    if processed_files:
        try:
            filing_with_ticker = filing.copy()
            filing_with_ticker["ticker"] = real_ticker
            if create_metadata_file(output_dir, processed_files, filing_with_ticker, source_folder, src_metadata):
                success_count += 1
                file_operations.append("Metadata file created")
                logger.debug(f"Created metadata file for {ticker}/{filename}")
            else:
                logger.warning(f"Failed to create metadata file for {ticker}/{filename}")
                file_operations.append("Metadata file failed")
        except Exception as e:
            logger.error(f"Exception creating metadata file for {ticker}/{filename}: {e}")
            file_operations.append(f"Metadata file exception: {str(e)}")
    
    # Log detailed results
    total_expected_files = 6  # HTML, JSON, XLSX, MD, JSONL, Metadata
    success_rate = (success_count / total_expected_files * 100) if total_expected_files > 0 else 0
    
    logger.info(f"Processed filing {filename} ({form_type}) for {ticker}: {success_count}/{total_expected_files} files created ({success_rate:.1f}% success rate)")
    logger.debug(f"File operations for {ticker}/{filename}: {file_operations}")
    
    return success_count > 0


def correct_filing(ticker, filing):
    """Correct the filing based on the source catalog"""
    if filing["primary_ticker"] == None or filing["primary_ticker"] == "":
        filing["primary_ticker"] = ticker
    if "unknown" in filing["primary_ticker"].lower() or "missing" in filing["primary_ticker"].lower():
        filing["primary_ticker"] = ticker

    if filing["source_institution"] == 'spglobal':
        filing["source_institution"] = 'sp_global'

    if "s_p_" in filing["source_institution"].lower():
        filing["source_institution"] = filing["source_institution"].replace("s_p_", "sp_")
    if "s&p_" in filing["source_institution"].lower():
        filing["source_institution"] = filing["source_institution"].replace("s&p_", "sp_")
        
    if filing["form_type"] == "strategy_session":
        filing["form_type"] = "stock_research"

    return filing

def process_ticker(ticker):
    """Process all filings for a specific ticker"""
    logger.info(f"Processing ticker: {ticker}")
    print(f"Processing ticker: {ticker}")
    
    # Load SEC metadata for this ticker
    metadata = load_src_metadatas(ticker)
    if not metadata:
        logger.error(f"Failed to load SEC metadata for ticker {ticker} - metadata file not found or invalid")
        print(f"ERROR: Failed to load SEC metadata for ticker {ticker} - metadata file not found or invalid")
        return False, "Failed to load SEC metadata"
    
    bronze_ticker_path = os.path.join(BRONZE_PATH, ticker)
    silver_base_path = SILVER_PATH
    
    # Check if bronze directory exists
    if not os.path.exists(bronze_ticker_path):
        logger.error(f"Bronze directory not found for ticker {ticker}: {bronze_ticker_path}")
        print(f"ERROR: Bronze directory not found for ticker {ticker}: {bronze_ticker_path}")
        return False, "Bronze directory not found"
    
    total_processed = 0
    total_filings = 0
    failed_filings = []
    
    # Process all form types
    filings_by_form = metadata.get("filings_by_form", {})
    
    if not filings_by_form:
        logger.warning(f"No filings found in metadata for ticker {ticker}")
        print(f"WARNING: No filings found in metadata for ticker {ticker}")
        return False, "No filings found in metadata"
    
    logger.info(f"Found {len(filings_by_form)} form types for {ticker}: {list(filings_by_form.keys())}")
    print(f"Found {len(filings_by_form)} form types for {ticker}: {list(filings_by_form.keys())}")
    
    for form_type, filings in filings_by_form.items():
        logger.info(f"Processing {len(filings)} {form_type} filings for {ticker}")
        print(f"Processing {len(filings)} {form_type} filings for {ticker}")
        
        skipped_count = 0
        for filing in filings:
            total_filings += 1
            filing = correct_filing(ticker, filing)
            filename = filing.get("filename", "unknown")
            logger.debug(f"Processing filing {filename} ({form_type}) for {ticker}")

            filepath = filing.get("filepath", "unknown")
            # DEBUG: Print filepath and check logic
            logger.info(f"Checking filepath: {filepath}")
            print(f"Checking filepath: {filepath}")
            
            try:
                result = process_filing(ticker, filing, bronze_ticker_path, silver_base_path)
                if result:
                    total_processed += 1
                    logger.debug(f"Successfully processed filing {filename} for {ticker}")
                    print(f"SUCCESS: Processed filing {filename} for {ticker}")
                else:
                    failed_filings.append({
                        "filename": filename,
                        "form_type": form_type,
                        "reason": "process_filing returned False"
                    })
                    logger.warning(f"Failed to process filing {filename} ({form_type}) for {ticker}")
                    print(f"FAILED: Failed to process filing {filename} ({form_type}) for {ticker}")
            except Exception as e:
                failed_filings.append({
                    "filename": filename,
                    "form_type": form_type,
                    "reason": f"Exception: {str(e)}"
                })
                logger.error(f"Exception processing filing {filename} ({form_type}) for {ticker}: {e}")
                print(f"EXCEPTION: Exception processing filing {filename} ({form_type}) for {ticker}: {e}")
        
        # Log summary for this form type
        if skipped_count > 0:
            logger.info(f"Skipped {skipped_count} duplicate filings for {form_type} in {ticker}")
            print(f"Skipped {skipped_count} duplicate filings for {form_type} in {ticker}")
    
    success_rate = (total_processed / total_filings * 100) if total_filings > 0 else 0
    logger.info(f"Completed processing {ticker}: {total_processed}/{total_filings} filings processed ({success_rate:.1f}% success rate)")
    print(f"COMPLETED: {ticker} - {total_processed}/{total_filings} filings processed ({success_rate:.1f}% success rate)")
    
    if failed_filings:
        logger.warning(f"Failed filings for {ticker}: {len(failed_filings)} failures")
        print(f"WARNING: Failed filings for {ticker}: {len(failed_filings)} failures")
        for failed in failed_filings:
            ident = failed.get('accession_number', failed.get('filename', 'unknown'))
            logger.warning(f"  - {ident} ({failed.get('form_type', 'unknown')}): {failed.get('reason', 'unknown')}")
            print(f"  - {ident} ({failed.get('form_type', 'unknown')}): {failed.get('reason', 'unknown')}")
    
    return total_processed > 0, f"Processed {total_processed}/{total_filings} filings"


def get_large_content_summary():
    """
    Get a summary of all large content cases from the log file
    
    Returns:
        Dictionary with summary statistics
    """
    try:
        log_file_path = get_large_content_log_path()
        
        if not os.path.exists(log_file_path):
            return {"total_cases": 0, "message": "No large content log file found"}
        
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count the number of JSON entries (each separated by 80 dashes)
        entries = content.split("-" * 80)
        # Filter out empty entries
        valid_entries = [entry.strip() for entry in entries if entry.strip()]
        
        # Parse each JSON entry to get statistics
        total_cases = len(valid_entries)
        contexts = {"main_loop": 0, "remaining_content": 0}
        max_content_length = 0
        total_excess = 0
        
        for entry in valid_entries:
            try:
                # Find the JSON part (before the separator)
                json_part = entry.split("\n")[0]
                data = json.loads(json_part)
                
                context = data.get("context", "unknown")
                if context in contexts:
                    contexts[context] += 1
                
                content_length = data.get("content_length", 0)
                max_content_length = max(max_content_length, content_length)
                total_excess += data.get("threshold_exceeded_by", 0)
                
            except json.JSONDecodeError:
                continue
        
        summary = {
            "total_cases": total_cases,
            "contexts": contexts,
            "max_content_length": max_content_length,
            "total_excess_chars": total_excess,
            "average_excess": total_excess / total_cases if total_cases > 0 else 0,
            "log_file_path": log_file_path
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting large content summary: {e}")
        return {"error": str(e)}


def generate_processing_report(successful_tickers, failed_tickers, total_tickers, processed_count):
    """
    Generate a detailed processing report and save it to a file
    
    Args:
        successful_tickers: List of successfully processed tickers
        failed_tickers: List of failed tickers with reasons
        total_tickers: Total number of tickers
        processed_count: Number of successfully processed tickers
    """
    try:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(DATA_ROOT, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        # Generate report filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"processing_report_{timestamp}.txt"
        report_path = os.path.join(logs_dir, report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("INTERNAL EDGAR PARSER PROCESSING REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Data Root: {DATA_ROOT}\n\n")
            
            # Summary statistics
            f.write("SUMMARY STATISTICS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total tickers: {total_tickers}\n")
            f.write(f"Successfully processed: {processed_count}\n")
            f.write(f"Failed: {len(failed_tickers)}\n")
            success_rate = (processed_count / total_tickers * 100) if total_tickers > 0 else 0
            f.write(f"Success rate: {success_rate:.1f}%\n\n")
            
            # Successfully processed tickers
            if successful_tickers:
                f.write("SUCCESSFULLY PROCESSED TICKERS\n")
                f.write("-" * 40 + "\n")
                for i, ticker in enumerate(successful_tickers, 1):
                    f.write(f"{i:3d}. {ticker}\n")
                f.write(f"\nTotal: {len(successful_tickers)} tickers\n\n")
            
            # Failed tickers with reasons
            if failed_tickers:
                f.write("FAILED TICKERS\n")
                f.write("-" * 40 + "\n")
                for i, failed in enumerate(failed_tickers, 1):
                    f.write(f"{i:3d}. {failed['ticker']}\n")
                    f.write(f"     Reason: {failed['reason']}\n")
                f.write(f"\nTotal: {len(failed_tickers)} tickers\n\n")
            
            # Log file locations
            f.write("LOG FILES\n")
            f.write("-" * 40 + "\n")
            f.write(f"Main log: {get_log_file_path()}\n")
            f.write(f"Large content cases: {get_large_content_log_path()}\n")
            f.write(f"This report: {report_path}\n\n")
            
            # Large content summary
            summary = get_large_content_summary()
            f.write("LARGE CONTENT CASES SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total cases: {summary.get('total_cases', 0)}\n")
            f.write(f"Contexts: {summary.get('contexts', {})}\n")
            f.write(f"Max content length: {summary.get('max_content_length', 0)}\n")
            f.write(f"Total excess characters: {summary.get('total_excess_chars', 0)}\n")
            f.write(f"Average excess: {summary.get('average_excess', 0):.2f}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 80 + "\n")
        
        logger.info(f"Processing report generated: {report_path}")
        return report_path
        
    except Exception as e:
        logger.error(f"Error generating processing report: {e}")
        return None


def get_log_file_path():
    """Get the path to the main log file"""
    logs_dir = os.path.join(DATA_ROOT, "logs")
    return os.path.join(logs_dir, "log.txt")


def get_large_content_log_path():
    """Get the path to the large content cases log file"""
    logs_dir = os.path.join(DATA_ROOT, "logs")
    return os.path.join(logs_dir, "large_content_cases.log")


def export_ticker_documents_csv(ticker):
	"""
	扫描 SILVER 目录下该 ticker 的所有输出 source 目录，读取 metadata.json，
	将每个 PDF 的完整路径、文件名、form_type 及所有可用 metadata 字段导出为 CSV。
	返回生成的 CSV 文件路径；若无数据则返回 None。
	"""
	try:
		real_ticker = tickers_map.get(ticker, ticker)
		target_root = os.path.join(SILVER_PATH, real_ticker)
		using_gold_fallback = False
		if not os.path.exists(target_root):
			logger.warning(f"Silver directory not found for ticker {ticker}: {target_root}")
			# Fallback to GOLD if available
			gold_candidate = os.path.join(GOLD_PATH, real_ticker)
			if os.path.exists(gold_candidate):
				using_gold_fallback = True
				target_root = gold_candidate
				logger.info(f"Falling back to GOLD directory for ticker {ticker}: {target_root}")
			else:
				return None

		print(f"[EXPORT] ticker={ticker} real_ticker={real_ticker} root={target_root} fallback_to_gold={using_gold_fallback}")

		rows = []
		seen_pdf_paths = set()

		for root, dirs, files in os.walk(target_root):
			if os.path.basename(root) != "source":
				continue
			metadata_path = os.path.join(root, "metadata.json")
			if not os.path.exists(metadata_path):
				print(f"[EXPORT] skip: metadata.json not found in {root}")
				continue
			try:
				with open(metadata_path, 'r', encoding='utf-8') as f:
					metadata = json.load(f)
			except Exception as e:
				logger.warning(f"Failed to read metadata.json at {metadata_path}: {e}")
				print(f"[EXPORT] failed to read metadata: {metadata_path} error={e}")
				continue

			filing_infos = metadata.get("filing_infos", []) or [{}]
			filing_info = filing_infos[0] if isinstance(filing_infos, list) and len(filing_infos) > 0 else {}

			common_fields = {
				"ticker": filing_info.get("ticker", ""),
				"form_type": filing_info.get("form_type", ""),
				"accession_number": filing_info.get("accession_number", ""),
				"filing_date": filing_info.get("filing_date", ""),
				"report_date": filing_info.get("report_date", ""),
				"company_name": filing_info.get("company_name", ""),
				"cik": filing_info.get("cik", ""),
				"year_q_no": filing_info.get("year_q_no", 0),
				"metadata_timestamp": metadata.get("timestamp", ""),
				"processing_type": metadata.get("processing_type", ""),
				"file_count": metadata.get("file_count", 0),
				"total_size_bytes": metadata.get("total_size_bytes", 0),
			}

			for filename in metadata.get("filenames", []):
				if not isinstance(filename, str) or not filename.lower().endswith('.pdf'):
					continue
				pdf_path = os.path.join(root, filename)
				if pdf_path in seen_pdf_paths:
					continue
				seen_pdf_paths.add(pdf_path)

				# Resolve original (bronze) file path via symlink target
				try:
					bronze_path = os.path.realpath(pdf_path)
					bronze_filename = os.path.basename(bronze_path)
				except Exception:
					bronze_path = pdf_path
					bronze_filename = filename

				row = {
					"pdf_path": bronze_path,
					"pdf_filename": bronze_filename,
					"silver_pdf_path": pdf_path,
				}
				row.update(common_fields)
				rows.append(row)

		if not rows:
			logger.info(f"No PDF records found to export for ticker {ticker}")
			print(f"[EXPORT] no PDF rows found for {ticker} under {target_root}")
			return None

		# Prepare export directory
		export_dir = os.path.join(DATA_ROOT, "logs", "exports")
		os.makedirs(export_dir, exist_ok=True)
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		csv_path = os.path.join(export_dir, f"{real_ticker}_documents_{timestamp}.csv")
		print(f"[EXPORT] writing CSV to {csv_path} (rows={len(rows)})")

		# Collect all columns across rows for a comprehensive header
		all_keys = set()
		for r in rows:
			all_keys.update(r.keys())
		fieldnames = [
			"pdf_path",
			"pdf_filename",
			"silver_pdf_path",
			"form_type",
			"ticker",
			"company_name",
			"accession_number",
			"cik",
			"filing_date",
			"report_date",
			"year_q_no",
			"processing_type",
			"file_count",
			"total_size_bytes",
			"metadata_timestamp",
		]
		# Append any extra keys discovered
		for k in sorted(all_keys):
			if k not in fieldnames:
				fieldnames.append(k)

		with open(csv_path, 'w', encoding='utf-8', newline='') as csvfile:
			writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
			writer.writeheader()
			for r in rows:
				writer.writerow({k: r.get(k, "") for k in fieldnames})

		logger.info(f"Exported {len(rows)} PDF records to CSV for ticker {ticker}: {csv_path}")
		return csv_path
	except Exception as e:
		logger.error(f"Error exporting CSV for ticker {ticker}: {e}")
		return None


def main():
    """Main function to process all tickers from batch progress"""
    logger.info("Starting internal EDGAR parser")
    
    logger.info(f"Processing {len(TICKER_LIST)} tickers: {TICKER_LIST}")
    completed_tickers = TICKER_LIST
    # Process each ticker
    processed_count = 0
    failed_tickers = []
    successful_tickers = []
    
    for ticker in completed_tickers:
        # Get duplicate check statistics
        duplicate_stats = get_duplicate_check_stats(ticker, SILVER_PATH)
        
        logger.info(f"=== Starting processing for ticker: {ticker} ===")
        logger.info(f"Duplicate check stats: {duplicate_stats}")
        print(f"=== Starting processing for ticker: {ticker} ===")
        print(f"Duplicate check stats: {duplicate_stats}")
        try:
            success, message = process_ticker(ticker)
            if success:
                processed_count += 1
                successful_tickers.append(ticker)
                logger.info(f"✓ Successfully processed ticker {ticker}: {message}")
                print(f"✓ Successfully processed ticker {ticker}: {message}")
            else:
                failed_tickers.append({"ticker": ticker, "reason": message})
                logger.error(f"✗ Failed to process ticker {ticker}: {message}")
                print(f"✗ Failed to process ticker {ticker}: {message}")
        except Exception as e:
            failed_tickers.append({"ticker": ticker, "reason": f"Exception: {str(e)}"})
            logger.error(f"✗ Exception processing ticker {ticker}: {e}")
            print(f"✗ Exception processing ticker {ticker}: {e}")
            continue
        # After processing each ticker, export the consolidated CSV
        try:
            csv_path = export_ticker_documents_csv(ticker)
            if csv_path:
                logger.info(f"CSV exported for ticker {ticker}: {csv_path}")
                print(f"CSV exported for {ticker}: {csv_path}")
            else:
                logger.info(f"No CSV exported for ticker {ticker} (no records)")
                print(f"No CSV exported for ticker {ticker} (no records)")
        except Exception as e:
            logger.error(f"Failed to export CSV for ticker {ticker}: {e}")
            print(f"ERROR: Failed to export CSV for ticker {ticker}: {e}")
        logger.info(f"=== Completed processing for ticker: {ticker} ===\n")
        print(f"=== Completed processing for ticker: {ticker} ===\n")
    
    # Summary statistics
    total_tickers = len(completed_tickers)
    success_rate = (processed_count / total_tickers * 100) if total_tickers > 0 else 0
    
    logger.info(f"=== PROCESSING SUMMARY ===")
    print(f"=== PROCESSING SUMMARY ===")
    logger.info(f"Total tickers: {total_tickers}")
    print(f"Total tickers: {total_tickers}")
    logger.info(f"Successfully processed: {processed_count}")
    print(f"Successfully processed: {processed_count}")
    logger.info(f"Failed: {len(failed_tickers)}")
    print(f"Failed: {len(failed_tickers)}")
    logger.info(f"Success rate: {success_rate:.1f}%")
    print(f"Success rate: {success_rate:.1f}%")
    
    # Log successful tickers
    if successful_tickers:
        logger.info(f"Successfully processed tickers ({len(successful_tickers)}): {successful_tickers}")
        print(f"Successfully processed tickers ({len(successful_tickers)}): {successful_tickers}")
    
    # Log failed tickers with reasons
    if failed_tickers:
        logger.error(f"Failed tickers ({len(failed_tickers)}):")
        print(f"Failed tickers ({len(failed_tickers)}):")
        for failed in failed_tickers:
            logger.error(f"  - {failed['ticker']}: {failed['reason']}")
            print(f"  - {failed['ticker']}: {failed['reason']}")
    
    # Generate and log summary of large content cases
    summary = get_large_content_summary()
    logger.info("Large content cases summary:")
    print("Large content cases summary:")
    logger.info(f"  Total cases: {summary.get('total_cases', 0)}")
    print(f"  Total cases: {summary.get('total_cases', 0)}")
    logger.info(f"  Contexts: {summary.get('contexts', {})}")
    print(f"  Contexts: {summary.get('contexts', {})}")
    logger.info(f"  Max content length: {summary.get('max_content_length', 0)}")
    print(f"  Max content length: {summary.get('max_content_length', 0)}")
    logger.info(f"  Total excess characters: {summary.get('total_excess_chars', 0)}")
    print(f"  Total excess characters: {summary.get('total_excess_chars', 0)}")
    logger.info(f"  Average excess: {summary.get('average_excess', 0):.2f}")
    print(f"  Average excess: {summary.get('average_excess', 0):.2f}")
    
    # Show log file locations
    logger.info("Log files created:")
    print("Log files created:")
    logger.info(f"  Main log: {get_log_file_path()}")
    print(f"  Main log: {get_log_file_path()}")
    logger.info(f"  Large content cases: {get_large_content_log_path()}")
    print(f"  Large content cases: {get_large_content_log_path()}")
    
    # Console output
    print(f"\n=== PROCESSING COMPLETE ===")
    print(f"Total tickers: {total_tickers}")
    print(f"Successfully processed: {processed_count}")
    print(f"Failed: {len(failed_tickers)}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Main log file: {get_log_file_path()}")
    print(f"Large content log: {get_large_content_log_path()}")
    print(f"Large content cases: {summary.get('total_cases', 0)}")
    
    # Show failed tickers in console
    if failed_tickers:
        print(f"\nFailed tickers:")
        for failed in failed_tickers:
            print(f"  - {failed['ticker']}: {failed['reason']}")
    
    # Show successful tickers in console
    if successful_tickers:
        print(f"\nSuccessfully processed tickers:")
        for ticker in successful_tickers:
            print(f"  ✓ {ticker}")
    
    # Generate and save processing report
    report_path = generate_processing_report(successful_tickers, failed_tickers, total_tickers, processed_count)
    if report_path:
        print(f"\nProcessing report saved to: {report_path}")
        logger.info(f"Processing report saved to: {report_path}")
    else:
        logger.error("Failed to generate processing report")
        print("ERROR: Failed to generate processing report")


if __name__ == "__main__":
    main()
