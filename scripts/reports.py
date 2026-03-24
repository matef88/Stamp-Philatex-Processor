"""
Stamp Philatex Processor - Report Generation Module
Generates processing reports in various formats.
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import csv

try:
    from utils import load_config, get_project_root, setup_logging, ensure_dirs, format_duration
    from database import StampDatabase
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from scripts.utils import load_config, get_project_root, setup_logging, ensure_dirs, format_duration
    from scripts.database import StampDatabase


class ReportGenerator:
    """
    Generates processing reports in multiple formats.

    Supported formats:
    - HTML: Visual report with thumbnails
    - JSON: Machine-readable data
    - CSV: Spreadsheet-compatible
    - TXT: Plain text summary
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize report generator.

        Args:
            config: Configuration dictionary
        """
        self.config = config or load_config()
        self.logger = setup_logging("ReportGenerator")

        self.project_root = get_project_root()
        self.reports_dir = self.project_root / self.config.get('paths', {}).get('reports', 'output/reports')
        ensure_dirs([self.reports_dir])

        self.database = StampDatabase()

    def generate_batch_report(
        self,
        batch_id: str,
        results: List[Dict],
        format: str = 'html'
    ) -> Path:
        """
        Generate report for a processing batch.

        Args:
            batch_id: Batch identifier
            results: List of processing results
            format: Output format ('html', 'json', 'csv', 'txt')

        Returns:
            Path to generated report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"batch_report_{batch_id}_{timestamp}"

        if format == 'html':
            return self._generate_html_report(filename, results, batch_id)
        elif format == 'json':
            return self._generate_json_report(filename, results, batch_id)
        elif format == 'csv':
            return self._generate_csv_report(filename, results)
        else:  # txt
            return self._generate_txt_report(filename, results, batch_id)

    def _generate_html_report(
        self,
        filename: str,
        results: List[Dict],
        batch_id: str
    ) -> Path:
        """Generate HTML report with visual elements."""

        # Calculate statistics
        total = len(results)
        successful = sum(1 for r in results if r.get('success', False))
        failed = total - successful
        duplicates = sum(1 for r in results if r.get('is_duplicate', False))
        avg_confidence = sum(r.get('confidence', 0) for r in results) / total if total > 0 else 0
        total_time = sum(r.get('processing_time', 0) for r in results)

        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stamp Processing Report - {batch_id}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: #4ecca3; margin-bottom: 20px; }}
        h2 {{ color: #4ecca3; margin: 20px 0 10px; border-bottom: 1px solid #333; padding-bottom: 5px; }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #16213e;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #4ecca3;
        }}
        .stat-card .label {{ color: #888; margin-top: 5px; }}
        .stat-card.error .value {{ color: #ff6b6b; }}
        .stat-card.warning .value {{ color: #ffd93d; }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #333;
        }}
        th {{ background: #16213e; color: #4ecca3; }}
        tr:hover {{ background: rgba(78, 204, 163, 0.1); }}

        .success {{ color: #4ecca3; }}
        .error {{ color: #ff6b6b; }}
        .duplicate {{ color: #ffd93d; }}

        .thumbnail {{
            width: 60px;
            height: 60px;
            object-fit: cover;
            border-radius: 5px;
        }}

        .footer {{
            margin-top: 30px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Stamp Processing Report</h1>
        <p style="color: #888; margin-bottom: 20px;">
            Batch ID: {batch_id} | Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        </p>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="value">{total}</div>
                <div class="label">Total Images</div>
            </div>
            <div class="stat-card">
                <div class="value">{successful}</div>
                <div class="label">Successful</div>
            </div>
            <div class="stat-card error">
                <div class="value">{failed}</div>
                <div class="label">Failed</div>
            </div>
            <div class="stat-card warning">
                <div class="value">{duplicates}</div>
                <div class="label">Duplicates</div>
            </div>
            <div class="stat-card">
                <div class="value">{avg_confidence:.1%}</div>
                <div class="label">Avg Confidence</div>
            </div>
            <div class="stat-card">
                <div class="value">{format_duration(total_time)}</div>
                <div class="label">Total Time</div>
            </div>
        </div>

        <h2>Processing Results</h2>
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>Status</th>
                    <th>Confidence</th>
                    <th>Detections</th>
                    <th>Time</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
'''

        for r in results:
            status_class = 'success' if r.get('success') else 'error'
            if r.get('is_duplicate'):
                status_class = 'duplicate'

            status_text = 'Success' if r.get('success') else 'Failed'
            if r.get('is_duplicate'):
                status_text = 'Duplicate'

            notes = r.get('error_message', '')
            if r.get('is_duplicate') and r.get('duplicate_of'):
                notes = f"Duplicate of: {r.get('duplicate_of')}"

            html_content += f'''
                <tr>
                    <td>{Path(r.get("input_path", "")).name}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{r.get("confidence", 0):.1%}</td>
                    <td>{r.get("num_detections", 0)}</td>
                    <td>{r.get("processing_time", 0):.2f}s</td>
                    <td>{notes}</td>
                </tr>
'''

        html_content += '''
            </tbody>
        </table>

        <div class="footer">
            <p>Generated by Stamp Philatex Processor</p>
        </div>
    </div>
</body>
</html>
'''

        output_path = self.reports_dir / f"{filename}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        self.logger.info(f"HTML report generated: {output_path}")
        return output_path

    def _generate_json_report(
        self,
        filename: str,
        results: List[Dict],
        batch_id: str
    ) -> Path:
        """Generate JSON report."""

        total = len(results)
        successful = sum(1 for r in results if r.get('success', False))

        report_data = {
            'batch_id': batch_id,
            'generated': datetime.now().isoformat(),
            'statistics': {
                'total': total,
                'successful': successful,
                'failed': total - successful,
                'duplicates': sum(1 for r in results if r.get('is_duplicate', False)),
                'average_confidence': sum(r.get('confidence', 0) for r in results) / total if total > 0 else 0,
                'total_time': sum(r.get('processing_time', 0) for r in results)
            },
            'results': []
        }

        for r in results:
            result_entry = {
                'input_path': str(r.get('input_path', '')),
                'output_path': str(r.get('output_path', '')) if r.get('output_path') else None,
                'success': r.get('success', False),
                'confidence': r.get('confidence', 0),
                'num_detections': r.get('num_detections', 0),
                'processing_time': r.get('processing_time', 0),
                'is_duplicate': r.get('is_duplicate', False),
                'error_message': r.get('error_message')
            }
            report_data['results'].append(result_entry)

        output_path = self.reports_dir / f"{filename}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str)

        self.logger.info(f"JSON report generated: {output_path}")
        return output_path

    def _generate_csv_report(self, filename: str, results: List[Dict]) -> Path:
        """Generate CSV report."""

        output_path = self.reports_dir / f"{filename}.csv"

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                'Input File', 'Output File', 'Success', 'Confidence',
                'Detections', 'Processing Time', 'Is Duplicate', 'Error'
            ])

            # Data rows
            for r in results:
                writer.writerow([
                    Path(r.get('input_path', '')).name,
                    Path(r.get('output_path', '')).name if r.get('output_path') else '',
                    r.get('success', False),
                    f"{r.get('confidence', 0):.2%}",
                    r.get('num_detections', 0),
                    f"{r.get('processing_time', 0):.2f}s",
                    r.get('is_duplicate', False),
                    r.get('error_message', '')
                ])

        self.logger.info(f"CSV report generated: {output_path}")
        return output_path

    def _generate_txt_report(
        self,
        filename: str,
        results: List[Dict],
        batch_id: str
    ) -> Path:
        """Generate plain text report."""

        total = len(results)
        successful = sum(1 for r in results if r.get('success', False))
        failed = total - successful
        duplicates = sum(1 for r in results if r.get('is_duplicate', False))
        total_time = sum(r.get('processing_time', 0) for r in results)

        content = f'''
================================================================================
                        STAMP PROCESSING REPORT
================================================================================

Batch ID: {batch_id}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

--------------------------------------------------------------------------------
                              SUMMARY
--------------------------------------------------------------------------------
Total Images:      {total}
Successful:        {successful}
Failed:            {failed}
Duplicates:        {duplicates}
Total Time:        {format_duration(total_time)}
Average Time:      {format_duration(total_time/total if total > 0 else 0)} per image

--------------------------------------------------------------------------------
                           DETAILED RESULTS
--------------------------------------------------------------------------------
'''

        # Successful
        successful_results = [r for r in results if r.get('success') and not r.get('is_duplicate')]
        if successful_results:
            content += f"\nSUCCESSFUL ({len(successful_results)}):\n"
            for r in successful_results:
                content += f"  + {Path(r.get('input_path', '')).name} "
                content += f"(conf: {r.get('confidence', 0):.1%}, {r.get('num_detections', 0)} stamps)\n"

        # Duplicates
        duplicate_results = [r for r in results if r.get('is_duplicate')]
        if duplicate_results:
            content += f"\nDUPLICATES ({len(duplicate_results)}):\n"
            for r in duplicate_results:
                content += f"  ~ {Path(r.get('input_path', '')).name}\n"

        # Failed
        failed_results = [r for r in results if not r.get('success')]
        if failed_results:
            content += f"\nFAILED ({len(failed_results)}):\n"
            for r in failed_results:
                content += f"  - {Path(r.get('input_path', '')).name}: {r.get('error_message', 'Unknown error')}\n"

        content += '''
================================================================================
                          END OF REPORT
================================================================================
'''

        output_path = self.reports_dir / f"{filename}.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        self.logger.info(f"Text report generated: {output_path}")
        return output_path

    def generate_duplicate_report(self, format: str = 'html') -> Path:
        """
        Generate report of all duplicates in database.

        Args:
            format: Output format

        Returns:
            Path to report file
        """
        # Import here to avoid circular dependency
        from duplicate_detector import DuplicateDetector

        detector = DuplicateDetector(self.config)
        groups = detector.get_duplicate_groups()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"duplicate_report_{timestamp}"

        if format == 'html':
            return self._generate_duplicate_html_report(filename, groups)
        else:
            return self._generate_duplicate_txt_report(filename, groups)

    def _generate_duplicate_html_report(
        self,
        filename: str,
        groups: List[List[Dict]]
    ) -> Path:
        """Generate HTML duplicate report."""

        total_duplicates = sum(len(g) - 1 for g in groups)  # -1 for original in each group

        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Duplicate Stamps Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            padding: 20px;
        }}
        h1 {{ color: #ffd93d; }}
        h2 {{ color: #4ecca3; margin-top: 30px; }}
        .stats {{ margin: 20px 0; font-size: 1.2em; }}
        .group {{
            background: #16213e;
            padding: 15px;
            margin: 15px 0;
            border-radius: 10px;
            border-left: 4px solid #ffd93d;
        }}
        .group h3 {{ color: #ffd93d; margin-bottom: 10px; }}
        .stamp {{ padding: 5px 0; border-bottom: 1px solid #333; }}
        .stamp:last-child {{ border-bottom: none; }}
    </style>
</head>
<body>
    <h1>Duplicate Stamps Report</h1>
    <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>

    <div class="stats">
        <p>Total Duplicate Groups: <strong>{len(groups)}</strong></p>
        <p>Total Duplicate Images: <strong>{total_duplicates}</strong></p>
    </div>

    <h2>Duplicate Groups</h2>
'''

        for i, group in enumerate(groups, 1):
            html_content += f'''
    <div class="group">
        <h3>Group {i} ({len(group)} images)</h3>
'''
            for stamp in group:
                html_content += f'''
        <div class="stamp">
            <strong>{Path(stamp.get("original_path", "")).name}</strong>
            <br>Processed: {stamp.get("processed_date", "Unknown")}
            <br>Confidence: {stamp.get("confidence", 0):.1%}
        </div>
'''
            html_content += '    </div>\n'

        html_content += '''
</body>
</html>
'''

        output_path = self.reports_dir / f"{filename}.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        return output_path

    def _generate_duplicate_txt_report(
        self,
        filename: str,
        groups: List[List[Dict]]
    ) -> Path:
        """Generate text duplicate report."""

        content = f'''
================================================================================
                        DUPLICATE STAMPS REPORT
================================================================================
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Total Duplicate Groups: {len(groups)}
Total Duplicate Images: {sum(len(g) - 1 for g in groups)}

--------------------------------------------------------------------------------
'''

        for i, group in enumerate(groups, 1):
            content += f"\nGROUP {i} ({len(group)} images):\n"
            for stamp in group:
                content += f"  - {Path(stamp.get('original_path', '')).name}\n"

        output_path = self.reports_dir / f"{filename}.txt"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path


if __name__ == "__main__":
    # Test report generation
    generator = ReportGenerator()

    # Generate sample report
    sample_results = [
        {'input_path': 'test1.jpg', 'output_path': 'test1_processed.jpg', 'success': True, 'confidence': 0.95, 'num_detections': 1, 'processing_time': 0.5},
        {'input_path': 'test2.jpg', 'output_path': 'test2_processed.jpg', 'success': True, 'confidence': 0.87, 'num_detections': 3, 'processing_time': 0.8, 'is_duplicate': True},
        {'input_path': 'test3.jpg', 'success': False, 'confidence': 0, 'num_detections': 0, 'processing_time': 0.2, 'error_message': 'No stamps detected'},
    ]

    report_path = generator.generate_batch_report('test_batch', sample_results, format='html')
    print(f"Report generated: {report_path}")
