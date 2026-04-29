# Security Control Coverage Mapper

Parses security policy documents (PDF, DOCX, plain text) and maps them against four control frameworks to produce a coverage heatmap and gap analysis report.

## Supported Frameworks

| Framework | Controls | Format |
|-----------|----------|--------|
| ISO/IEC 27001:2022 Annex A | 15 | A.5.1, A.5.4, ... |
| NIST Cybersecurity Framework (CSF) | 15 | ID.AM-2, PR.AA-1, ... |
| CIS Controls v8 | 10 | CIS 1.1, CIS 2.1, ... |
| Vodafone Tier 2 (audit-aligned) | 15 | VOD-ACC-001, ... |

## Quick Start

```bash
make install
make demo          # Run against built-in demo policy
make test          # Run the test suite
```

## Usage

```bash
# Scan a file against all frameworks
python3 -m src.cli scan --file policy.md

# Scan against a specific framework
python3 -m src.cli scan --file policy.docx --framework iso27001 --output report.json

# Generate CSV output
python3 -m src.cli scan --file policy.txt --csv coverage.csv

# List available frameworks
python3 -m src.cli list-frameworks
```

## How It Works

1. **Parse** the policy document into paragraphs
2. **Extract** control-like statements using regex patterns (looks for "Control:", "Requirement:", numbered sections, and sentences with "shall"/"must")
3. **Map** extracted statements to framework controls using token-based similarity (Jaccard + keyword boost)
4. **Classify** each framework control as COVERED, PARTIAL, or GAP based on similarity threshold
5. **Report** coverage percentage, RAG status, per-category heatmap, and actionable gap remediations

## File Support

| Format | Dependency |
|--------|------------|
| .txt / .md | None (built-in) |
| .docx | python-docx |
| .pdf | pdfplumber |

The demo mode uses built-in text and requires no optional dependencies.
