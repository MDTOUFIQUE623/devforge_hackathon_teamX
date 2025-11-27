"""
Test LinkedIn HTML extraction - specifically for the user's reported issue
where pasting LinkedIn profile HTML returns "0 characters, 0 paragraphs"
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.data_processor.unstructured_processor import UnstructuredDataProcessor
from src.utils.config import DATA_DIR

def test_linkedin_html_extraction():
    """Test extraction from a realistic LinkedIn profile HTML snippet"""
    
    # This is a simplified but representative LinkedIn profile HTML structure
    # that mimics what the user would paste from LinkedIn
    linkedin_html = """<body dir="ltr" class="render-mode-BIGPIPE nav-v2 ember-application payment-failure-global-alert-lix-enabled-class icons-loaded boot-complete" data-t-link-to-event-attached="true">
    <div class="application-outlet">
        <div class="profile-section">
            <div class="pv-text-details__left-panel">
                <h1 class="text-heading-xlarge inline t-24 v-align-middle break-words">John Doe</h1>
                <div class="text-body-medium break-words">Senior Software Engineer at Tech Company</div>
                <div class="text-body-small inline t-black--light break-words">
                    <span class="text-body-small inline t-black--light break-words">San Francisco Bay Area</span>
                </div>
            </div>
        </div>
        
        <section class="pv-profile-section experience-section">
            <h2 class="text-heading-large">Experience</h2>
            <div class="pvs-list__outer-container">
                <div class="pvs-list__paged-list-item">
                    <div class="pvs-entity">
                        <div class="pvs-entity__summary-info">
                            <h3 class="t-16 t-black t-bold">Senior Software Engineer</h3>
                            <div class="t-14 t-black--light t-normal">Tech Company</div>
                            <div class="t-14 t-black--light t-normal">Jan 2020 - Present · 4 yrs</div>
                            <div class="t-14 t-black--light t-normal">San Francisco Bay Area</div>
                        </div>
                        <div class="pvs-entity__summary-info-content">
                            <div class="t-14 t-black t-normal">
                                <span>Led development of microservices architecture serving 10M+ users. 
                                Implemented CI/CD pipelines reducing deployment time by 60%. 
                                Mentored junior engineers and contributed to open-source projects.</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        
        <section class="pv-profile-section education-section">
            <h2 class="text-heading-large">Education</h2>
            <div class="pvs-list__outer-container">
                <div class="pvs-entity">
                    <div class="pvs-entity__summary-info">
                        <h3 class="t-16 t-black t-bold">Master of Science in Computer Science</h3>
                        <div class="t-14 t-black--light t-normal">Stanford University</div>
                        <div class="t-14 t-black--light t-normal">2016 - 2018</div>
                    </div>
                </div>
            </div>
        </section>
        
        <section class="pv-profile-section skills-section">
            <h2 class="text-heading-large">Skills</h2>
            <div class="pvs-list__outer-container">
                <div class="pvs-list__paged-list-item">
                    <span class="t-14 t-black t-normal">Python</span>
                    <span class="t-14 t-black t-normal">JavaScript</span>
                    <span class="t-14 t-black t-normal">React</span>
                    <span class="t-14 t-black t-normal">Docker</span>
                    <span class="t-14 t-black t-normal">Kubernetes</span>
                </div>
            </div>
        </section>
        
        <div class="pv-about-section">
            <h2 class="text-heading-large">About</h2>
            <div class="inline-show-more-text">
                <span>Passionate software engineer with 8+ years of experience building scalable web applications. 
                Specialized in full-stack development, cloud infrastructure, and system design. 
                Always eager to learn new technologies and contribute to meaningful projects.</span>
            </div>
        </div>
    </div>
    
    <script type="application/json" data-json-key="voyager-decorators">
        {"data":{"entityUrn":"urn:li:collectionResponse:4HlijJjSiEXmgxSNTaZbyKnZ88db1eTefgOnimBx6wM=","elements":[]}}
    </script>
    
    <nav class="global-nav">
        <div class="nav-item">Home</div>
        <div class="nav-item">My Network</div>
        <div class="nav-item">Jobs</div>
    </nav>
</body>"""

    print("=" * 80)
    print("Testing LinkedIn HTML Extraction")
    print("=" * 80)
    
    processor = UnstructuredDataProcessor()
    
    # Test direct HTML processing
    print("\n1. Testing direct HTML processing...")
    processed_text = processor.process_html(linkedin_html, source_name="linkedin_profile")
    
    print(f"\nExtracted text length: {len(processed_text)} characters")
    print(f"Extracted text preview (first 500 chars):\n{processed_text[:500]}")
    
    # Count paragraphs
    paragraphs = [p.strip() for p in processed_text.split('\n\n') if p.strip()]
    if not paragraphs:
        paragraphs = [p.strip() for p in processed_text.split('\n') if p.strip() and len(p.strip()) > 10]
    
    print(f"\nParagraphs found: {len(paragraphs)}")
    
    if len(processed_text) == 0 or len(paragraphs) == 0:
        print("\n❌ FAILED: No content extracted!")
        return False
    else:
        print(f"\n✅ SUCCESS: Extracted {len(processed_text)} characters, {len(paragraphs)} paragraphs")
    
    # Test via process_and_save (simulating frontend behavior)
    print("\n2. Testing via process_and_save (simulating frontend)...")
    result = processor.process_and_save(
        content=linkedin_html,
        content_type="html",
        filename="test_linkedin_profile",
        output_dir=DATA_DIR
    )
    
    print(f"\nResult: {result}")
    
    if result["success"]:
        content_length = result.get('content_length', 0)
        paragraphs = result.get('paragraphs', 0)
        print(f"\n✅ SUCCESS: {content_length} characters, {paragraphs} paragraphs")
        
        if content_length == 0 or paragraphs == 0:
            print("\n❌ FAILED: process_and_save returned 0 characters/paragraphs!")
            return False
        
        # Read and show the saved file
        if result.get('file_path'):
            saved_file = Path(result['file_path'])
            if saved_file.exists():
                saved_content = saved_file.read_text(encoding='utf-8')
                print(f"\nSaved file content preview (first 500 chars):\n{saved_content[:500]}")
        
        return True
    else:
        print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
        return False


def test_minimal_linkedin_html():
    """Test with a minimal LinkedIn HTML that might cause issues"""
    
    minimal_html = """<body dir="ltr" class="render-mode-BIGPIPE">
    <div class="application-outlet">
        <div class="pv-text-details__left-panel">
            <h1>Jane Smith</h1>
            <div>Software Developer</div>
        </div>
    </div>
    <script>var data = {"test": "value"};</script>
</body>"""
    
    print("\n" + "=" * 80)
    print("Testing Minimal LinkedIn HTML")
    print("=" * 80)
    
    processor = UnstructuredDataProcessor()
    result = processor.process_and_save(
        content=minimal_html,
        content_type="html",
        filename="test_minimal_linkedin",
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


def test_complex_linkedin_with_json():
    """Test with complex LinkedIn HTML that includes JSON data (like the user's error message)"""
    
    complex_html = """<body dir="ltr" class="render-mode-BIGPIPE nav-v2 ember-application">
    <div class="application-outlet">
        <div class="profile-section">
            <h1 class="text-heading-xlarge">John Doe</h1>
            <div class="text-body-medium">Senior Software Engineer</div>
        </div>
    </div>
    
    <script type="application/json" data-json-key="voyager-decorators">
        {"data":{"entityUrn":"urn:li:collectionResponse:4HlijJjSiEXmgxSNTaZbyKnZ88db1eTefgOnimBx6wM=","elements":[{"lixTracking":{"urn":"urn:li:member:1556551351","segmentIndex":5,"experimentId":5161311,"treatmentIndex":0,"$type":"com.linkedin.voyager.dash.segments.chameleon.ChameleonConfigLixTrackingInfo"},"chameleonConfigTrackingItem":{"configLixTrackingInfoListV2":[{"lixTracking":{"urn":"urn:li:member:1556551351","segmentIndex":5,"experimentId":5161311,"treatmentIndex":0,"$type":"com.linkedin.voyager.dash.segments.chameleon.ChameleonConfigLixTrackingInfo"},"lixTreatment":"control","lixKey":"chameleon.OJ_GLOBAL.web-copy-definition.90945.child.90952","$type":"com.linkedin.voyager.dash.segments.chameleon.ChameleonConfigLixTrackingInfoWrapper"}]}}]}
    </script>
    
    <nav class="global-nav">
        <div>Home</div>
        <div>My Network</div>
    </nav>
</body>"""
    
    print("\n" + "=" * 80)
    print("Testing Complex LinkedIn HTML with JSON")
    print("=" * 80)
    
    processor = UnstructuredDataProcessor()
    result = processor.process_and_save(
        content=complex_html,
        content_type="html",
        filename="test_complex_linkedin",
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
    print("LinkedIn HTML Extraction Test Suite")
    print("=" * 80)
    
    results = []
    
    # Run all tests
    results.append(("LinkedIn HTML Extraction", test_linkedin_html_extraction()))
    results.append(("Minimal LinkedIn HTML", test_minimal_linkedin_html()))
    results.append(("Complex LinkedIn with JSON", test_complex_linkedin_with_json()))
    
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
        print("\n⚠️ Some tests failed. Review the output above.")

