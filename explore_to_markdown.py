import os

def sanitize_filename(name):
    return ''.join(c for c in name if c.isalnum() or c in (' ', '_', '-')).rstrip()

def export_to_markdown(data, output_dir="markdown_notes"):
    os.makedirs(output_dir, exist_ok=True)
    filename = sanitize_filename(data['subject'] or 'Untitled')[:50] + ".md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w") as f:
        f.write(f"# {data['subject']}  \n")
        f.write(f"**From**: [[{data['from']}]]  \n")
        f.write(f"**Date**: {data['date']}  \n")
        f.write(f"**Sentiment**: {data['sentiment']}  \n")
        f.write(f"\n## Summary\n{data['summary']}\n")
        f.write(f"\n## Tasks\n")
        for task in data['tasks']:
            f.write(f"- [ ] {task}\n")
        f.write(f"\n---\n\n## Full Email\n\n{data['body']}")

    return filepath
