"""
RTF Processing utilities for text extraction and cleaning
"""

import re
import yaml
from pathlib import Path
from striprtf.striprtf import rtf_to_text

class RTFProcessor:
    def __init__(self):
        """Initialize with default boilerplate patterns"""
        self.boilerplate_patterns = [
            # SAS system output headers/footers
            r'Version \d+\.\d+ SAS System Output',
            r'CONFIDENTIAL',
            r'Program \[SC\]:.*',
            r'Page \d+ of \d+',
            r'Generated on:?\s*\d{4}-\d{2}-\d{2}(\s+\d{2}:\d{2}:\d{2})?',
            r'Created on:?\s*\d{4}-\d{2}-\d{2}(\s+\d{2}:\d{2}:\d{2})?',
            r'Updated on:?\s*\d{4}-\d{2}-\d{2}(\s+\d{2}:\d{2}:\d{2})?',
            r'Printed on:?\s*\d{4}-\d{2}-\d{2}(\s+\d{2}:\d{2}:\d{2})?',
            r'Generated at:?\s*\d{2}/\d{2}/\d{4}(\s+\d{1,2}:\d{2}(\s*[APap][Mm])?)?',
            r'Created at:?\s*\d{2}/\d{2}/\d{4}(\s+\d{1,2}:\d{2}(\s*[APap][Mm])?)?',
            r'Updated at:?\s*\d{2}/\d{2}/\d{4}(\s+\d{1,2}:\d{2}(\s*[APap][Mm])?)?',
            r'Printed at:?\s*\d{2}/\d{2}/\d{4}(\s+\d{1,2}:\d{2}(\s*[APap][Mm])?)?',
            r'\d{1,2}-[A-Za-z]{3}-\d{4}(\s+\d{2}:\d{2}:\d{2})?',
            r'\d{1,2}/\d{1,2}/\d{4}(\s+\d{1,2}:\d{2}(\s*[APap][Mm])?)?',
            r'\d{4}-\d{2}-\d{2}(\s+\d{2}:\d{2}:\d{2})?',
            # Table pagination and metadata
            r'Table \d+\.\d+(\.\d+)?',
            r'Listing \d+\.\d+(\.\d+)?',
            r'Figure \d+\.\d+(\.\d+)?',
            r'^\s*-+\s*$',  # Separator lines
            r'^\s*=+\s*$',  # Separator lines
            r'Study:\s*\w+',
            r'Protocol:\s*\w+',
            r'Output Date:.*',
            r'Run Date:.*',
            r'File Path:.*',
            r'Program Name:.*',
        ]
    
    def process_file(self, file_path, options):
        """
        Convert RTF file to processed text based on options
        
        Args:
            file_path: Path to RTF file
            options: Dict of processing options
            
        Returns:
            Processed text string
        """
        try:
            # Read RTF file with encoding handling
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                rtf_content = f.read()
        except UnicodeDecodeError:
            # Try with Windows-1252 encoding
            with open(file_path, 'r', encoding='windows-1252', errors='ignore') as f:
                rtf_content = f.read()
        
        # Convert RTF to plain text
        try:
            text = rtf_to_text(rtf_content)
        except Exception as e:
            # Fallback: try to extract text manually if striprtf fails
            text = self._manual_rtf_extract(rtf_content)
        
        # Apply processing options
        if options.get('ignore_boilerplate', True):
            text = self._remove_boilerplate(text)
        
        if options.get('normalize_whitespace', True):
            text = self._normalize_whitespace(text)
        
        if options.get('ignore_case', False):
            text = text.lower()
        
        if options.get('ignore_punctuation', False):
            text = self._remove_punctuation(text)
        
        return text
    
    def _manual_rtf_extract(self, rtf_content):
        """
        Manual RTF text extraction as fallback
        """
        # Remove RTF control words and groups
        text = re.sub(r'\\[a-z]+\d*\s?', '', rtf_content)
        text = re.sub(r'[{}]', '', text)
        text = re.sub(r'\\[\'"]([0-9a-f]{2})', lambda m: chr(int(m.group(1), 16)), text)
        return text
    
    def _remove_boilerplate(self, text):
        """
        Remove boilerplate patterns from text
        """
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                cleaned_lines.append(line)
                continue
            
            # Check if line matches any boilerplate pattern
            is_boilerplate = False
            for pattern in self.boilerplate_patterns:
                if re.search(pattern, line_stripped, re.IGNORECASE):
                    is_boilerplate = True
                    break
            
            if not is_boilerplate:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _normalize_whitespace(self, text):
        """
        Normalize whitespace and line endings
        """
        # Convert Windows line endings to Unix
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive whitespace but preserve structure
        lines = text.split('\n')
        normalized_lines = []
        
        for line in lines:
            # Normalize internal whitespace
            normalized_line = ' '.join(line.split())
            normalized_lines.append(normalized_line)
        
        return '\n'.join(normalized_lines)
    
    def _remove_punctuation(self, text):
        """
        Remove punctuation for comparison
        """
        # Keep alphanumeric and essential whitespace
        return re.sub(r'[^\w\s]', '', text)
    
    def add_boilerplate_pattern(self, pattern):
        """
        Add custom boilerplate pattern
        """
        self.boilerplate_patterns.append(pattern)
    
    def load_boilerplate_config(self, config_path):
        """
        Load boilerplate patterns from YAML config
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                if 'boilerplate_patterns' in config:
                    self.boilerplate_patterns.extend(config['boilerplate_patterns'])
        except Exception as e:
            print(f"Warning: Could not load boilerplate config: {e}")
