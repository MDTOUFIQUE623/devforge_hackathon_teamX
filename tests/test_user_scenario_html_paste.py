"""
Test the exact user scenario: pasting LinkedIn HTML into text area and processing it.
This simulates what happens in the frontend when a user pastes HTML content.
"""

import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.data_processor.unstructured_processor import UnstructuredDataProcessor
from src.utils.config import DATA_DIR

def test_user_paste_scenario():
    """
    Simulates the exact scenario where a user pastes LinkedIn HTML into the text area.
    This is a realistic LinkedIn profile HTML that might cause issues.
    """
    
    # This simulates what a user might paste from LinkedIn's outer HTML
    user_pasted_html = """<body dir="ltr" class="render-mode-BIGPIPE nav-v2 ember-application payment-failure-global-alert-lix-enabled-class icons-loaded boot-complete" data-t-link-to-event-attached="true">
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
                    <h2 class="text-heading-large">Experience</h2>
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
                
                <section class="pv-profile-section education-section">
                    <h2 class="text-heading-large">Education</h2>
                    <div class="pvs-list__outer-container">
                        <div class="pvs-entity">
                            <div class="pvs-entity__summary-info">
                                <div class="t-16 t-black t-bold">
                                    <span class="t-16 t-black t-bold">Master of Science in Computer Science</span>
                                </div>
                                <div class="t-14 t-black--light t-normal">
                                    <span class="t-14 t-black--light t-normal">Stanford University</span>
                                </div>
                                <div class="t-14 t-black--light t-normal">
                                    <span class="t-14 t-black--light t-normal">2016 - 2018</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
                
                <div class="pv-about-section">
                    <h2 class="text-heading-large">About</h2>
                    <div class="inline-show-more-text">
                        <span class="t-14 t-black t-normal">Passionate software engineer with 8+ years of experience building scalable web applications. Specialized in full-stack development, cloud infrastructure, and system design. Always eager to learn new technologies and contribute to meaningful projects.</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script type="application/json" data-json-key="voyager-decorators">
        {"data":{"entityUrn":"urn:li:collectionResponse:4HlijJjSiEXmgxSNTaZbyKnZ88db1eTefgOnimBx6wM=","elements":[{"lixTracking":{"urn":"urn:li:member:1556551351","segmentIndex":5,"experimentId":5161311,"treatmentIndex":0,"$type":"com.linkedin.voyager.dash.segments.chameleon.ChameleonConfigLixTrackingInfo"},"chameleonConfigTrackingItem":{"configLixTrackingInfoListV2":[{"lixTracking":{"urn":"urn:li:member:1556551351","segmentIndex":5,"experimentId":5161311,"treatmentIndex":0,"$type":"com.linkedin.voyager.dash.segments.chameleon.ChameleonConfigLixTrackingInfo"},"lixTreatment":"control","lixKey":"chameleon.OJ_GLOBAL.web-copy-definition.90945.child.90952","$type":"com.linkedin.voyager.dash.segments.chameleon.ChameleonConfigLixTrackingInfoWrapper"}]}}]}
    </script>
    
    <nav class="global-nav">
        <div class="nav-item">Home</div>
        <div class="nav-item">My Network</div>
        <div class="nav-item">Jobs</div>
    </nav>
</body>"""

    print("=" * 80)
    print("Testing User Paste Scenario (Simulating Frontend Behavior)")
    print("=" * 80)
    
    processor = UnstructuredDataProcessor()
    
    # Simulate exactly what happens in the frontend:
    # 1. User pastes HTML into text area
    # 2. User selects content_type="html"
    # 3. User clicks "Convert & Process"
    # 4. Frontend calls process_and_save with content, content_type="html", filename, output_dir
    
    print("\nSimulating frontend call: process_and_save(content=html, content_type='html', ...)")
    
    result = processor.process_and_save(
        content=user_pasted_html,
        content_type="html",
        filename="user_linkedin_profile",
        output_dir=DATA_DIR
    )
    
    print(f"\nResult: {result}")
    
    # Check the result
    success = result.get("success", False)
    content_length = result.get('content_length', 0)
    paragraphs = result.get('paragraphs', 0)
    error = result.get('error', None)
    
    print(f"\nSuccess: {success}")
    print(f"Content Length: {content_length} characters")
    print(f"Paragraphs: {paragraphs}")
    if error:
        print(f"Error: {error}")
    
    # This should NOT return 0 characters and 0 paragraphs
    if success and content_length > 0 and paragraphs > 0:
        print(f"\n✅ SUCCESS: Successfully extracted {content_length} characters, {paragraphs} paragraphs")
        
        # Show the saved content
        if result.get('file_path'):
            saved_file = Path(result['file_path'])
            if saved_file.exists():
                saved_content = saved_file.read_text(encoding='utf-8')
                print(f"\n📄 Saved file: {saved_file}")
                print(f"\n📝 Content preview (first 500 chars):\n{saved_content[:500]}")
                if len(saved_content) > 500:
                    print("...")
        
        return True
    else:
        print(f"\n❌ FAILED: Got {content_length} characters, {paragraphs} paragraphs")
        if not success:
            print(f"Error message: {error}")
        return False


def test_empty_html_input():
    """Test what happens with empty or minimal HTML input"""
    
    print("\n" + "=" * 80)
    print("Testing Empty/Minimal HTML Input")
    print("=" * 80)
    
    processor = UnstructuredDataProcessor()
    
    # Test with very minimal HTML
    minimal_html = "<body></body>"
    
    result = processor.process_and_save(
        content=minimal_html,
        content_type="html",
        filename="test_minimal",
        output_dir=DATA_DIR
    )
    
    print(f"\nResult: {result}")
    
    # This should fail gracefully with a proper error message
    if not result["success"]:
        print(f"\n✅ EXPECTED: Processing failed (empty HTML): {result.get('error', 'Unknown')}")
        return True
    else:
        content_length = result.get('content_length', 0)
        paragraphs = result.get('paragraphs', 0)
        if content_length == 0 and paragraphs == 0:
            print(f"\n✅ EXPECTED: 0 characters, 0 paragraphs (empty HTML)")
            return True
        else:
            print(f"\n⚠️ UNEXPECTED: Got {content_length} characters, {paragraphs} paragraphs")
            return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("User Scenario Test Suite")
    print("=" * 80)
    
    results = []
    
    results.append(("User Paste Scenario", test_user_paste_scenario()))
    results.append(("Empty HTML Input", test_empty_html_input()))
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n🎉 All tests passed! The HTML processor should now work correctly for user scenarios.")
    else:
        print("\n⚠️ Some tests failed. Review the output above.")

