# Ebay-Checker

**Ebay-Checker** is a Python-based automation service that periodically checks eBay listings, updates product data, and prepares output files for Amazon and a repricer.  
The main orchestration logic is located in `main.py`.

The system runs in a long-lived processing loop and automatically:

- retrieves inventory/input data from Google Sheets,
- checks eBay product pages in parallel,
- writes results into CSV processing files,
- compiles upload files for Amazon and a repricer,
- communicates with a backend server (logs, errors, proxy management),
- schedules repeated execution every cycle.

This documentation is based strictly on the repository’s code structure and the logic in `main.py`.

---

## 📑 Table of Contents

- Project Description  
- Features  
- Module Overview  
- Installation  
- Usage  
- Data Flow  
- Configuration  
- Output Files  
- Notes & Troubleshooting  

---

## 📌 Project Description

The main script (`main.py`) orchestrates a full processing cycle:

1. Connects to a server API and obtains proxies.  
2. Reads product data from Google Sheets (via `RequestToGoogleSheets`).  
3. Performs asynchronous checks of eBay listings (`RequestsToEbay`).  
4. Writes intermediate results to `processing/` CSV files.  
5. Updates the Google Sheet with processed data.  
6. Creates output files for Amazon and a repricer (`uploads/`).  
7. Sends reports, logs, and files to a remote server (`RequestToServer`).  
8. Sleeps for 6 hours and repeats the entire cycle.

All behavior described here is derived strictly from the code visible in this repository.

---

## 🚀 Features (Based on Real Code)

- Asynchronous periodic execution loop
- Integration with Google Sheets:
  - reading main inventory worksheet
  - reading exception worksheets
  - updating processed results back to the sheet
- eBay listing checks via `RequestsToEbay`
- Proxy management:
  - retrieving proxies from a server API
  - fallback proxy list
  - resetting proxy state after execution
- Local file processing:
  - reading `processing/process.csv`
  - handling errors from `processing/errors.csv`
- File generation:
  - `uploads/upload.txt` for Amazon
  - `uploads/uploadReprice.csv` for repricer systems
- Amazon upload via `RequestToAMZ`
- Repricer integration via `RepricerWorker`
- Server reporting:
  - sending reports
  - sending errors
  - uploading files and messages
- Robust error handling:
  - retry loops up to 36 attempts
  - long backoff delays
  - safe cancellation and restart of processing

---

## 🧩 Module Overview

### `main.py` — Orchestration Layer
Contains:
- helper functions:
  - `collect_info_from_sheet()`
  - `cancel_all_tasks()`
  - `average_processing_time_by_link()`
  - `thread_count()`
  - `read_file_of_processing()`
  - `collect_proxies()`
  - `exception_processing()`
- main workflow: `processing()`
- entrypoint: `main()`  
  Runs the process in an endless loop with 6-hour delays.

---

### `moduls.py`
Defines classes used throughout the orchestration:

- **RequestsToEbay** — handles eBay checks  
- **RequestToGoogleSheets** — Google Sheets I/O  
- **RequestToServer** — server API communication  
- **FilesWorker** — reading/writing files under `processing/` and `uploads/`  
- **RequestToAMZ** — uploads output file to Amazon  
- **RepricerWorker** — sends repricer upload file

---

### `main_settings.py`
Provides configuration values:

- Google credentials path  
- Spreadsheet ID  
- Worksheet names  
- Column names  
- Shop configuration  
- Amazon-related IDs/credentials  
- Repricer rules  
- Thread thresholds  

---

### `parser_settings.py`
Includes parser-specific options such as:

- `allow_triggers` — passed to `RequestsToEbay`

---

### Other Files
- `requirements.txt` — dependency list  
- `cookies.json` — likely used for request handling  
- `exception_page.html` — error template  
- `processing/` — processing outputs  
- `uploads/` — final export files  
- `my_proxies.json` — proxy storage file  

---

## 🛠 Installation

1. Clone the repository:
```bash
git clone https://github.com/ltrix07/Ebay-Checker
cd Ebay-Checker
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate.ps1       # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## ▶️ Usage
Run the main program:
```bash
python main.py
```

The script will:
- request proxies
- load Google Sheets inventory
- check eBay items
- write processing results
- regenerate Google Sheets output
- create Amazon & repricer files
- upload files
- send a report to the server

The loop repeats every 6 hours automatically.
There are no command-line arguments; configuration is handled via Python modules (main_settings.py).

## 🔁 Data Flow Diagram
Google Sheets → RequestToGoogleSheets → eBay Checker (RequestsToEbay) → process.csv
        ↓                       ↓                        ↓
  exception sheets         checked items          errors.csv (if any)
        ↓                       ↓                        ↓
 Google Sheets Update ← collect_to_table
        ↓
uploads/upload.txt (Amazon)
uploads/uploadReprice.csv (repricer)
        ↓
RequestToAMZ / RepricerWorker
        ↓
Server reports (RequestToServer)


## ⚙️ Configuration
main_settings.py contains:
- Google APIs configuration
- spreadsheet IDs
- worksheet names
- column mappings
- seller/shop configuration
- repricer rules
- Amazon credentials references

parser_settings.py
- Parser-level flags (e.g., trigger handling)

## 📦 Output Files
| File                        | Description                    |
| --------------------------- | ------------------------------ |
| `processing/process.csv`    | Parsed eBay results            |
| `processing/errors.csv`     | Processing errors              |
| `uploads/upload.txt`        | Amazon upload file             |
| `uploads/uploadReprice.csv` | Repricer output                |
| `my_proxies.json`           | Fetched proxies stored locally |
Additional outputs are sent to the server via RequestToServer.

## 📝 Notes & Troubleshooting
- The project includes long retry loops and sleeps — errors may take time to manifest.
- Check logged exceptions (traceback.print_exc()) and server error messages.
- Ensure directories processing/ and uploads/ exist.
- my_proxies.json is crucial for proxy reset via server API.
- All API interaction logic is inside moduls.py; inspect it for deeper debugging.
