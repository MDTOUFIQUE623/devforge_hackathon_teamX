"""
Test script for spaCy-based entity extraction.
Tests the enhanced entity extraction using spaCy NER.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ingestion.ingest_pipeline import IngestionPipeline


def test_spacy_extraction():
    """Test spaCy entity extraction."""
    print("=" * 70)
    print("SPACY ENTITY EXTRACTION TEST")
    print("=" * 70)
    print()
    
    # Initialize pipeline
    print("[1/3] Initializing IngestionPipeline...")
    try:
        pipeline = IngestionPipeline(use_spacy=True)
        print(f"   ✅ Pipeline initialized")
        print(f"   📊 spaCy available: {pipeline.use_spacy}")
        if pipeline.use_spacy:
            print(f"   📊 spaCy model: {pipeline.spacy_model_name}")
        else:
            print("   ⚠️  spaCy not available - will use simple extraction")
            print("   💡 To enable spaCy, run: python -m spacy download en_core_web_sm")
    except Exception as e:
        print(f"   ❌ Failed to initialize: {e}")
        return
    print()
    
    # Create test document
    print("[2/3] Creating test document...")
    test_text = """
    John Smith is a software engineer at Microsoft Corporation in Seattle.
    He works on machine learning projects and artificial intelligence.
    Microsoft is located in Redmond, Washington.
    Sarah Johnson, the CTO of Google, announced new AI initiatives.
    Google's headquarters are in Mountain View, California.
    """
    
    # Create a temporary test file
    test_file = Path("data/test_spacy.txt")
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text(test_text)
    print(f"   ✅ Created test file: {test_file}")
    print()
    
    # Process document
    print("[3/3] Processing document and extracting entities...")
    try:
        result = pipeline.run(str(test_file))
        
        print(f"   ✅ Document processed successfully")
        print(f"   📄 Paragraphs: {len(result['paragraphs'])}")
        print(f"   🏷️  Entities: {len(result['entities'])}")
        print(f"   🔗 Relationships: {len(result['relationships'])}")
        print()
        
        # Display entities
        if result['entities']:
            print("   📋 Extracted Entities:")
            for entity in result['entities'][:10]:  # Show first 10
                label = entity.get('label', 'Unknown')
                name = entity.get('metadata', {}).get('name', entity.get('id', 'Unknown'))
                spacy_label = entity.get('metadata', {}).get('spacy_label', 'N/A')
                print(f"      • {name} ({label}) [spaCy: {spacy_label}]")
            if len(result['entities']) > 10:
                print(f"      ... and {len(result['entities']) - 10} more")
        print()
        
        # Display relationships
        if result['relationships']:
            print("   🔗 Extracted Relationships:")
            for rel in result['relationships'][:10]:  # Show first 10
                start_id = rel.get('start', 'Unknown')
                end_id = rel.get('end', 'Unknown')
                rel_type = rel.get('type', 'Unknown')
                
                # Get entity names
                start_entity = next((e for e in result['entities'] if e['id'] == start_id), None)
                end_entity = next((e for e in result['entities'] if e['id'] == end_id), None)
                
                start_name = start_entity.get('metadata', {}).get('name', start_id) if start_entity else start_id
                end_name = end_entity.get('metadata', {}).get('name', end_id) if end_entity else end_id
                
                print(f"      • {start_name} --[{rel_type}]--> {end_name}")
            if len(result['relationships']) > 10:
                print(f"      ... and {len(result['relationships']) - 10} more")
        print()
        
        # Clean up
        test_file.unlink()
        print("   🧹 Cleaned up test file")
        
    except Exception as e:
        print(f"   ❌ Processing failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)
    print()
    print("💡 To use spaCy entity extraction:")
    print("   1. Install spaCy: pip install spacy")
    print("   2. Download model: python -m spacy download en_core_web_sm")
    print("   3. The pipeline will automatically use spaCy when available!")


if __name__ == "__main__":
    test_spacy_extraction()

