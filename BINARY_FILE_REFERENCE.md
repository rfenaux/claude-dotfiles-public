# Binary File Reference Guide

Complete reference for handling binary files in Claude Code. When encountering any binary file, consult this guide for the correct approach.

---

## Quick Decision Tree

```
Is it a binary file?
├── PDF, Images (.png, .jpg, .gif, .webp) → Use Read tool (built-in support)
├── Microsoft Office (.xlsx, .docx, .pptx) → Use Python
├── Apple iWork (.numbers, .pages, .keynote) → Use Python or convert
├── Audio/Video → Use Python (whisper for transcription)
├── Archives (.zip, .tar) → Use Python
└── Other binary → Check below or use Python
```

---

## Microsoft Office Formats

### Excel (.xlsx, .xls)

```python
import pandas as pd

# Read entire file
df = pd.read_excel("file.xlsx")

# Read specific sheet
df = pd.read_excel("file.xlsx", sheet_name="Sheet1")

# Read all sheets
sheets = pd.read_excel("file.xlsx", sheet_name=None)  # Returns dict

# Preview
print(df.head())
print(df.info())
print(df.columns.tolist())
```

**Alternative with openpyxl (more control):**
```python
from openpyxl import load_workbook

wb = load_workbook("file.xlsx")
print(wb.sheetnames)

ws = wb.active
for row in ws.iter_rows(max_row=10, values_only=True):
    print(row)
```

### Word (.docx)

```python
from docx import Document

doc = Document("file.docx")

# All paragraphs
for para in doc.paragraphs:
    print(para.text)

# All tables
for table in doc.tables:
    for row in table.rows:
        for cell in row.cells:
            print(cell.text, end="\t")
        print()

# Full text extraction
full_text = "\n".join([para.text for para in doc.paragraphs])
```

### PowerPoint (.pptx)

```python
from pptx import Presentation

prs = Presentation("file.pptx")

# Iterate slides
for i, slide in enumerate(prs.slides, 1):
    print(f"\n--- Slide {i} ---")
    for shape in slide.shapes:
        if hasattr(shape, "text"):
            print(shape.text)

# Extract all text
all_text = []
for slide in prs.slides:
    for shape in slide.shapes:
        if hasattr(shape, "text"):
            all_text.append(shape.text)
```

### Legacy Office (.doc, .ppt, .xls - old format)

```python
# For .doc (not .docx)
import subprocess
# Use antiword or textract
result = subprocess.run(["antiword", "file.doc"], capture_output=True, text=True)
print(result.stdout)

# Or use textract (handles many formats)
import textract
text = textract.process("file.doc").decode("utf-8")
```

---

## Apple iWork Formats

### Numbers (.numbers)

```python
from numbers_parser import Document

doc = Document("file.numbers")
sheets = doc.sheets
for sheet in sheets:
    for table in sheet.tables:
        print(f"Table: {table.name}")
        for row in table.iter_rows():
            print([cell.value for cell in row])
```

**Alternative: Export to CSV first**
```bash
# On macOS, can use AppleScript or open in Numbers and export
```

### Pages (.pages) / Keynote (.keynote)

These are actually ZIP archives containing XML:
```python
import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile("file.pages", "r") as z:
    # List contents
    print(z.namelist())
    # Main content is usually in Index/Document.iwa (proprietary)
```

**Best approach:** Export to PDF/DOCX from the app, or use a conversion service.

---

## Audio & Video

### Transcription with Whisper

```python
import whisper

model = whisper.load_model("base")  # or "small", "medium", "large"
result = model.transcribe("audio.mp3")
print(result["text"])

# With timestamps
for segment in result["segments"]:
    print(f"[{segment['start']:.2f}s] {segment['text']}")
```

### Using whisper-cpp (faster, local)

```bash
whisper-cpp -m /path/to/model.bin -f audio.wav
```

### Audio metadata

```python
from mutagen import File

audio = File("song.mp3")
print(audio.tags)  # ID3 tags
print(audio.info.length)  # Duration in seconds
```

### Video frame extraction

```python
import cv2

cap = cv2.VideoCapture("video.mp4")
fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# Extract frame
cap.set(cv2.CAP_PROP_POS_FRAMES, 100)  # Go to frame 100
ret, frame = cap.read()
cv2.imwrite("frame.jpg", frame)
cap.release()
```

---

## Email Formats

### EML Files

```python
import email
from email import policy

with open("message.eml", "rb") as f:
    msg = email.message_from_binary_file(f, policy=policy.default)

print(f"From: {msg['from']}")
print(f"To: {msg['to']}")
print(f"Subject: {msg['subject']}")
print(f"Date: {msg['date']}")

# Body
if msg.is_multipart():
    for part in msg.walk():
        if part.get_content_type() == "text/plain":
            print(part.get_content())
else:
    print(msg.get_content())
```

### MSG Files (Outlook)

```python
import extract_msg

msg = extract_msg.Message("email.msg")
print(f"From: {msg.sender}")
print(f"To: {msg.to}")
print(f"Subject: {msg.subject}")
print(f"Body: {msg.body}")

# Attachments
for attachment in msg.attachments:
    print(f"Attachment: {attachment.longFilename}")
    attachment.save()
```

### MBOX (mailbox export)

```python
import mailbox

mbox = mailbox.mbox("archive.mbox")
for message in mbox:
    print(f"Subject: {message['subject']}")
```

---

## Calendar & Contacts

### ICS (Calendar)

```python
from icalendar import Calendar

with open("calendar.ics", "rb") as f:
    cal = Calendar.from_ical(f.read())

for event in cal.walk("VEVENT"):
    print(f"Event: {event.get('SUMMARY')}")
    print(f"Start: {event.get('DTSTART').dt}")
    print(f"End: {event.get('DTEND').dt}")
    print(f"Location: {event.get('LOCATION')}")
    print()
```

### VCF (Contacts)

```python
import vobject

with open("contacts.vcf", "r") as f:
    for vcard in vobject.readComponents(f):
        print(f"Name: {vcard.fn.value}")
        if hasattr(vcard, "email"):
            print(f"Email: {vcard.email.value}")
        if hasattr(vcard, "tel"):
            print(f"Phone: {vcard.tel.value}")
```

---

## Archives

### ZIP

```python
import zipfile

# List contents
with zipfile.ZipFile("archive.zip", "r") as z:
    print(z.namelist())

# Extract all
with zipfile.ZipFile("archive.zip", "r") as z:
    z.extractall("output_folder")

# Read file without extracting
with zipfile.ZipFile("archive.zip", "r") as z:
    content = z.read("file_inside.txt").decode("utf-8")
```

### TAR / TAR.GZ

```python
import tarfile

# List contents
with tarfile.open("archive.tar.gz", "r:gz") as tar:
    print(tar.getnames())

# Extract all
with tarfile.open("archive.tar.gz", "r:gz") as tar:
    tar.extractall("output_folder")

# Read single file
with tarfile.open("archive.tar.gz", "r:gz") as tar:
    f = tar.extractfile("file_inside.txt")
    content = f.read().decode("utf-8")
```

---

## Data Formats

### Parquet

```python
import pandas as pd

df = pd.read_parquet("data.parquet")

# Or with pyarrow directly
import pyarrow.parquet as pq
table = pq.read_table("data.parquet")
df = table.to_pandas()
```

### SQLite / Database

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("database.sqlite")

# List tables
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
print(tables)

# Query
df = pd.read_sql("SELECT * FROM table_name LIMIT 100", conn)
conn.close()
```

### HDF5

```python
import h5py

with h5py.File("data.h5", "r") as f:
    print(list(f.keys()))  # List datasets
    data = f["dataset_name"][:]  # Read dataset

# Or with pandas
import pandas as pd
df = pd.read_hdf("data.h5", key="dataset_name")
```

### Pickle

```python
import pickle

with open("data.pkl", "rb") as f:
    obj = pickle.load(f)
```

**Warning:** Only unpickle files from trusted sources.

### AVRO

```python
from fastavro import reader

with open("data.avro", "rb") as f:
    avro_reader = reader(f)
    for record in avro_reader:
        print(record)
```

### Protocol Buffers

```python
# Requires generated Python classes from .proto file
from your_proto_pb2 import YourMessage

with open("data.pb", "rb") as f:
    msg = YourMessage()
    msg.ParseFromString(f.read())
```

---

## OpenDocument Formats

### ODT (OpenDocument Text)

```python
from odf.opendocument import load
from odf.text import P

doc = load("document.odt")
paragraphs = doc.getElementsByType(P)
for para in paragraphs:
    print(para.textContent)
```

### ODS (OpenDocument Spreadsheet)

```python
import pandas as pd

df = pd.read_excel("spreadsheet.ods", engine="odf")
```

---

## Installing Required Libraries

```bash
# Core Office formats
pip install pandas openpyxl python-docx python-pptx

# Apple formats
pip install numbers-parser

# Audio/Video
pip install openai-whisper mutagen opencv-python

# Email
pip install extract-msg

# Calendar/Contacts
pip install icalendar vobject

# Data formats
pip install pyarrow h5py fastavro

# OpenDocument
pip install odfpy
```

---

## Troubleshooting

### "Module not found"
Install the required library: `pip install <library>`

### Excel file with macros (.xlsm)
```python
df = pd.read_excel("file.xlsm", engine="openpyxl")
```

### Password-protected Office files
```python
# Excel with password
import msoffcrypto
import io

with open("encrypted.xlsx", "rb") as f:
    decrypted = io.BytesIO()
    file = msoffcrypto.OfficeFile(f)
    file.load_key(password="your_password")
    file.decrypt(decrypted)
    df = pd.read_excel(decrypted)
```

### Large files (memory issues)
```python
# Read in chunks
for chunk in pd.read_excel("large.xlsx", chunksize=10000):
    process(chunk)

# Or read specific columns
df = pd.read_excel("file.xlsx", usecols=["A", "B", "C"])
```
