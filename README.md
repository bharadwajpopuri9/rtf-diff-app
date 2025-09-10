# RTF Comparison Web Application

A Flask-based web application for comparing RTF (Rich Text Format) files with intelligent boilerplate filtering, side-by-side diff viewing, and exportable reports.

## Features

- **Drag & Drop Upload**: Intuitive file upload with drag-and-drop support
- **Multiple File Comparison**: Compare one source file against multiple comparison files
- **Intelligent Filtering**: Automatically removes SAS output headers, timestamps, and pagination
- **Flexible Options**: 
  - Word-level or line-level diffs
  - Case-insensitive comparison
  - Punctuation ignoring
  - Whitespace normalization
- **Rich Reporting**: 
  - Side-by-side HTML diff viewer
  - Consolidated HTML reports
  - CSV summary export
- **Production Ready**: Secure file handling, session management, and error handling

## Quick Start

### Local Development

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd rtf-diff-app
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   flask run
   ```
   
3. **Open your browser:**
   ```
   http://localhost:5000
   ```

### Production Deployment

#### Using Gunicorn (Recommended)

```bash
# Install gunicorn (already in requirements.txt)
pip install gunicorn

# Run with gunicorn
gunicorn "app:app" --bind 0.0.0.0:8000 --workers 4
```

#### Platform-Specific Deployment

**Heroku:**
```bash
# Create Procfile
echo "web: gunicorn app:app" > Procfile

# Deploy
git add .
git commit -m "Deploy RTF comparison app"
git push heroku main
```

**Azure App Service:**
```bash
# Set startup command in Azure Portal:
gunicorn --bind=0.0.0.0 --workers=4 app:app
```

**Render:**
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`

## Usage

### Basic Workflow

1. **Upload Files**:
   - Select one source/reference RTF file
   - Select one or more comparison RTF files (max 20, 15MB each)

2. **Configure Options**:
   - **Ignore case**: Treat "Hello" and "hello" as identical
   - **Ignore punctuation**: Remove commas, periods, etc.
   - **Ignore boilerplate**: Remove SAS headers, timestamps (recommended)
   - **Normalize whitespace**: Clean up spacing and line endings
   - **Diff granularity**: Choose word-level (precise) or line-level

3. **Review Results**:
   - Summary table showing which files have differences
   - Click "View Diff" to see side-by-side comparisons
   - Download consolidated HTML report or CSV summary

### File Format Requirements

- **Only RTF files** (.rtf extension)
- **Valid RTF signature** (starts with `{\rtf`)
- **Size limit**: 15MB per file
- **Count limit**: 20 comparison files maximum

> **Note**: If you have .docx or .pdf files, use "Save As → Rich Text Format (.rtf)" in your document editor first.

### Boilerplate Filtering

The application automatically removes common SAS output boilerplate:

- Version headers: "Version 9.4 SAS System Output"
- Confidentiality notices: "CONFIDENTIAL"
- Program references: "Program [SC]: filename.sas"
- Timestamps: "Generated on: 2024-01-01 12:00:00"
- Page numbers: "Page 1 of 5"
- Various date formats and patterns

This can be disabled by unchecking "Ignore repeated headers/footers".

## Configuration

### Environment Variables

```bash
# Production settings
export SECRET_KEY="your-secret-key-here"
export FLASK_ENV="production"

# Optional: Configure max file size (default: 15MB)
export MAX_CONTENT_LENGTH="15728640"  # 15MB in bytes
```

### Security Considerations

1. **File Validation**: 
   - Extension checking (.rtf only)
   - RTF signature verification
   - Size limits enforced

2. **Secure File Handling**:
   - Werkzeug secure filename processing
   - Session-isolated temporary directories
   - Automatic cleanup after 24 hours

3. **Input Sanitization**:
   - HTML escaping in diff output
   - XSS protection in templates
   - CSRF protection (configure SECRET_KEY)

## Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-flask

# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app --cov=utils

# Run specific test file
python -m pytest tests/test_app.py
```

### Test Coverage

- **Unit Tests**: RTF processing, diff generation
- **Integration Tests**: File upload, comparison workflow
- **Edge Cases**: Invalid files, empty content, large files

## API Reference

### Main Routes

- `GET /` - Upload form page
- `POST /upload` - Process file uploads
- `GET /results` - Comparison results page
- `GET /diff/<int:file_index>` - Individual diff viewer
- `GET /download/report` - Download HTML report
- `GET /download/csv` - Download CSV summary

### File Processing Options

```python
options = {
    'ignore_case': bool,          # Case-insensitive comparison
    'ignore_punctuation': bool,   # Remove punctuation
    'ignore_boilerplate': bool,   # Remove SAS headers/footers
    'normalize_whitespace': bool, # Clean spacing
    'diff_granularity': str      # 'word' or 'line'
}
```

## Architecture

### Components

```
app.py              # Main Flask application
utils/
├── rtf_processor.py    # RTF to text conversion
└── diff_generator.py   # Diff generation and HTML output
templates/          # Jinja2 templates
static/            # CSS, JavaScript assets
tests/             # Test suite
```

### Key Features

- **Session Management**: Isolated user sessions with automatic cleanup
- **Progress Tracking**: Visual feedback during file processing
- **Responsive Design**: Works on desktop and mobile devices
- **Accessibility**: ARIA labels, keyboard navigation, high contrast

## Troubleshooting

### Common Issues

1. **"File does not appear to be valid RTF format"**
   - Ensure file was saved as RTF, not copied/renamed
   - Re-export from original application using "Save As → RTF"

2. **"File too large" errors**
   - Reduce file size or split into smaller files
   - Check MAX_CONTENT_LENGTH setting

3. **Upload hangs or times out**
   - Check network connection
   - Verify file isn't corrupted
   - Try smaller files first

4. **No differences shown for files that should differ**
   - Check if "Ignore boilerplate" is removing actual content
   - Try disabling normalization options
   - Verify files aren't identical after processing

### Debug Mode

```bash
# Enable debug mode (development only)
export FLASK_DEBUG=1
flask run
```

### Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install black flake8 mypy

# Code formatting
black app.py utils/ tests/

# Linting
flake8 app.py utils/ tests/

# Type checking
mypy app.py utils/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review existing GitHub issues
3. Create a new issue with:
   - Python version
   - Operating system
   - Error messages
   - Steps to reproduce

---

**Note**: This application is designed for comparing structured text documents, particularly SAS output tables. For other document types, consider converting to RTF format first for best results.
