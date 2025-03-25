import os
import json
import datetime
from git import Repo
import openai 
from openai import OpenAI
import re 
from collections import defaultdict
import itertools
# import langfuse
# from langfuse import Langfuse

# ---------------------------
# LANGFUSE SETUP (COMMENTED OUT FOR DEMO)
# ---------------------------
# langfuse = Langfuse(
#     public_key="pk-lf-6153689c-353a-432b-87cb-59d0f5794a63",
#     secret_key="sk-lf-e6a780f3-6411-4237-b640-15cb8c9a04ad",
#     host="https://us.cloud.langfuse.com"
# )

#openai key
api_key = os.getenv("OPENAI_API_KEY")

# Check if the key is retrieved properly
if not api_key:
    raise ValueError("API Key is not set. Please set the OPENAI_API_KEY environment variable.")

client = OpenAI(api_key=api_key)
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
# SUMMARIZE EMAIL (Dummy logic, Langfuse removed)
# ---------------------------
def summarize_email(email_text):
    # trace = langfuse.trace(name="summarize_email", metadata={"length": len(email_text)})
    summary = email_text[:100] + "..." if len(email_text) > 100 else email_text
    # trace.complete(response=summary)
    return summary

# ---------------------------
# EXTRACT KEY INFORMATION FROM EMAIL
# ---------------------------
def extract_key_info(email):
    key_info = {}
    key_info["from"] = email.get("from", "unknown")
    key_info["subject"] = email.get("subject", "No Subject")
    key_info["date"] = email.get("date", str(datetime.date.today()))
    key_info["sentiment"] = "Neutral"
    key_info["tasks"] = []
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
    repo_path = "./notes_repo"
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
    for email in emails:
        body = email.get("body", "")
        analysis = analyze_email(body)
        summary = analysis["summary"]

        key_info = extract_key_info(email)
        key_info["sentiment"] = analysis["sentiment"]
        key_info["tasks"] = analysis["tasks"]

        # New metadata
        email["mentions"] = analysis["mentions"]
        email["referrals"] = analysis["referrals"]
        email["status"] = analysis["status"]

        links = []  # future: based on threading / references
        md_content = generate_markdown(email, summary, key_info, links)

        sender_filename = key_info["from"].replace('@', '_').replace('.', '_')
        note_filename = f"{key_info['date']}_{sender_filename}.md"
        note_path = os.path.join("notes_repo", "notes", note_filename)

        note_dir = os.path.dirname(note_path)
        if os.path.exists(note_dir) and not os.path.isdir(note_dir):
            raise RuntimeError(f"'{note_dir}' exists but is not a directory.")
        os.makedirs(note_dir, exist_ok=True)

        with open(note_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"Created note: {note_filename}")
        push_to_github(note_path, commit_message=f"Add note for email from {key_info['from']}")
        

def build_topic_graph(emails):
    person_topics = defaultdict(set)

    # Build topic map
    for email in emails:
        sender = email.get("from", "unknown").lower()
        recipients = email.get("to", "").split(",")
        mentions = email.get("mentions", [])
        referrals = email.get("referrals", [])
        topics = email.get("topics", [])

        people = [sender] + recipients + mentions + referrals
        people = [p.strip().lower() for p in people if p]

        for person in people:
            person_topics[person].update(topics)

    # Build connections based on shared topics
    topic_edges = defaultdict(list)

    for (p1, topics1), (p2, topics2) in itertools.combinations(person_topics.items(), 2):
        shared = set(topics1).intersection(set(topics2))
        if shared:
            topic_edges[p1].append((p2, list(shared)))
            topic_edges[p2].append((p1, list(shared)))

    return topic_edges


# ---------------------------
# GPT SUMMARIZATION + SENTIMENT ANALYSIS
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
  "topics": ["internship", "drones", "AI", "agentic AI", "university", "humanoids", "waterloo", "software", "AI", "autonomous"]  # or any relevant topics
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
        print("GPT Output:\n", result)
        return json.loads(result)

    except Exception as e:
        print("OpenAI error:", e)
        return {
            "summary": email_text[:100] + "...",
            "sentiment": "Neutral",
            "tasks": [],
            "mentions": [],
            "referrals": [],
            "status": "Pending"
        }

# ---------------------------
# SUGGEST CONNECTIONS BASED ON FREQUENT EMAILS
# ---------------------------
def suggest_connections(email_dir):
    emails = read_emails(email_dir)
    sender_count = {}
    for email in emails:
        sender = email.get("from", "unknown")
        sender_count[sender] = sender_count.get(sender, 0) + 1
    suggestions = [sender for sender, count in sender_count.items() if count > 1]
    return suggestions


email_directory = "./emails"  # or your full path
emails = read_emails(email_directory)

connections = {}

for email in emails:
    sender = email.get("from", "unknown")
    mentions = email.get("mentions", [])
    referrals = email.get("referrals", [])

    for person in mentions + referrals:
        if person not in connections:
            connections[person] = set()
        connections[person].add(sender)

# ---------------------------
# MAIN
# ---------------------------
if __name__ == "__main__":
    email_directory = "/Users/pavidhiman/email_brain/emails"  # Absolute path
    process_emails(email_directory)
    
    emails = read_emails(email_directory)
    topic_graph = build_topic_graph(emails)

    # Print connections
    print("\nTopic-based Connections Between People:")
    for person, connections in topic_graph.items():
        for other, shared_topics in connections:
            print(f"{person} ↔ {other}  (topics: {', '.join(shared_topics)})")
    
    connections = suggest_connections(email_directory)
    print("\nSuggested people to connect with based on your email interactions:")
    for conn in connections:
        print(f"- {conn}")

