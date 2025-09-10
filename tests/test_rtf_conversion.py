"""
Tests for RTF processing utilities
"""

import pytest
import tempfile
import os
from pathlib import Path

from utils.rtf_processor import RTFProcessor

class TestRTFProcessor:
    
    def setup_method(self):
        """Set up test fixtures"""
        self.processor = RTFProcessor()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_rtf(self, content, filename="test.rtf"):
        """Create a test RTF file"""
        rtf_content = f"{{\\rtf1\\ansi\\deff0 {{\\fonttbl {{\\f0 Times New Roman;}}}} \\f0\\fs24 {content}}}"
        file_path = Path(self.temp_dir) / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(rtf_content)
        return file_path
    
    def test_basic_rtf_processing(self):
        """Test basic RTF to text conversion"""
        test_content = "Hello, this is a test document."
        file_path = self.create_test_rtf(test_content)
        
        options = {
            'ignore_boilerplate': False,
            'normalize_whitespace': True,
            'ignore_case': False,
            'ignore_punctuation': False
        }
        
        result = self.processor.process_file(file_path, options)
        assert "Hello, this is a test document." in result
    
    def test_boilerplate_removal(self):
        """Test boilerplate pattern removal"""
        test_content = """
        Generated on: 2024-01-01 12:00:00
        Version 9.4 SAS System Output
        CONFIDENTIAL
        This is the actual content.
        Program [SC]: test_program.sas
        Page 1 of 5
        """
        
        file_path = self.create_test_rtf(test_content)
        
        options = {
            'ignore_boilerplate': True,
            'normalize_whitespace': True,
            'ignore_case': False,
            'ignore_punctuation': False
        }
        
        result = self.processor.process_file(file_path, options)
        
        # Should contain actual content
        assert "This is the actual content." in result
        
        # Should not contain boilerplate
        assert "Generated on:" not in result
        assert "Version 9.4 SAS System Output" not in result
        assert "CONFIDENTIAL" not in result
        assert "Program [SC]:" not in result
        assert "Page 1 of 5" not in result
    
    def test_whitespace_normalization(self):
        """Test whitespace normalization"""
        test_content = "This   has    multiple\\n\\nspaces    and\\r\\nlines."
        file_path = self.create_test_rtf(test_content)
        
        options = {
            'ignore_boilerplate': False,
            'normalize_whitespace': True,
            'ignore_case': False,
            'ignore_punctuation': False
        }
        
        result = self.processor.process_file(file_path, options)
        
        # Whitespace should be normalized
        assert "multiple  spaces" not in result
        assert "This has multiple" in result
    
    def test_case_ignore(self):
        """Test case ignoring"""
        test_content = "HELLO World Test"
        file_path = self.create_test_rtf(test_content)
        
        options = {
            'ignore_boilerplate': False,
            'normalize_whitespace': True,
            'ignore_case': True,
            'ignore_punctuation': False
        }
        
        result = self.processor.process_file(file_path, options)
        assert result.lower() == result  # Should be all lowercase
    
    def test_punctuation_removal(self):
        """Test punctuation removal"""
        test_content = "Hello, world! How are you?"
        file_path = self.create_test_rtf(test_content)
        
        options = {
            'ignore_boilerplate': False,
            'normalize_whitespace': True,
            'ignore_case': False,
            'ignore_punctuation': True
        }
        
        result = self.processor.process_file(file_path, options)
        
        # Punctuation should be removed
        assert "," not in result
        assert "!" not in result
        assert "?" not in result
        assert "Hello world How are you" in result
    
    def test_custom_boilerplate_patterns(self):
        """Test adding custom boilerplate patterns"""
        test_content = """
        CUSTOM_HEADER: Test Header
        This is the actual content.
        CUSTOM_FOOTER: End of document
        """
        
        file_path = self.create_test_rtf(test_content)
        
        # Add custom pattern
        self.processor.add_boilerplate_pattern(r'CUSTOM_\w+:.*')
        
        options = {
            'ignore_boilerplate': True,
            'normalize_whitespace': True,
            'ignore_case': False,
            'ignore_punctuation': False
        }
        
        result = self.processor.process_file(file_path, options)
        
        # Should contain actual content
        assert "This is the actual content." in result
        
        # Should not contain custom boilerplate
        assert "CUSTOM_HEADER:" not in result
        assert "CUSTOM_FOOTER:" not in result
    
    def test_invalid_rtf_fallback(self):
        """Test fallback for invalid RTF content"""
        # Create a file with invalid RTF content
        file_path = Path(self.temp_dir) / "invalid.rtf"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("{\\rtf1 Invalid RTF content with \\unknown commands}")
        
        options = {
            'ignore_boilerplate': False,
            'normalize_whitespace': True,
            'ignore_case': False,
            'ignore_punctuation': False
        }
        
        # Should not raise an exception
        result = self.processor.process_file(file_path, options)
        assert isinstance(result, str)
    
    def test_encoding_handling(self):
        """Test handling of different encodings"""
        test_content = "Test with special characters: áéíóú"
        file_path = self.create_test_rtf(test_content)
        
        options = {
            'ignore_boilerplate': False,
            'normalize_whitespace': True,
            'ignore_case': False,
            'ignore_punctuation': False
        }
        
        result = self.processor.process_file(file_path, options)
        # Should handle special characters gracefully
        assert isinstance(result, str)
    
    def test_empty_file(self):
        """Test processing empty RTF file"""
        file_path = self.create_test_rtf("")
        
        options = {
            'ignore_boilerplate': False,
            'normalize_whitespace': True,
            'ignore_case': False,
            'ignore_punctuation': False
        }
        
        result = self.processor.process_file(file_path, options)
        assert isinstance(result, str)
    
    def test_table_content_processing(self):
        """Test processing table-like content similar to t_dv.rtf"""
        test_content = """
        Generated on: 2024-01-01
        +---------------------------------------------------------+--------------+
        |                                                         | `  -21`\\     |
        |                                                         | ` (N = 46)`  |
        +---------------------------------------------------------+--------------+
        | `Any protocol deviation`                                | ` 35 (76.1)` |
        +---------------------------------------------------------+--------------+
        | `Any major protocol deviation`                          | `  2 ( 4.3)` |
        +---------------------------------------------------------+--------------+
        Program [SC]: test_table.sas
        """
        
        file_path = self.create_test_rtf(test_content)
        
        options = {
            'ignore_boilerplate': True,
            'normalize_whitespace': True,
            'ignore_case': False,
            'ignore_punctuation': False
        }
        
        result = self.processor.process_file(file_path, options)
        
        # Should contain table content
        assert "Any protocol deviation" in result
        assert "35 (76.1)" in result
        
        # Should not contain boilerplate
        assert "Generated on:" not in result
        assert "Program [SC]:" not in result
