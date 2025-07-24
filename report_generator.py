import re
from datetime import datetime


def generate_html_report(messages):
    """Generate a nice HTML report of filtered jobs"""
    if not messages:
        return "<html><body><h1>No jobs found</h1></body></html>"

    # Group by channel for better organization
    channels = {}
    for msg in messages:
        channel = msg['channel']
        if channel not in channels:
            channels[channel] = []
        channels[channel].append(msg)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Job Filter Results - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; margin-bottom: 20px; }}
            .stats {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .channel-section {{ margin-bottom: 30px; }}
            .channel-title {{ background: #007acc; color: white; padding: 10px; margin: 0; border-radius: 5px 5px 0 0; }}
            .job-card {{ border: 1px solid #ddd; margin-bottom: 15px; border-radius: 0 0 5px 5px; }}
            .job-header {{ background: #f8f9fa; padding: 10px; border-bottom: 1px solid #ddd; }}
            .job-content {{ padding: 15px; }}
            .job-meta {{ font-size: 12px; color: #666; }}
            .keywords {{ background: #fff3cd; padding: 5px 10px; border-radius: 3px; display: inline-block; margin: 5px 5px 0 0; }}
            .contact-info {{ color: #28a745; font-weight: bold; }}
            .job-link {{ color: #007acc; text-decoration: none; }}
            .job-link:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 Job Filter Results</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
            </div>

            <div class="stats">
                <strong>📊 Summary:</strong> 
                Found {len(messages)} jobs from {len(channels)} channels
            </div>
    """

    for channel, jobs in channels.items():
        html += f"""
            <div class="channel-section">
                <h2 class="channel-title">📢 {channel} ({len(jobs)} jobs)</h2>
                <div class="job-cards">
        """

        for job in jobs:
            # Highlight keywords in text
            text = job['text']
            for keyword in job.get('matched_keywords', []):
                text = re.sub(f"({re.escape(keyword)})", r'<span class="keywords">\1</span>', text, flags=re.IGNORECASE)

            # Check for contact info
            has_contact = "✅" if job.get('has_contact') else "❌"

            html += f"""
                <div class="job-card">
                    <div class="job-header">
                        <div class="job-meta">
                            📅 {job['date'][:19]} | 📝 {job.get('word_count', 0)} words | 📞 Contact: {has_contact}
                            <a href="{job.get('url', '#')}" class="job-link" target="_blank">🔗 View Original</a>
                        </div>
                    </div>
                    <div class="job-content">
                        {text.replace('\n', '<br>')}
                    </div>
                </div>
            """

        html += """
                </div>
            </div>
        """

    html += """
        </div>
    </body>
    </html>
    """

    return html


def save_html_report(messages, filename=None):
    """Save HTML report to file"""
    if not filename:
        filename = f"job_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

    html_content = generate_html_report(messages)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"📄 HTML report saved to {filename}")
    return filename