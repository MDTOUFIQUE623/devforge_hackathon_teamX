"""
Test file for IngestionPipeline.
Run this script to verify that ingestion works and outputs JSON.
"""

import sys
from pathlib import Path

# Add project root to Python path so we can import from src
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ingestion.ingest_pipeline import IngestionPipeline
import json

def main():
    # Initialize the ingestion pipeline
    pipeline = IngestionPipeline()

    # Replace this with a path to your sample file
    sample_file = Path("data/sample.txt")  # or sample.pdf, sample.docx, sample.csv

    if not sample_file.exists():
        print(f"[ERROR] Sample file not found: {sample_file}")
        return

    # Run ingestion
    result = pipeline.run(str(sample_file))

    # Print JSON output (pretty)
    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    main()
