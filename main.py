import os
import json
import datetime
from git import Repo
import langfuse

# ---------------------------
# SET UP LANGFUSE TRACING
# ---------------------------
# Replace these placeholders with your Langfuse credentials from your email.
LANGFUSE_API_KEY = "YOUR_LANGFUSE_API_KEY"
LANGFUSE_PROJECT_ID = "YOUR_PROJECT_ID"

langfuse.initialize(api_key=LANGFUSE_API_KEY, project_id=LANGFUSE_PROJECT_ID)

# ---------------------------
# READ EMAILS FROM DIRECTORY
# ---------------------------
def read_emails(email_dir):
    emails = []
    for file in os.listdir(email_dir):
        if file.endswith(".json"):
            with open(os.path.join(email_dir, file), 'r', encoding='utf-8') as f:
                data = json.load(f)
                emails.append(data)
    return emails

# ---------------------------
# SUMMARIZE EMAIL USING LLM (DUMMY EXAMPLE)
# ---------------------------
def summarize_email(email_text):
    # Wrap the LLM call with Langfuse for observability.
    with langfuse.trace("summarize_email", metadata={"length": len(email_text)}):
        # In a real implementation, replace this with an actual LLM API call (e.g., OpenAI)
        summary = email_text[:100] + "..." if len(email_text) > 100 else email_text
    return summary

# ---------------------------
# EXTRACT KEY INFORMATION FROM EMAIL
# ---------------------------
def extract_key_info(email):
    key_info = {}
    key_info["from"] = email.get("from", "unknown")
    key_info["subject"] = email.get("subject", "No Subject")
    key_info["date"] = email.get("date", str(datetime.date.today()))
    key_info["sentiment"] = "Neutral"  # You can integrate a sentiment analysis package here.
    key_info["tasks"] = []
    # Dummy task extraction: if the word "action" appears, add a task.
    if "action" in email.get("body", "").lower():
        key_info["tasks"].append("Follow up on action")
    return key_info

# ---------------------------
# GENERATE OBSIDIAN-STYLE MARKDOWN NOTE
# ---------------------------
def generate_markdown(email, summary, key_info, links):
    md = f"## Email from {key_info['from']} – {key_info['subject']}\n\n"
    md += f"**From:** {key_info['from']}\n\n"
    md += f"**Date:** {key_info['date']}\n\n"
    md += f"**Subject:** {email.get('subject', 'No Subject')}\n\n"
    md += f"**Summary:**\n{summary}\n\n"
    md += f"**Sentiment:** {key_info['sentiment']}\n\n"
    if key_info["tasks"]:
        md += f"**Tasks:**\n"
        for task in key_info["tasks"]:
            md += f"- [ ] {task}\n"
    if links:
        md += f"\n**Links to Related Emails:**\n"
        for link in links:
            md += f"- {link}\n"
    md += "\n**Tags:** #email #knowledge\n"
    return md

# ---------------------------
# PUSH THE GENERATED NOTE TO GITHUB
# ---------------------------
def push_to_github(note_path, commit_message="Add new email note"):
    repo_path = "./notes_repo"  # This folder must be a Git repository.
    try:
        repo = Repo(repo_path)
        repo.index.add([note_path])
        repo.index.commit(commit_message)
        origin = repo.remote(name='origin')
        origin.push()
        print(f"Pushed {note_path} to GitHub.")
    except Exception as e:
        print(f"Git push failed: {e}")

# ---------------------------
# PROCESS ALL EMAILS
# ---------------------------
def process_emails(email_dir):
    emails = read_emails(email_dir)
    for email in emails:
        body = email.get("body", "")
        summary = summarize_email(body)
        key_info = extract_key_info(email)
        # For linking: placeholder logic; in a real app, you might search previous notes for related topics.
        links = []  
        md_content = generate_markdown(email, summary, key_info, links)
        
        # Create a filename for the note (sanitize the sender string for filename)
        sender_filename = key_info["from"].replace('@', '_').replace('.', '_')
        note_filename = f"{key_info['date']}_{sender_filename}.md"
        note_path = os.path.join("notes_repo", "notes", note_filename)
        
        # Ensure the directory exists.
        os.makedirs(os.path.dirname(note_path), exist_ok=True)
        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"Created note: {note_filename}")
        
        # Push the note to GitHub.
        push_to_github(note_path, commit_message=f"Add note for email from {key_info['from']}")

# ---------------------------
# SUGGEST CONNECTIONS BASED ON FREQUENT EMAILS
# ---------------------------
def suggest_connections(email_dir):
    emails = read_emails(email_dir)
    sender_count = {}
    for email in emails:
        sender = email.get("from", "unknown")
        sender_count[sender] = sender_count.get(sender, 0) + 1
    # Dummy rule: suggest connecting with senders with more than one email.
    suggestions = [sender for sender, count in sender_count.items() if count > 1]
    return suggestions

# ---------------------------
# MAIN EXECUTION
# ---------------------------
if __name__ == "__main__":
    email_directory = "./emails"  # Folder where sample emails are stored.
    process_emails(email_directory)
    connections = suggest_connections(email_directory)
    print("\nSuggested people to connect with based on your email interactions:")
    for conn in connections:
        print(f"- {conn}")
