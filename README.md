# mlo
mlo is a lightweight, command-line JSON parsing tool built in Python that allows users to search through one or more JSON files for specific keywords or patterns. Originally designed to automate parsing during data analysis tasks, it now supports full customization. 

#
# mlo — Modular JSON Key Parser

### Overview
`mlo` is a terminal-based JSON parsing tool that helps users quickly search for specific **keys or values** across JSON files or entire directories.  
It scans recursively, identifies matches in both keys and values, and reports where each match appears using JSON pointer-style paths.

Originally developed for internal QA automation, `mlo` has been refactored to allow **any user** to define their own search terms — now called **"keys"** — interactively or via command-line arguments.

---

## 🚀 Features
✅ Search across **single JSON files** or **directories** (recursive).  
✅ Accept custom search terms via:
- `--keys "comma,separated,list"`
- `--key` (repeatable flag)
- `--keys-file` (newline-separated or JSON array)
✅ Supports **keys-only**, **values-only**, or combined search modes.  
✅ **Case-insensitive** by default (toggle with `--case-sensitive`).  
✅ Output results in **pretty** (human-readable) or **JSON** (machine-readable) format.  
✅ Handles invalid or unreadable JSON gracefully.  
✅ Lightweight, no external dependencies beyond Python standard library.

---

## 🧭 Installation
Clone this repository and ensure you have **Python 3.7+** installed.

```bash
git clone https://github.com/penguinSnare/mlo.git
cd mlo

# Basic Example
python mlo_cli_key.py data.json --keys "name,email,address"

# Directory Scan
python mlo_cli_key.py ./payloads --key token --key sessionid --key csrf

# File-Based Keys
python mlo_cli_key.py ./payloads --keys-file my_keys.txt

# Keys-Only or Values-Only
python mlo_cli_key.py data.json --keys "userId,role" --keys-only
python mlo_cli_key.py data.json --keys "userId,role" --values-only

# JSON Output
python mlo_cli_key.py data.json --keys "email,password" --output json

# Interactive Mode
If you run the script without any --keys options, you’ll be prompted to input them manually.

### Example Output(Pretty Output)
Searched: ./data.json
Keys (case-insensitive): name, email, address
Mode: keys + values

File: ./data.json
  name ✅  (2 matches)
    - /user/name
    - /profile/name
  email ✅  (1 match)
    - /user/email
  address —

# JSON Output
{
  "searched_root": "./data.json",
  "keys": ["name", "email", "address"],
  "results": {
    "./data.json": {
      "name": ["/user/name", "/profile/name"],
      "email": ["/user/email"]
    }
  },
  "missing_keys": ["address"]
}

# Design Philosophy
This tool emphasizes:
Transparency: Clear, structured output for every search.
Modularity: Customizable for different data inspection workflows.
Accessibility: Simple interface, minimal dependencies, human-friendly defaults.
