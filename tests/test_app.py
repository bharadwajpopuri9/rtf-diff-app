"""
Integration tests for the Flask RTF comparison app
"""

import pytest
import tempfile
import os
from pathlib import Path
from io import BytesIO

from app import app
from utils.rtf_processor import RTFProcessor
from utils.diff_generator import DiffGenerator

class TestRTFComparisonApp:
    
    def setup_method(self):
        """Set up test fixtures"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_rtf(self, content, filename="test.rtf"):
        """Create a test RTF file"""
        rtf_content = f"{{\\rtf1\\ansi\\deff0 {{\\fonttbl {{\\f0 Times New Roman;}}}} \\f0\\fs24 {content}}}"
        return BytesIO(rtf_content.encode('utf-8')), filename
    
    def test_index_page_loads(self):
        """Test that the index page loads correctly"""
        response = self.client.get('/')
        assert response.status_code == 200
        assert b'Upload RTF Files for Comparison' in response.data
        assert b'Source/Reference File' in response.data
        assert b'Comparison Files' in response.data
    
    def test_upload_no_files(self):
        """Test upload with no files"""
        response = self.client.post('/upload', data={})
        assert response.status_code == 302  # Redirect back to index
        
        # Follow redirect to see flash message
        response = self.client.get('/')
        assert b'Source/Reference file is required' in response.data
    
    def test_upload_invalid_file_extension(self):
        """Test upload with invalid file extension"""
        # Create a fake .txt file
        fake_file = BytesIO(b"This is not an RTF file")
        
        response = self.client.post('/upload', data={
            'source_file': (fake_file, 'test.txt'),
            'comparison_files': (fake_file, 'test2.txt')
        })
        
        assert response.status_code == 302  # Redirect back to index
    
    def test_upload_invalid_rtf_signature(self):
        """Test upload with .rtf extension but invalid RTF signature"""
        # Create a file with .rtf extension but invalid content
        fake_rtf = BytesIO(b"This is not valid RTF content")
        
        response = self.client.post('/upload', data={
            'source_file': (fake_rtf, 'test.rtf'),
            'comparison_files': (fake_rtf, 'test2.rtf')
        })
        
        assert response.status_code == 302  # Redirect back to index
    
    def test_successful_upload_and_comparison(self):
        """Test successful file upload and comparison"""
        # Create test RTF files
        source_content = "This is the source document. Line 1. Line 2."
        comparison_content = "This is the modified document. Line 1. Line 3."
        
        source_file, source_name = self.create_test_rtf(source_content, "source.rtf")
        comp_file, comp_name = self.create_test_rtf(comparison_content, "comparison.rtf")
        
        with self.client.session_transaction() as sess:
            sess['session_id'] = 'test_session'
        
        response = self.client.post('/upload', data={
            'source_file': (source_file, source_name),
            'comparison_files': [(comp_file, comp_name)],
            'ignore_boilerplate': 'on',
            'normalize_whitespace': 'on',
            'diff_granularity': 'word'
        })
        
        assert response.status_code == 302  # Redirect to results
        assert '/results' in response.location
    
    def test_results_page_without_data(self):
        """Test accessing results page without comparison data"""
        response = self.client.get('/results')
        assert response.status_code == 302  # Redirect to index
        
        # Follow redirect to see flash message
        response = self.client.get('/')
        assert b'No comparison results found' in response.data
    
    def test_diff_view_without_data(self):
        """Test accessing diff view without comparison data"""
        response = self.client.get('/diff/0')
        assert response.status_code == 302  # Redirect to index
    
    def test_download_report_without_data(self):
        """Test downloading report without comparison data"""
        response = self.client.get('/download/report')
        assert response.status_code == 302  # Redirect to index
    
    def test_download_csv_without_data(self):
        """Test downloading CSV without comparison data"""
        response = self.client.get('/download/csv')
        assert response.status_code == 302  # Redirect to index
    
    def test_file_size_limit(self):
        """Test file size limit enforcement"""
        # Create a large file (16MB, over the 15MB limit)
        large_content = "A" * (16 * 1024 * 1024)
        large_file = BytesIO(large_content.encode('utf-8'))
        
        response = self.client.post('/upload', data={
            'source_file': (large_file, 'large.rtf')
        })
        
        assert response.status_code == 413  # Request Entity Too Large
    
    def test_multiple_comparison_files(self):
        """Test upload with multiple comparison files"""
        source_content = "This is the source document."
        comp1_content = "This is the first comparison document."
        comp2_content = "This is the second comparison document."
        
        source_file, source_name = self.create_test_rtf(source_content, "source.rtf")
        comp1_file, comp1_name = self.create_test_rtf(comp1_content, "comp1.rtf")
        comp2_file, comp2_name = self.create_test_rtf(comp2_content, "comp2.rtf")
        
        with self.client.session_transaction() as sess:
            sess['session_id'] = 'test_session'
        
        response = self.client.post('/upload', data={
            'source_file': (source_file, source_name),
            'comparison_files': [
                (comp1_file, comp1_name),
                (comp2_file, comp2_name)
            ],
            'ignore_boilerplate': 'on',
            'normalize_whitespace': 'on',
            'diff_granularity': 'word'
        })
        
        assert response.status_code == 302  # Redirect to results
    
    def test_comparison_options(self):
        """Test different comparison options"""
        source_content = "Hello, World! This is a TEST."
        comp_content = "hello world this is a test"
        
        source_file, source_name = self.create_test_rtf(source_content, "source.rtf")
        comp_file, comp_name = self.create_test_rtf(comp_content, "comp.rtf")
        
        with self.client.session_transaction() as sess:
            sess['session_id'] = 'test_session'
        
        # Test with ignore case and punctuation
        response = self.client.post('/upload', data={
            'source_file': (source_file, source_name),
            'comparison_files': [(comp_file, comp_name)],
            'ignore_case': 'on',
            'ignore_punctuation': 'on',
            'normalize_whitespace': 'on',
            'diff_granularity': 'word'
        })
        
        assert response.status_code == 302
    
    def test_identical_files(self):
        """Test comparison of identical files"""
        content = "This is identical content in both files."
        
        source_file, source_name = self.create_test_rtf(content, "source.rtf")
        comp_file, comp_name = self.create_test_rtf(content, "comp.rtf")
        
        with self.client.session_transaction() as sess:
            sess['session_id'] = 'test_session'
        
        response = self.client.post('/upload', data={
            'source_file': (source_file, source_name),
            'comparison_files': [(comp_file, comp_name)],
            'normalize_whitespace': 'on',
            'diff_granularity': 'word'
        })
        
        assert response.status_code == 302
    
    def test_empty_files(self):
        """Test comparison of empty files"""
        source_file, source_name = self.create_test_rtf("", "source.rtf")
        comp_file, comp_name = self.create_test_rtf("", "comp.rtf")
        
        with self.client.session_transaction() as sess:
            sess['session_id'] = 'test_session'
        
        response = self.client.post('/upload', data={
            'source_file': (source_file, source_name),
            'comparison_files': [(comp_file, comp_name)],
            'normalize_whitespace': 'on',
            'diff_granularity': 'word'
        })
        
        assert response.status_code == 302
    
    def test_line_vs_word_diff(self):
        """Test line-level vs word-level diff granularity"""
        source_content = "Line 1\\nLine 2\\nLine 3"
        comp_content = "Line 1\\nModified Line 2\\nLine 3"
        
        source_file, source_name = self.create_test_rtf(source_content, "source.rtf")
        comp_file, comp_name = self.create_test_rtf(comp_content, "comp.rtf")
        
        with self.client.session_transaction() as sess:
            sess['session_id'] = 'test_session'
        
        # Test word-level diff
        response = self.client.post('/upload', data={
            'source_file': (source_file, source_name),
            'comparison_files': [(comp_file, comp_name)],
            'diff_granularity': 'word'
        })
        assert response.status_code == 302
        
        # Test line-level diff
        source_file, _ = self.create_test_rtf(source_content, "source.rtf")
        comp_file, _ = self.create_test_rtf(comp_content, "comp.rtf")
        
        response = self.client.post('/upload', data={
            'source_file': (source_file, source_name),
            'comparison_files': [(comp_file, comp_name)],
            'diff_granularity': 'line'
        })
        assert response.status_code == 302

class TestDiffGenerator:
    
    def setup_method(self):
        """Set up test fixtures"""
        self.generator = DiffGenerator()
    
    def test_word_level_diff(self):
        """Test word-level diff generation"""
        source_text = "Hello world this is a test"
        comp_text = "Hello beautiful world this is a test"
        
        options = {'diff_granularity': 'word'}
        result = self.generator.compare_texts(
            source_text, comp_text, 
            "source.rtf", "comp.rtf", 
            options
        )
        
        assert result['has_differences'] == True
        assert result['change_count'] > 0
        assert 'html' in result
        assert 'stats' in result
    
    def test_line_level_diff(self):
        """Test line-level diff generation"""
        source_text = "Line 1\nLine 2\nLine 3"
        comp_text = "Line 1\nModified Line 2\nLine 3"
        
        options = {'diff_granularity': 'line'}
        result = self.generator.compare_texts(
            source_text, comp_text,
            "source.rtf", "comp.rtf",
            options
        )
        
        assert result['has_differences'] == True
        assert result['change_count'] > 0
        assert 'html' in result
        assert 'stats' in result
    
    def test_identical_texts(self):
        """Test diff of identical texts"""
        text = "This is identical text"
        
        options = {'diff_granularity': 'word'}
        result = self.generator.compare_texts(
            text, text,
            "source.rtf", "comp.rtf",
            options
        )
        
        assert result['has_differences'] == False
        assert result['change_count'] == 0
    
    def test_consolidated_report_generation(self):
        """Test consolidated HTML report generation"""
        results = [
            {
                'filename': 'test1.rtf',
                'has_differences': True,
                'change_count': 5,
                'diff_html': '<div>Test diff 1</div>',
                'stats': {'insertions': 2, 'deletions': 3, 'replacements': 0}
            },
            {
                'filename': 'test2.rtf',
                'has_differences': False,
                'change_count': 0,
                'diff_html': '',
                'stats': {'insertions': 0, 'deletions': 0, 'replacements': 0}
            }
        ]
        
        options = {'diff_granularity': 'word'}
        report = self.generator.generate_consolidated_report(
            'source.rtf', results, options
        )
        
        assert isinstance(report, str)
        assert 'RTF Comparison Report' in report
        assert 'test1.rtf' in report
        assert 'test2.rtf' in report
        assert 'DOCTYPE html' in report
