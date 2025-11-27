"""
Test edge cases where HTML extraction might fail and return 0 characters
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.data_processor.unstructured_processor import UnstructuredDataProcessor
from src.utils.config import DATA_DIR

def test_html_where_all_content_is_in_data_attributes():
    """
    Test HTML where meaningful content might be in data attributes or aria-labels
    rather than text nodes
    """
    
    data_attribute_html = """<body>
    <div class="application-outlet" data-testid="main-content">
        <div class="profile-section" aria-label="John Doe Profile">
            <div class="pv-text-details__left-panel" data-testid="profile-header">
                <h1 aria-label="John Doe">John Doe</h1>
                <div aria-label="Senior Software Engineer">Senior Software Engineer</div>
            </div>
        </div>
    </div>
</body>"""
    
    print("=" * 80)
    print("Testing HTML with Data Attributes")
    print("=" * 80)
    
    processor = UnstructuredDataProcessor()
    result = processor.process_and_save(
        content=data_attribute_html,
        content_type="html",
        filename="test_data_attributes",
        output_dir=DATA_DIR
    )
    
    print(f"\nResult: {result}")
    content_length = result.get('content_length', 0)
    paragraphs = result.get('paragraphs', 0)
    
    if result["success"] and content_length > 0 and paragraphs > 0:
        print(f"\n✅ SUCCESS: {content_length} characters, {paragraphs} paragraphs")
        return True
    else:
        print(f"\n❌ FAILED: {content_length} characters, {paragraphs} paragraphs")
        return False


def test_html_with_very_short_text_nodes():
    """
    Test HTML where text is split across many very short nodes
    This might cause the fallback to filter everything out
    """
    
    short_nodes_html = """<body>
    <div>
        <span>J</span><span>o</span><span>h</span><span>n</span> <span>D</span><span>o</span><span>e</span>
    </div>
    <div>
        <span>S</span><span>e</span><span>n</span><span>i</span><span>o</span><span>r</span> 
        <span>S</span><span>o</span><span>f</span><span>t</span><span>w</span><span>a</span><span>r</span><span>e</span> 
        <span>E</span><span>n</span><span>g</span><span>i</span><span>n</span><span>e</span><span>e</span><span>r</span>
    </div>
    <div>
        <span>L</span><span>e</span><span>d</span> <span>d</span><span>e</span><span>v</span><span>e</span><span>l</span><span>o</span><span>p</span><span>m</span><span>e</span><span>n</span><span>t</span> 
        <span>o</span><span>f</span> <span>m</span><span>i</span><span>c</span><span>r</span><span>o</span><span>s</span><span>e</span><span>r</span><span>v</span><span>i</span><span>c</span><span>e</span><span>s</span>
    </div>
</body>"""
    
    print("\n" + "=" * 80)
    print("Testing HTML with Very Short Text Nodes")
    print("=" * 80)
    
    processor = UnstructuredDataProcessor()
    result = processor.process_and_save(
        content=short_nodes_html,
        content_type="html",
        filename="test_short_nodes",
        output_dir=DATA_DIR
    )
    
    print(f"\nResult: {result}")
    content_length = result.get('content_length', 0)
    paragraphs = result.get('paragraphs', 0)
    
    if result["success"] and content_length > 0 and paragraphs > 0:
        print(f"\n✅ SUCCESS: {content_length} characters, {paragraphs} paragraphs")
        if result.get('file_path'):
            saved_file = Path(result['file_path'])
            if saved_file.exists():
                saved_content = saved_file.read_text(encoding='utf-8')
                print(f"\nSaved content:\n{saved_content}")
        return True
    else:
        print(f"\n❌ FAILED: {content_length} characters, {paragraphs} paragraphs")
        return False


def test_empty_or_whitespace_only_html():
    """
    Test HTML that appears to have structure but only whitespace
    """
    
    whitespace_html = """<body>
    <div class="application-outlet">
        <div class="profile-section">
            <div class="pv-text-details__left-panel">
                <h1>   </h1>
                <div>    </div>
            </div>
        </div>
    </div>
</body>"""
    
    print("\n" + "=" * 80)
    print("Testing Whitespace-Only HTML")
    print("=" * 80)
    
    processor = UnstructuredDataProcessor()
    result = processor.process_and_save(
        content=whitespace_html,
        content_type="html",
        filename="test_whitespace",
        output_dir=DATA_DIR
    )
    
    print(f"\nResult: {result}")
    # This should fail gracefully
    if not result["success"]:
        print(f"\n✅ EXPECTED: Processing failed (whitespace only): {result.get('error', 'Unknown')}")
        return True
    else:
        content_length = result.get('content_length', 0)
        paragraphs = result.get('paragraphs', 0)
        if content_length == 0 and paragraphs == 0:
            print(f"\n✅ EXPECTED: 0 characters, 0 paragraphs (whitespace only)")
            return True
        else:
            print(f"\n⚠️ UNEXPECTED: Got {content_length} characters, {paragraphs} paragraphs")
            return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Edge Case HTML Test Suite")
    print("=" * 80)
    
    results = []
    
    results.append(("HTML with Data Attributes", test_html_where_all_content_is_in_data_attributes()))
    results.append(("HTML with Very Short Text Nodes", test_html_with_very_short_text_nodes()))
    results.append(("Whitespace-Only HTML", test_empty_or_whitespace_only_html()))
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️ Some tests failed.")

