import json
import os
from collections import defaultdict
import itertools

EMAIL_DIR = "../emails"
OUTPUT_PATH = "../data/graph.json"

def read_emails(email_dir):
    emails = []
    for file in os.listdir(email_dir):
        if file.endswith(".json"):
            with open(os.path.join(email_dir, file), "r", encoding="utf-8") as f:
                data = json.load(f)
                emails.append(data)
    return emails

def build_graph_data(emails):
    nodes = {}
    links = []
    id_counter = 1

    for email in emails:
        people = set([email.get("from", "")])
        people.update([e.strip() for e in email.get("to", "").split(",")])
        people.update(email.get("mentions", []))
        people.update(email.get("referrals", []))

        topics = email.get("topics", [])
        status = email.get("status", "Pending")

        for person in people:
            if person not in nodes:
                nodes[person] = {
                    "id": person,
                    "group": topics[0] if topics else "other",
                    "topics": topics,
                    "status": status
                }

        for p1, p2 in itertools.combinations(people, 2):
            links.append({
                "source": p1,
                "target": p2,
                "topics": topics
            })

    return {
        "nodes": list(nodes.values()),
        "links": links
    }

if __name__ == "__main__":
    emails = read_emails(EMAIL_DIR)
    graph_data = build_graph_data(emails)
    os.makedirs("../data", exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(graph_data, f, indent=2)
    print(f"Graph JSON saved to {OUTPUT_PATH}")
