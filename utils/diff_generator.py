"""
Diff generation utilities for text comparison and HTML report creation
"""

import difflib
import re
from datetime import datetime

class DiffGenerator:
    def __init__(self):
        """Initialize diff generator with styling"""
        self.css_styles = """
        <style>
        .diff-container { font-family: 'Courier New', monospace; font-size: 14px; }
        .diff-table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        .diff-table th, .diff-table td { padding: 8px; border: 1px solid #ddd; vertical-align: top; }
        .diff-table th { background-color: #f5f5f5; font-weight: bold; }
        .line-number { background-color: #f0f0f0; color: #666; text-align: right; width: 50px; }
        .diff-added { background-color: #d4edda; }
        .diff-deleted { background-color: #f8d7da; }
        .diff-changed { background-color: #fff3cd; }
        .word-added { background-color: #28a745; color: white; padding: 2px 4px; border-radius: 3px; }
        .word-deleted { background-color: #dc3545; color: white; padding: 2px 4px; border-radius: 3px; text-decoration: line-through; }
        .summary-box { background-color: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .stats { display: flex; gap: 20px; margin: 10px 0; }
        .stat-item { padding: 10px; border-radius: 5px; text-align: center; }
        .stat-added { background-color: #d4edda; color: #155724; }
        .stat-deleted { background-color: #f8d7da; color: #721c24; }
        .stat-unchanged { background-color: #d1ecf1; color: #0c5460; }
        .legend { background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .legend-item { display: inline-block; margin-right: 15px; }
        .diff-unchanged { color: #666; }
        .file-header { background-color: #007bff; color: white; padding: 15px; border-radius: 5px; margin: 20px 0; }
        .context-line { background-color: #f8f9fa; }
        </style>
        """
    
    def compare_texts(self, source_text, comparison_text, source_filename, comparison_filename, options):
        """
        Compare two texts and generate diff results
        
        Args:
            source_text: Source/reference text
            comparison_text: Text to compare against source
            source_filename: Name of source file
            comparison_filename: Name of comparison file
            options: Comparison options
            
        Returns:
            Dict with comparison results
        """
        if options.get('diff_granularity') == 'word':
            return self._word_level_diff(source_text, comparison_text, source_filename, comparison_filename, options)
        else:
            return self._line_level_diff(source_text, comparison_text, source_filename, comparison_filename, options)
    
    def _word_level_diff(self, source_text, comparison_text, source_filename, comparison_filename, options):
        """Generate word-level diff"""
        source_words = self._tokenize_for_diff(source_text)
        comparison_words = self._tokenize_for_diff(comparison_text)
        
        # Generate sequence matcher
        matcher = difflib.SequenceMatcher(None, source_words, comparison_words)
        
        # Build diff HTML
        html_parts = [self.css_styles]
        html_parts.append(f'<div class="diff-container">')
        html_parts.append(f'<div class="file-header">')
        html_parts.append(f'<h2>Comparison: {comparison_filename} vs {source_filename}</h2>')
        html_parts.append(f'</div>')
        
        # Statistics
        opcodes = matcher.get_opcodes()
        insertions = sum(1 for tag, _, _, _, _ in opcodes if tag == 'insert')
        deletions = sum(1 for tag, _, _, _, _ in opcodes if tag == 'delete')
        replacements = sum(1 for tag, _, _, _, _ in opcodes if tag == 'replace')
        
        stats = {
            'insertions': insertions,
            'deletions': deletions,
            'replacements': replacements,
            'total_changes': insertions + deletions + replacements
        }
        
        html_parts.append(f'<div class="summary-box">')
        html_parts.append(f'<h3>Summary</h3>')
        html_parts.append(f'<div class="stats">')
        html_parts.append(f'<div class="stat-item stat-added">Insertions: {insertions}</div>')
        html_parts.append(f'<div class="stat-item stat-deleted">Deletions: {deletions}</div>')
        html_parts.append(f'<div class="stat-item stat-unchanged">Replacements: {replacements}</div>')
        html_parts.append(f'</div>')
        html_parts.append(f'</div>')
        
        # Legend
        html_parts.append('<div class="legend">')
        html_parts.append('<strong>Legend:</strong> ')
        html_parts.append('<span class="legend-item"><span class="word-added">Added</span></span>')
        html_parts.append('<span class="legend-item"><span class="word-deleted">Deleted</span></span>')
        html_parts.append('<span class="legend-item"><span class="diff-unchanged">Unchanged</span></span>')
        html_parts.append('</div>')
        
        # Diff table
        html_parts.append('<table class="diff-table">')
        html_parts.append('<thead><tr><th width="50">Line</th><th width="50%">Source</th><th width="50%">Comparison</th></tr></thead>')
        html_parts.append('<tbody>')
        
        source_line_num = 1
        comp_line_num = 1
        
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'equal':
                # Show a few context lines for equal sections
                equal_text = ' '.join(source_words[i1:i2])
                lines = equal_text.split('\n')
                for line in lines[:3]:  # Show first 3 lines of context
                    if line.strip():
                        html_parts.append(f'<tr class="context-line">')
                        html_parts.append(f'<td class="line-number">{source_line_num}</td>')
                        html_parts.append(f'<td class="diff-unchanged">{self._escape_html(line[:100])}{"..." if len(line) > 100 else ""}</td>')
                        html_parts.append(f'<td class="diff-unchanged">{self._escape_html(line[:100])}{"..." if len(line) > 100 else ""}</td>')
                        html_parts.append('</tr>')
                        source_line_num += 1
                        comp_line_num += 1
                if len(lines) > 6:
                    html_parts.append('<tr><td colspan="3" style="text-align: center; color: #666;">... (identical content) ...</td></tr>')
                for line in lines[-3:]:  # Show last 3 lines of context
                    if line.strip() and len(lines) > 3:
                        html_parts.append(f'<tr class="context-line">')
                        html_parts.append(f'<td class="line-number">{source_line_num}</td>')
                        html_parts.append(f'<td class="diff-unchanged">{self._escape_html(line[:100])}{"..." if len(line) > 100 else ""}</td>')
                        html_parts.append(f'<td class="diff-unchanged">{self._escape_html(line[:100])}{"..." if len(line) > 100 else ""}</td>')
                        html_parts.append('</tr>')
                        source_line_num += 1
                        comp_line_num += 1
            
            elif tag == 'delete':
                deleted_text = ' '.join(source_words[i1:i2])
                html_parts.append('<tr class="diff-deleted">')
                html_parts.append(f'<td class="line-number">{source_line_num}</td>')
                html_parts.append(f'<td><span class="word-deleted">{self._escape_html(deleted_text)}</span></td>')
                html_parts.append('<td></td>')
                html_parts.append('</tr>')
                source_line_num += deleted_text.count('\n') + 1
            
            elif tag == 'insert':
                inserted_text = ' '.join(comparison_words[j1:j2])
                html_parts.append('<tr class="diff-added">')
                html_parts.append(f'<td class="line-number">{comp_line_num}</td>')
                html_parts.append('<td></td>')
                html_parts.append(f'<td><span class="word-added">{self._escape_html(inserted_text)}</span></td>')
                html_parts.append('</tr>')
                comp_line_num += inserted_text.count('\n') + 1
            
            elif tag == 'replace':
                source_text_part = ' '.join(source_words[i1:i2])
                comp_text_part = ' '.join(comparison_words[j1:j2])
                html_parts.append('<tr class="diff-changed">')
                html_parts.append(f'<td class="line-number">{source_line_num}</td>')
                html_parts.append(f'<td><span class="word-deleted">{self._escape_html(source_text_part)}</span></td>')
                html_parts.append(f'<td><span class="word-added">{self._escape_html(comp_text_part)}</span></td>')
                html_parts.append('</tr>')
                source_line_num += source_text_part.count('\n') + 1
                comp_line_num += comp_text_part.count('\n') + 1
        
        html_parts.append('</tbody></table>')
        html_parts.append('</div>')
        
        html_content = '\n'.join(html_parts)
        
        return {
            'has_differences': stats['total_changes'] > 0,
            'change_count': stats['total_changes'],
            'html': html_content,
            'stats': stats
        }
    
    def _line_level_diff(self, source_text, comparison_text, source_filename, comparison_filename, options):
        """Generate line-level diff"""
        source_lines = source_text.splitlines()
        comparison_lines = comparison_text.splitlines()
        
        # Generate HTML diff
        differ = difflib.HtmlDiff(wrapcolumn=80)
        html_diff = differ.make_file(
            source_lines, comparison_lines,
            fromdesc=f"{source_filename} (Source)",
            todesc=f"{comparison_filename} (Comparison)"
        )
        
        # Count changes
        matcher = difflib.SequenceMatcher(None, source_lines, comparison_lines)
        opcodes = matcher.get_opcodes()
        
        insertions = sum(j2 - j1 for tag, _, _, j1, j2 in opcodes if tag == 'insert')
        deletions = sum(i2 - i1 for tag, i1, i2, _, _ in opcodes if tag == 'delete')
        replacements = sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in opcodes if tag == 'replace')
        
        stats = {
            'insertions': insertions,
            'deletions': deletions,
            'replacements': replacements,
            'total_changes': insertions + deletions + replacements
        }
        
        return {
            'has_differences': stats['total_changes'] > 0,
            'change_count': stats['total_changes'],
            'html': html_diff,
            'stats': stats
        }
    
    def _tokenize_for_diff(self, text):
        """Tokenize text for word-level diffing"""
        # Split on whitespace and punctuation but keep structure
        words = []
        current_word = ""
        
        for char in text:
            if char.isalnum():
                current_word += char
            else:
                if current_word:
                    words.append(current_word)
                    current_word = ""
                if char.strip():  # Non-whitespace punctuation
                    words.append(char)
                elif char in '\n\r':
                    words.append('\n')
                elif char.isspace():
                    words.append(' ')
        
        if current_word:
            words.append(current_word)
        
        return words
    
    def _escape_html(self, text):
        """Escape HTML characters"""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#x27;'))
    
    def generate_consolidated_report(self, source_filename, results, options):
        """Generate consolidated HTML report for all comparisons"""
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '<title>RTF Comparison Report</title>',
            self.css_styles,
            '</head>',
            '<body>',
            '<div class="diff-container">',
            '<h1>RTF Comparison Report</h1>',
            f'<p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>',
            f'<p><strong>Source/Reference File:</strong> {source_filename}</p>',
            '<div class="summary-box">',
            '<h2>Summary</h2>',
            f'<p>Compared {len(results)} file(s) against the source.</p>',
            '<table class="diff-table">',
            '<thead>',
            '<tr><th>File</th><th>Status</th><th>Changes</th><th>Insertions</th><th>Deletions</th></tr>',
            '</thead>',
            '<tbody>'
        ]
        
        # Summary table
        for result in results:
            status = "Differences Found" if result['has_differences'] else "No Differences"
            status_class = "diff-changed" if result['has_differences'] else "diff-unchanged"
            html_parts.append(f'<tr class="{status_class}">')
            html_parts.append(f'<td>{result["filename"]}</td>')
            html_parts.append(f'<td>{status}</td>')
            html_parts.append(f'<td>{result["change_count"]}</td>')
            html_parts.append(f'<td>{result["stats"]["insertions"]}</td>')
            html_parts.append(f'<td>{result["stats"]["deletions"]}</td>')
            html_parts.append('</tr>')
        
        html_parts.extend([
            '</tbody>',
            '</table>',
            '</div>',
            '<h2>Detailed Comparisons</h2>'
        ])
        
        # Individual diffs
        for i, result in enumerate(results):
            if result['has_differences']:
                html_parts.append(f'<div id="diff-{i}">')
                html_parts.append(result['diff_html'])
                html_parts.append('</div>')
                html_parts.append('<hr style="margin: 40px 0;">')
        
        html_parts.extend([
            '</div>',
            '</body>',
            '</html>'
        ])
        
        return '\n'.join(html_parts)
