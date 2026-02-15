import feedparser
import json
import os
import re
from datetime import datetime, timedelta
import pytz

# --- CONFIGURATION ---
RSS_FEED_URL = "https://www.freejobalert.com/feed"
DB_FILE = "jobs.json" # The file where we store job history

# Keywords
WB_KEYWORDS = ["west bengal", "wb ", "wbpsc", "kolkata", "wbhrb", "wb police", "wbp ", "calcutta"]
CENTRAL_KEYWORDS = ["upsc", "ssc", "central", "railway", "rrb", "ibps", "sbi", "drdo", "isro", "army", "navy", "air force", "bsf", "bank"]

def get_job_category(title):
    title_lower = title.lower()
    for k in WB_KEYWORDS:
        if k in title_lower: return "WB"
    for k in CENTRAL_KEYWORDS:
        if k in title_lower: return "CENTRAL"
    return "OTHER"

# Helper: Try to find a date inside text like "Last Date: 25-02-2026"
def extract_last_date(text):
    match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', text)
    if match:
        return match.group(1)
    return "Check Link"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    return []

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def update_jobs():
    # 1. Load History
    current_jobs = load_db()
    
    # 2. Fetch New Data
    print(f"Fetching jobs from {RSS_FEED_URL}...")
    feed = feedparser.parse(RSS_FEED_URL)
    new_entries = []
    
    # Get today's date for "New" badge
    ist = pytz.timezone('Asia/Kolkata')
    today_str = datetime.now(ist).strftime("%Y-%m-%d")

    for entry in feed.entries:
        link = entry.link
        
        # Check if we already have this job (by Link)
        if any(job['link'] == link for job in current_jobs):
            continue # Skip duplicates
            
        clean_title = entry.title.split("Last Date")[0].strip()
        category = get_job_category(clean_title)
        
        # Try to find Last Date in the summary text
        last_date = extract_last_date(entry.summary if hasattr(entry, 'summary') else "")
        
        new_job = {
            "title": clean_title,
            "link": link,
            "category": category,
            "last_date": last_date,
            "added_on": today_str,  # We save when we found it
            "is_new": True
        }
        new_entries.append(new_job)

    # 3. Add new jobs to the TOP of the list
    updated_jobs = new_entries + current_jobs
    
    # 4. Cleanup: Remove jobs older than 45 days to prevent clutter
    # (Optional: You can remove this block if you want infinite history)
    cutoff_date = (datetime.now(ist) - timedelta(days=45)).strftime("%Y-%m-%d")
    updated_jobs = [job for job in updated_jobs if job.get('added_on', '2025-01-01') > cutoff_date]

    # 5. Save back to database
    save_db(updated_jobs)
    return updated_jobs

def generate_html(jobs):
    wb_jobs = [j for j in jobs if j['category'] == "WB"]
    central_jobs = [j for j in jobs if j['category'] == "CENTRAL"]
    other_jobs = [j for j in jobs if j['category'] == "OTHER"]

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sarkari Job Archive</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #f8f9fa; margin: 0; padding: 20px; }
            .container { max-width: 900px; margin: 0 auto; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
            h1 { text-align: center; color: #333; }
            .update-time { text-align: center; color: #888; font-size: 0.9rem; margin-bottom: 30px; }
            
            .section-header { 
                padding: 12px 20px; color: white; margin-top: 30px; border-radius: 8px; 
                font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;
            }
            .wb-header { background: #28a745; } 
            .central-header { background: #007bff; }
            .other-header { background: #6c757d; }
            
            .job-item { 
                border-bottom: 1px solid #f1f1f1; padding: 15px 10px; display: flex; 
                justify-content: space-between; align-items: center; flex-wrap: wrap;
            }
            .job-info { flex: 1; }
            .job-title { color: #343a40; font-weight: 600; text-decoration: none; font-size: 1rem; display: block; }
            .job-title:hover { color: #0056b3; }
            
            .meta-row { font-size: 0.85rem; color: #666; margin-top: 4px; }
            
            .last-date-btn { 
                background: #fff3cd; color: #856404; padding: 4px 10px; 
                border-radius: 4px; border: 1px solid #ffeeba; font-size: 0.8rem; font-weight: bold;
                margin-right: 10px;
            }
            
            .new-badge { 
                background: #ff4757; color: white; padding: 2px 6px; border-radius: 4px; 
                font-size: 0.7rem; font-weight: bold; margin-left: 8px; vertical-align: middle;
            }

            .apply-btn { 
                background: #343a40; color: white; padding: 6px 15px; text-decoration: none; 
                border-radius: 5px; font-size: 0.85rem; white-space: nowrap;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Job Archive & Tracker</h1>
            <div class="update-time">Last Updated: {DATE_PLACEHOLDER}</div>

            <div class="section-header wb-header">🟢 West Bengal Jobs</div>
            <div>{WB_LIST}</div>

            <div class="section-header central-header">🔵 Central Govt Jobs</div>
            <div>{CENTRAL_LIST}</div>

            <div class="section-header other-header">⚪ Other Updates</div>
            <div>{OTHER_LIST}</div>
        </div>
    </body>
    </html>
    """
    
    # Get today for marking "New"
    ist = pytz.timezone('Asia/Kolkata')
    today_str = datetime.now(ist).strftime("%Y-%m-%d")

    def make_list(jobs):
        if not jobs: return "<p style='padding:15px; color:#999; text-align:center;'>No jobs found in database.</p>"
        items = ""
        for job in jobs:
            # Show NEW badge if added today
            new_tag = '<span class="new-badge">NEW</span>' if job.get('added_on') == today_str else ""
            
            # Last Date Logic
            ld_text = job.get('last_date', 'Check Link')
            ld_display = f'<span class="last-date-btn">⏳ Last Date: {ld_text}</span>'
            
            items += f"""
            <div class="job-item">
                <div class="job-info">
                    <a href="{job['link']}" target="_blank" class="job-title">{job['title']} {new_tag}</a>
                    <div class="meta-row">
                        {ld_display}
                    </div>
                </div>
                <a href="{job['link']}" target="_blank" class="apply-btn">View</a>
            </div>
            """
        return items

    now = datetime.now(ist).strftime("%d %b %Y, %I:%M %p IST")
    final_html = html.replace("{DATE_PLACEHOLDER}", now)
    final_html = final_html.replace("{WB_LIST}", make_list(wb_jobs))
    final_html = final_html.replace("{CENTRAL_LIST}", make_list(central_jobs))
    final_html = final_html.replace("{OTHER_LIST}", make_list(other_jobs))

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)

if __name__ == "__main__":
    all_jobs = update_jobs()
    generate_html(all_jobs)
    print("Database updated and HTML generated.")
