import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.features.matrix.service.document_parsers.excel_parser import ExcelParser

def test_excel_parser():
    """Test the Excel parser with a simple example"""
    parser = ExcelParser()
    
    # Test with a non-existent file
    result = parser.parse("non_existent_file.xlsx")
    print("Test with non-existent file:", result)
    
    print("Excel parser tests completed")

if __name__ == "__main__":
    test_excel_parser()