#!/usr/bin/env python3
"""
Simple test script to verify PDF generation works
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_pdf_imports():
    """Test that we can import the PDF modules"""
    try:
        import weasyprint
        print("✅ WeasyPrint imported successfully")
    except ImportError as e:
        print(f"❌ WeasyPrint import failed: {e}")
        return False
    
    try:
        from natural_shift_planner.templates.pdf_renderer import generate_schedule_pdf
        print("✅ PDF renderer imported successfully")
    except ImportError as e:
        print(f"❌ PDF renderer import failed: {e}")
        return False
    
    return True

def test_basic_pdf_generation():
    """Test basic PDF generation"""
    try:
        from natural_shift_planner.utils.demo_data import create_demo_schedule
        from natural_shift_planner.api.converters import convert_domain_to_response
        from natural_shift_planner.templates.pdf_renderer import generate_schedule_pdf
        
        print("📊 Creating demo schedule...")
        schedule = create_demo_schedule()
        schedule_data = convert_domain_to_response(schedule)
        
        print("📄 Generating PDF...")
        pdf_content = generate_schedule_pdf(schedule_data)
        
        if isinstance(pdf_content, bytes) and len(pdf_content) > 0:
            print(f"✅ PDF generated successfully ({len(pdf_content)} bytes)")
            if pdf_content.startswith(b'%PDF'):
                print("✅ PDF format validated (starts with %PDF)")
                return True
            else:
                print("❌ PDF format invalid (doesn't start with %PDF)")
                return False
        else:
            print("❌ PDF generation failed - no content")
            return False
            
    except Exception as e:
        print(f"❌ PDF generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 Testing PDF report generation...")
    print("=" * 50)
    
    success = True
    
    print("\n1. Testing imports...")
    success &= test_pdf_imports()
    
    print("\n2. Testing PDF generation...")
    success &= test_basic_pdf_generation()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! PDF generation is working.")
        return 0
    else:
        print("❌ Some tests failed.")
        return 1

if __name__ == "__main__":
    exit(main())