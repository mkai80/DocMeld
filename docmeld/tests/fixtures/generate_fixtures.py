"""Generate test fixture PDFs programmatically using PyMuPDF."""
from __future__ import annotations

from pathlib import Path

import fitz


def create_sample_simple() -> None:
    """Create a 3-page PDF with text, one title, and one table."""
    output = Path(__file__).parent / "sample_simple.pdf"
    doc = fitz.open()

    # Page 1: Title + text
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "Executive Summary", fontsize=18, fontname="helv")
    page.insert_text(
        (72, 110),
        "This is a sample document for testing the DocMeld pipeline.\n"
        "It contains text, tables, and multiple pages.",
        fontsize=11,
        fontname="helv",
    )

    # Page 2: Table-like content + text
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "Financial Results", fontsize=14, fontname="helv")
    page.insert_text(
        (72, 110),
        "The following table shows quarterly results:\n\n"
        "Revenue    | Q1    | Q2    | Q3\n"
        "Product A  | $100  | $120  | $130\n"
        "Product B  | $200  | $210  | $220\n"
        "Total      | $300  | $330  | $350\n",
        fontsize=11,
        fontname="helv",
    )

    # Page 3: More text
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "Conclusion", fontsize=14, fontname="helv")
    page.insert_text(
        (72, 110),
        "In conclusion, the company has shown strong growth across all segments.\n"
        "We expect continued momentum in the coming quarters.",
        fontsize=11,
        fontname="helv",
    )

    doc.save(str(output))
    doc.close()


def create_sample_complex() -> None:
    """Create a 5-page PDF with multi-level titles, tables, and mixed content."""
    output = Path(__file__).parent / "sample_complex.pdf"
    doc = fitz.open()

    # Page 1: Top-level title + intro
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "Annual Report 2025", fontsize=20, fontname="helv")
    page.insert_text((72, 110), "Company Overview", fontsize=16, fontname="helv")
    page.insert_text(
        (72, 150),
        "This annual report covers the fiscal year 2025.\n"
        "The company achieved record revenue and expanded into new markets.",
        fontsize=11,
        fontname="helv",
    )

    # Page 2: Sub-section with table
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "Revenue Breakdown", fontsize=14, fontname="helv")
    page.insert_text(
        (72, 110),
        "Segment    | Revenue | Growth\n"
        "Cloud      | $500M   | 25%\n"
        "Enterprise | $300M   | 15%\n"
        "Consumer   | $200M   | 10%\n",
        fontsize=11,
        fontname="helv",
    )
    page.insert_text(
        (72, 250),
        "Cloud segment continues to be the primary growth driver.",
        fontsize=11,
        fontname="helv",
    )

    # Page 3: Another sub-section
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "Operating Expenses", fontsize=14, fontname="helv")
    page.insert_text(
        (72, 110),
        "Category   | Amount  | % Revenue\n"
        "R&D        | $150M   | 15%\n"
        "Sales      | $100M   | 10%\n"
        "G&A        | $50M    | 5%\n",
        fontsize=11,
        fontname="helv",
    )

    # Page 4: New top-level section
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "Strategic Outlook", fontsize=16, fontname="helv")
    page.insert_text((72, 110), "Growth Initiatives", fontsize=14, fontname="helv")
    page.insert_text(
        (72, 150),
        "The company plans to invest heavily in AI and machine learning.\n"
        "Key initiatives include:\n"
        "- Expanding cloud infrastructure\n"
        "- Launching new enterprise products\n"
        "- Entering emerging markets",
        fontsize=11,
        fontname="helv",
    )

    # Page 5: Conclusion
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 72), "Summary and Outlook", fontsize=14, fontname="helv")
    page.insert_text(
        (72, 110),
        "FY2025 was a transformative year for the company.\n"
        "We are well-positioned for continued growth in FY2026.",
        fontsize=11,
        fontname="helv",
    )

    doc.save(str(output))
    doc.close()


if __name__ == "__main__":
    create_sample_simple()
    create_sample_complex()
    print("Test fixtures created successfully.")
