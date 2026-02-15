import feedparser
from datetime import datetime
import pytz

# --- CONFIGURATION ---
# We use the FreeJobAlert RSS Feed
RSS_FEED_URL = "https://www.freejobalert.com/feed"

# Keywords for West Bengal (Case Insensitive)
WB_KEYWORDS = [
    "west bengal", "wb ", "wbpsc", "kolkata", "wbhrb", "wb police", 
    "wbsetcl", "wbsedcl", "wbhealth", "calcutta", "wbp ", "wbconstable"
]

# Keywords for Central Govt
CENTRAL_KEYWORDS = [
    "upsc", "ssc", "central", "railway", "rrb", "ibps", "sbi", "rbi", 
    "navy", "army", "air force", "drdo", "isro", "bsf", "crpf", "cisf", 
    "itbp", "ssb", "nia", "assam rifles", "india post", "gds", "aicte",
    "ugc", "ntpc", "ongc", "bhel", "gail", "sail", "coal india", "lic"
]

def get_job_category(title):
    title_lower = title.lower()

    # Check for West Bengal
    for keyword in WB_KEYWORDS:
        if keyword in title_lower:
            return "WB"

    # Check for Central Govt
    for keyword in CENTRAL_KEYWORDS:
        if keyword in title_lower:
            return "CENTRAL"

    return None

def fetch_jobs():
    wb_jobs = []
    central_jobs = []

    try:
        print(f"Fetching jobs from {RSS_FEED_URL}...")
        feed = feedparser.parse(RSS_FEED_URL)

        for entry in feed.entries:
            # Clean title to remove "Last Date" info for cleaner look
            clean_title = entry.title.split("Last Date")[0].strip()
            category = get_job_category(clean_title)

            job_data = {
                "title": clean_title,
                "link": entry.link,
                "date": entry.published,
            }

            if category == "WB":
                wb_jobs.append(job_data)
            elif category == "CENTRAL":
                central_jobs.append(job_data)

    except Exception as e:
        print(f"Error: {e}")

    return wb_jobs, central_jobs

def generate_html(wb_jobs, central_jobs):
    # HTML Template
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WB & Central Job Alerts</title>
        <style>
            body { font-family: sans-serif; background: #f4f6f8; margin: 0; padding: 20px; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
            h1 { text-align: center; color: #2c3e50; }
            .update-time { text-align: center; color: #7f8c8d; font-size: 0.9rem; margin-bottom: 20px; }

            .section-header { 
                padding: 10px; color: white; margin-top: 20px; border-radius: 5px; 
                font-weight: bold; letter-spacing: 1px;
            }
            .wb-header { background-color: #27ae60; } /* Green for WB */
            .central-header { background-color: #2980b9; } /* Blue for Central */

            .job-item { 
                border-bottom: 1px solid #eee; padding: 15px 0; display: flex; 
                justify-content: space-between; align-items: center; 
            }
            .job-item:last-child { border-bottom: none; }

            .job-title { color: #34495e; font-weight: 600; text-decoration: none; font-size: 1.1rem; }
            .job-title:hover { text-decoration: underline; color: #e67e22; }
            .apply-btn { 
                background: #e67e22; color: white; padding: 5px 15px; text-decoration: none; 
                border-radius: 20px; font-size: 0.9rem; white-space: nowrap; margin-left: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Sarkari Job Tracker</h1>
            <div class="update-time">Last Updated: {DATE_PLACEHOLDER}</div>

            <div class="section-header wb-header">🟢 WEST BENGAL GOVT JOBS</div>
            <div id="wb-list">{WB_LIST}</div>

            <div class="section-header central-header">🔵 CENTRAL GOVT JOBS</div>
            <div id="central-list">{CENTRAL_LIST}</div>
        </div>
    </body>
    </html>
    """

    def make_list(jobs):
        if not jobs: return "<p style='padding:10px; color:#999;'>No new updates found today.</p>"
        items = ""
        for job in jobs:
            items += f"""
            <div class="job-item">
                <a href="{job['link']}" target="_blank" class="job-title">{job['title']}</a>
                <a href="{job['link']}" target="_blank" class="apply-btn">View Details →</a>
            </div>
            """
        return items

    # Get current time in India
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist).strftime("%d %B %Y, %I:%M %p IST")

    # Fill the template
    final_html = html.replace("{DATE_PLACEHOLDER}", now)
    final_html = final_html.replace("{WB_LIST}", make_list(wb_jobs))
    final_html = final_html.replace("{CENTRAL_LIST}", make_list(central_jobs))

    # Save the file
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(final_html)

if __name__ == "__main__":
    wb, central = fetch_jobs()
    generate_html(wb, central)
    print("Website generated successfully.")
