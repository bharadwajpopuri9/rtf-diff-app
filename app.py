"""
RTF Comparison Web Application
Author: Converted from rtf_folder_comparer.py
Date: 2025-09-10
Description:
    Flask web app for comparing RTF files with configurable options and HTML reports.
"""

import os
import tempfile
import uuid
import shutil
import csv
import io
from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, request, render_template, jsonify, send_file, flash, redirect, url_for, session
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from utils.rtf_processor import RTFProcessor
from utils.diff_generator import DiffGenerator

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 15 * 1024 * 1024  # 15MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Initialize processors
rtf_processor = RTFProcessor()
diff_generator = DiffGenerator()

def cleanup_old_sessions():
    """Clean up session directories older than 24 hours"""
    upload_base = Path(app.config['UPLOAD_FOLDER'])
    cutoff = datetime.now() - timedelta(hours=24)
    
    for session_dir in upload_base.glob('rtf_session_*'):
        if session_dir.is_dir() and datetime.fromtimestamp(session_dir.stat().st_mtime) < cutoff:
            shutil.rmtree(session_dir, ignore_errors=True)

def get_session_dir():
    """Get or create session-specific upload directory"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    session_dir = Path(app.config['UPLOAD_FOLDER']) / f"rtf_session_{session['session_id']}"
    session_dir.mkdir(exist_ok=True)
    return session_dir

def validate_rtf_file(file_path):
    """Validate that uploaded file is RTF format"""
    try:
        # Check file extension
        if not file_path.suffix.lower() == '.rtf':
            return False, "File must have .rtf extension"
        
        # Check file is not empty and is readable
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(50)  # Read first 50 chars
                if not content.strip():
                    return False, "File appears to be empty"
                # Basic RTF format check - look for RTF signature
                content_lower = content.lower()
                if 'rtf' not in content_lower or '{' not in content:
                    return False, "File does not appear to be valid RTF format"
        except Exception:
            return False, "File encoding is not supported"
        
        return True, None
    except Exception as e:
        return False, f"Error validating file: {str(e)}"

@app.before_request
def before_request():
    """Run cleanup before each request"""
    cleanup_old_sessions()

@app.route('/')
def index():
    """Main upload page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads and process comparisons"""
    try:
        # Get upload options
        options = {
            'ignore_case': request.form.get('ignore_case') == 'on',
            'ignore_punctuation': request.form.get('ignore_punctuation') == 'on',
            'ignore_boilerplate': request.form.get('ignore_boilerplate', 'on') == 'on',
            'normalize_whitespace': request.form.get('normalize_whitespace', 'on') == 'on',
            'diff_granularity': request.form.get('diff_granularity', 'word')
        }
        
        # Validate files
        if 'source_file' not in request.files:
            flash('Source/Reference file is required', 'error')
            return redirect(url_for('index'))
        
        source_file = request.files['source_file']
        comparison_files = request.files.getlist('comparison_files')
        
        if source_file.filename == '':
            flash('Source/Reference file is required', 'error')
            return redirect(url_for('index'))
        
        if not comparison_files or all(f.filename == '' for f in comparison_files):
            flash('At least one comparison file is required', 'error')
            return redirect(url_for('index'))
        
        # Check file limits
        if len(comparison_files) > 20:
            flash('Maximum 20 comparison files allowed', 'error')
            return redirect(url_for('index'))
        
        session_dir = get_session_dir()
        
        # Save and validate source file
        source_filename = secure_filename(source_file.filename)
        source_path = session_dir / f"source_{source_filename}"
        source_file.save(source_path)
        
        is_valid, error_msg = validate_rtf_file(source_path)
        if not is_valid:
            flash(f'Source file error: {error_msg}. Please re-export as Rich Text Format (.rtf)', 'error')
            return redirect(url_for('index'))
        
        # Save and validate comparison files
        comparison_paths = []
        for comp_file in comparison_files:
            if comp_file.filename == '':
                continue
                
            comp_filename = secure_filename(comp_file.filename)
            comp_path = session_dir / f"comp_{comp_filename}"
            comp_file.save(comp_path)
            
            is_valid, error_msg = validate_rtf_file(comp_path)
            if not is_valid:
                flash(f'Comparison file "{comp_filename}" error: {error_msg}. Please re-export as Rich Text Format (.rtf)', 'error')
                return redirect(url_for('index'))
            
            comparison_paths.append((comp_filename, comp_path))
        
        if not comparison_paths:
            flash('No valid comparison files found', 'error')
            return redirect(url_for('index'))
        
        # Process comparisons
        results = []
        source_text = rtf_processor.process_file(source_path, options)
        
        for comp_filename, comp_path in comparison_paths:
            comp_text = rtf_processor.process_file(comp_path, options)
            
            diff_result = diff_generator.compare_texts(
                source_text, comp_text, 
                source_filename, comp_filename,
                options
            )
            
            results.append({
                'filename': comp_filename,
                'has_differences': diff_result['has_differences'],
                'change_count': diff_result['change_count'],
                'diff_html': diff_result['html'],
                'stats': diff_result['stats']
            })
        
        # Store results in session for later retrieval
        session['comparison_results'] = {
            'source_filename': source_filename,
            'results': results,
            'options': options,
            'timestamp': datetime.now().isoformat()
        }
        
        return redirect(url_for('results'))
        
    except RequestEntityTooLarge:
        flash('File too large. Maximum size is 15MB per file.', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        flash(f'Error processing files: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/results')
def results():
    """Display comparison results"""
    if 'comparison_results' not in session:
        flash('No comparison results found. Please upload files first.', 'error')
        return redirect(url_for('index'))
    
    data = session['comparison_results']
    return render_template('results.html', 
                         source_filename=data['source_filename'],
                         results=data['results'],
                         options=data['options'])

@app.route('/diff/<int:file_index>')
def view_diff(file_index):
    """View individual file diff"""
    if 'comparison_results' not in session:
        flash('No comparison results found. Please upload files first.', 'error')
        return redirect(url_for('index'))
    
    data = session['comparison_results']
    if file_index >= len(data['results']):
        flash('Invalid file index', 'error')
        return redirect(url_for('results'))
    
    result = data['results'][file_index]
    return render_template('diff.html',
                         source_filename=data['source_filename'],
                         comparison_filename=result['filename'],
                         diff_html=result['diff_html'],
                         stats=result['stats'],
                         file_index=file_index)

@app.route('/download/report')
def download_report():
    """Download consolidated HTML report"""
    if 'comparison_results' not in session:
        flash('No comparison results found. Please upload files first.', 'error')
        return redirect(url_for('index'))
    
    data = session['comparison_results']
    
    # Generate consolidated report
    report_html = diff_generator.generate_consolidated_report(
        data['source_filename'],
        data['results'],
        data['options']
    )
    
    # Create file-like object
    report_file = io.BytesIO()
    report_file.write(report_html.encode('utf-8'))
    report_file.seek(0)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"rtf_comparison_report_{timestamp}.html"
    
    return send_file(report_file, 
                    as_attachment=True,
                    download_name=filename,
                    mimetype='text/html')

@app.route('/download/csv')
def download_csv():
    """Download summary as CSV"""
    if 'comparison_results' not in session:
        flash('No comparison results found. Please upload files first.', 'error')
        return redirect(url_for('index'))
    
    data = session['comparison_results']
    
    # Create CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(['Source File', 'Comparison File', 'Has Differences', 
                    'Total Changes', 'Insertions', 'Deletions', 'Timestamp'])
    
    # Data rows
    for result in data['results']:
        writer.writerow([
            data['source_filename'],
            result['filename'],
            'Yes' if result['has_differences'] else 'No',
            result['change_count'],
            result['stats']['insertions'],
            result['stats']['deletions'],
            data['timestamp']
        ])
    
    # Create file-like object
    csv_content = output.getvalue()
    csv_file = io.BytesIO()
    csv_file.write(csv_content.encode('utf-8'))
    csv_file.seek(0)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"rtf_comparison_summary_{timestamp}.csv"
    
    return send_file(csv_file,
                    as_attachment=True,
                    download_name=filename,
                    mimetype='text/csv')

@app.errorhandler(413)
def too_large(e):
    flash('File too large. Maximum size is 15MB per file.', 'error')
    return redirect(url_for('index'))

@app.errorhandler(500)
def server_error(e):
    flash('An internal server error occurred. Please try again.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
