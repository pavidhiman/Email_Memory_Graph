import os
import json
import datetime
from git import Repo
from openai import OpenAI
from gmail_fetcher import authenticate_gmail, get_emails

# ---------------------------
# SETUP
# ---------------------------
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not set as environment variable.")
client = OpenAI(api_key=api_key)

# ---------------------------
# GPT ANALYSIS
# ---------------------------
def analyze_email(email_text):
    prompt = f"""
You're analyzing an email.

Return a JSON object like this:

{{
  "summary": "...",
  "sentiment": "Positive" | "Negative" | "Neutral",
  "tasks": ["..."],
  "mentions": ["email/name"],
  "referrals": ["email/name"],
  "status": "Interested" | "Rejected" | "Pending",
  "topics": ["internship", "drones", "AI", "agentic AI", "university", "humanoids", "waterloo", "software", "AI", "autonomous"]
}}

Email:
\"\"\"
{email_text}
\"\"\"
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You analyze internship emails and extract insights."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        result = response.choices[0].message.content
        return json.loads(result)
    except Exception as e:
        print("OpenAI error:", e)
        return {
            "summary": email_text[:100] + "...",
            "sentiment": "Neutral",
            "tasks": [],
            "mentions": [],
            "referrals": [],
            "status": "Pending",
            "topics": []
        }

# ---------------------------
# EXPORT TO OBSIDIAN MARKDOWN
# ---------------------------
def export_to_markdown(email, analysis, output_dir="notes_repo/notes"):
    os.makedirs(output_dir, exist_ok=True)
    subject = email.get("subject", "No Subject")
    filename = f"{email['date'].replace(':', '-')}_{email['from'].replace('@', '_').replace('.', '_')}.md"
    path = os.path.join(output_dir, filename)

    with open(path, "w") as f:
        f.write(f"# {subject}\n")
        f.write(f"**From**: [[{email['from']}]]\n")
        f.write(f"**Date**: {email['date']}\n")
        f.write(f"**Sentiment**: {analysis['sentiment']}\n")
        f.write(f"**Status**: {analysis['status']}\n\n")
        f.write(f"## Summary\n{analysis['summary']}\n\n")
        f.write("## Tasks\n")
        for task in analysis["tasks"]:
            f.write(f"- [ ] {task}\n")
        f.write(f"\n## Topics\n{', '.join(analysis['topics'])}\n\n")
        f.write("---\n")
        f.write(f"\n## Full Email\n{email['body']}")
    
    print(f"✅ Saved: {path}")
    return path

# ---------------------------
# PUSH TO GITHUB
# ---------------------------
def push_to_github(path, commit_message="Add email note"):
    try:
        repo = Repo("notes_repo")
        repo.index.add([path])
        repo.index.commit(commit_message)
        origin = repo.remote(name="origin")
        origin.push()
        print(f"🚀 Pushed to GitHub: {path}")
    except Exception as e:
        print(f"⚠️ Git push failed: {e}")

# ---------------------------
# MAIN
# ---------------------------
if __name__ == "__main__":
    service = authenticate_gmail()
    emails = get_emails(service, max_results=100)

    for email in emails:
        body = email.get("body", "")
        email["date"] = email.get("date", str(datetime.date.today()))
        analysis = analyze_email(body)
        note_path = export_to_markdown(email, analysis)
        push_to_github(note_path)

    print("\n✅ All emails processed and pushed to GitHub.")
    print("🧠 Open `notes_repo/notes/` in Obsidian and click Graph View to explore.")
