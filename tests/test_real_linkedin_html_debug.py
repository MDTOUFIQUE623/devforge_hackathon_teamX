"""
Debug test for real-world LinkedIn HTML that might cause "0 characters, 0 paragraphs"
This simulates what happens when a user pastes complex LinkedIn outer HTML
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.data_processor.unstructured_processor import UnstructuredDataProcessor
from src.utils.config import DATA_DIR
from bs4 import BeautifulSoup

def test_extremely_nested_linkedin_html():
    """
    Test with extremely nested LinkedIn HTML that might cause extraction issues.
    This simulates the actual structure of LinkedIn profiles with lots of nested divs.
    """
    
    # This HTML has very nested structures and might cause the processor to miss content
    nested_html = """<body dir="ltr" class="render-mode-BIGPIPE nav-v2 ember-application payment-failure-global-alert-lix-enabled-class icons-loaded boot-complete" data-t-link-to-event-attached="true">
    <div class="application-outlet">
        <div class="scaffold-layout">
            <div class="scaffold-layout__main">
                <div class="pv-profile-section">
                    <div class="pv-text-details__left-panel">
                        <div class="inline t-24 v-align-middle break-words">
                            <h1 class="text-heading-xlarge inline t-24 v-align-middle break-words">John Doe</h1>
                        </div>
                        <div class="text-body-medium break-words">
                            <div class="text-body-medium break-words">Senior Software Engineer at Tech Company</div>
                        </div>
                        <div class="text-body-small inline t-black--light break-words">
                            <span class="text-body-small inline t-black--light break-words">San Francisco Bay Area</span>
                        </div>
                    </div>
                </div>
                
                <section class="pv-profile-section experience-section">
                    <div class="pvs-list__outer-container">
                        <div class="pvs-list__paged-list-item">
                            <div class="pvs-entity">
                                <div class="pvs-entity__summary-info">
                                    <div class="t-16 t-black t-bold">
                                        <span class="t-16 t-black t-bold">Senior Software Engineer</span>
                                    </div>
                                    <div class="t-14 t-black--light t-normal">
                                        <span class="t-14 t-black--light t-normal">Tech Company</span>
                                    </div>
                                    <div class="t-14 t-black--light t-normal">
                                        <span class="t-14 t-black--light t-normal">Jan 2020 - Present · 4 yrs</span>
                                    </div>
                                </div>
                                <div class="pvs-entity__summary-info-content">
                                    <div class="t-14 t-black t-normal">
                                        <span class="t-14 t-black t-normal">Led development of microservices architecture serving 10M+ users. Implemented CI/CD pipelines reducing deployment time by 60%. Mentored junior engineers and contributed to open-source projects.</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    </div>
    
    <script type="application/json" data-json-key="voyager-decorators">
        {"data":{"entityUrn":"urn:li:collectionResponse:4HlijJjSiEXmgxSNTaZbyKnZ88db1eTefgOnimBx6wM=","elements":[{"lixTracking":{"urn":"urn:li:member:1556551351"}}]}}
    </script>
    
    <nav class="global-nav">
        <div class="nav-item">Home</div>
        <div class="nav-item">My Network</div>
    </nav>
</body>"""

    print("=" * 80)
    print("Testing Extremely Nested LinkedIn HTML")
    print("=" * 80)
    
    processor = UnstructuredDataProcessor()
    
    # First, let's see what BeautifulSoup extracts directly
    print("\n1. Direct BeautifulSoup extraction test...")
    soup = BeautifulSoup(nested_html, 'html.parser')
    for tag in soup(["script", "style", "meta", "link", "nav"]):
        tag.decompose()
    
    direct_text = soup.get_text(separator=' ', strip=True)
    print(f"Direct extraction length: {len(direct_text)} characters")
    print(f"Direct extraction preview: {direct_text[:200]}")
    
    # Now test with our processor
    print("\n2. Testing with UnstructuredDataProcessor...")
    processed_text = processor.process_html(nested_html, source_name="nested_linkedin")
    print(f"Processed text length: {len(processed_text)} characters")
    print(f"Processed text preview: {processed_text[:500]}")
    
    # Test via process_and_save
    print("\n3. Testing via process_and_save...")
    result = processor.process_and_save(
        content=nested_html,
        content_type="html",
        filename="test_nested_linkedin",
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
        if not result["success"]:
            print(f"Error: {result.get('error', 'Unknown')}")
        return False


def test_html_with_only_spans():
    """
    Test HTML that has content only in span elements (common in LinkedIn)
    This might cause issues if the processor filters out spans too aggressively
    """
    
    span_only_html = """<body>
    <div class="application-outlet">
        <div class="profile-section">
            <div class="pv-text-details__left-panel">
                <h1>
                    <span class="text-heading-xlarge">John Doe</span>
                </h1>
                <div>
                    <span class="text-body-medium">Senior Software Engineer at Tech Company</span>
                </div>
                <div>
                    <span class="text-body-small">San Francisco Bay Area</span>
                </div>
            </div>
        </div>
        
        <section>
            <div>
                <div>
                    <span class="t-16 t-black t-bold">Senior Software Engineer</span>
                </div>
                <div>
                    <span class="t-14 t-black--light">Tech Company</span>
                </div>
                <div>
                    <span class="t-14 t-black--light">Jan 2020 - Present</span>
                </div>
                <div>
                    <span class="t-14 t-black t-normal">Led development of microservices architecture. Implemented CI/CD pipelines. Mentored junior engineers.</span>
                </div>
            </div>
        </section>
    </div>
</body>"""
    
    print("\n" + "=" * 80)
    print("Testing HTML with Only Spans")
    print("=" * 80)
    
    processor = UnstructuredDataProcessor()
    result = processor.process_and_save(
        content=span_only_html,
        content_type="html",
        filename="test_span_only",
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
        if not result["success"]:
            print(f"Error: {result.get('error', 'Unknown')}")
        return False


def test_empty_body_with_scripts():
    """
    Test HTML that might appear to have content but is mostly scripts
    This could cause the processor to return 0 characters
    """
    
    script_heavy_html = """<body dir="ltr" class="render-mode-BIGPIPE">
    <script>
        var data = {"entityUrn":"urn:li:collectionResponse:4HlijJjSiEXmgxSNTaZbyKnZ88db1eTefgOnimBx6wM=","elements":[]};
        console.log(data);
    </script>
    <div class="application-outlet">
        <div class="pv-text-details__left-panel">
            <h1>John Doe</h1>
            <div>Senior Software Engineer</div>
        </div>
    </div>
    <script type="application/json" data-json-key="voyager-decorators">
        {"data":{"entityUrn":"urn:li:collectionResponse:4HlijJjSiEXmgxSNTaZbyKnZ88db1eTefgOnimBx6wM=","elements":[{"lixTracking":{"urn":"urn:li:member:1556551351","segmentIndex":5,"experimentId":5161311,"treatmentIndex":0,"$type":"com.linkedin.voyager.dash.segments.chameleon.ChameleonConfigLixTrackingInfo"},"chameleonConfigTrackingItem":{"configLixTrackingInfoListV2":[{"lixTracking":{"urn":"urn:li:member:1556551351","segmentIndex":5,"experimentId":5161311,"treatmentIndex":0,"$type":"com.linkedin.voyager.dash.segments.chameleon.ChameleonConfigLixTrackingInfo"},"lixTreatment":"control","lixKey":"chameleon.OJ_GLOBAL.web-copy-definition.90945.child.90952","$type":"com.linkedin.voyager.dash.segments.chameleon.ChameleonConfigLixTrackingInfoWrapper"}]}}]}
    </script>
</body>"""
    
    print("\n" + "=" * 80)
    print("Testing Script-Heavy HTML")
    print("=" * 80)
    
    processor = UnstructuredDataProcessor()
    result = processor.process_and_save(
        content=script_heavy_html,
        content_type="html",
        filename="test_script_heavy",
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
        if not result["success"]:
            print(f"Error: {result.get('error', 'Unknown')}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Real LinkedIn HTML Debug Test Suite")
    print("=" * 80)
    
    results = []
    
    results.append(("Extremely Nested HTML", test_extremely_nested_linkedin_html()))
    results.append(("HTML with Only Spans", test_html_with_only_spans()))
    results.append(("Script-Heavy HTML", test_empty_body_with_scripts()))
    
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
        print("\n⚠️ Some tests failed. This might indicate the issue.")

