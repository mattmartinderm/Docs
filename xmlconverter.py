import time
import requests
import xml.etree.ElementTree as ET
from xml.dom.minidom import Document
import re

FEED_URL = "https://recruitingbypaycor.com/career/CareerAtomFeed.action?clientId=8a7883c681b199c90181b5a0c172022e"
OUTPUT_FILE = "paycor_full_feed.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_feed():
    for attempt in range(1, 6):
        try:
            r = requests.get(FEED_URL, headers=HEADERS, timeout=60)

            if r.status_code == 504:
                print(f"504 timeout. Retry {attempt}/5...")
                time.sleep(5)
                continue

            r.raise_for_status()
            return r.content

        except requests.RequestException as e:
            print(f"Attempt {attempt}/5 failed: {e}")
            time.sleep(5)

    raise Exception("Unable to load feed.")

def clean_tag(tag):
    # Removes XML namespace
    tag = re.sub(r"\{.*?\}", "", tag)

    # Clean invalid chars
    tag = re.sub(r"[^a-zA-Z0-9_]", "_", tag)

    return tag.lower()

feed_content = fetch_feed()

root = ET.fromstring(feed_content)

doc = Document()
jobs_el = doc.createElement("jobs")
doc.appendChild(jobs_el)

entries = [el for el in root.iter() if el.tag.endswith("entry")]

for entry in entries:

    job_el = doc.createElement("job")
    jobs_el.appendChild(job_el)

    seen_tags = set()

    for child in entry.iter():

        tag_name = clean_tag(child.tag)

        if tag_name == "entry":
            continue

        if tag_name in seen_tags:
            continue

        seen_tags.add(tag_name)

        text_value = (child.text or "").strip()

        # Handle links specially
        if tag_name == "link":
            text_value = child.attrib.get("href", "")

        field_el = doc.createElement(tag_name)

        # Use CDATA for long/html fields
        if any(x in tag_name for x in ["description", "content", "summary"]):
            field_el.appendChild(doc.createCDATASection(text_value))
        else:
            field_el.appendChild(doc.createTextNode(text_value))

        job_el.appendChild(field_el)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(
        doc.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
    )

print(f"Created {OUTPUT_FILE}")
print(f"Jobs found: {len(entries)}")
