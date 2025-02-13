# GrowLog Scraper

This script extracts grow logs from the GrowWithJane website and generates a PDF report.

## Prerequisites

Before installing and running the script, make sure you have:

- **Python 3.x** installed
- **Google Chrome** installed
- **ChromeDriver** matching your browser version ([download here](https://sites.google.com/chromium.org/driver/))
- A valid internet connection

Verify that `chromedriver` is installed by running:
```bash
which chromedriver  # (or "where chromedriver" on Windows)
```
If nothing appears, add `chromedriver` to your PATH.

## Installation

### 1. Clone the repository
```bash
git clone <repository_url>
cd <repository_name>
```

### 2. Create a virtual environment
**On macOS and Linux:**
```bash
python3 -m venv myenv
source myenv/bin/activate
```
**On Windows:**
```bash
python -m venv myenv
myenv\Scripts\activate
```

### 3. Install dependencies
Ensure `requirements.txt` is present in the cloned folder.
```bash
pip install -r requirements.txt
```

## Configuration

### 1. Set the GrowLog URL
Copy the `.env.example` file and rename it to `.env`:
```bash
cp .env.example .env
```

Open `.env` and update the `GROWLOG_URL` variable with your GrowLog URL:
```plaintext
GROWLOG_URL=https://growithjane.com/growlog/growlog-example/
```

## Usage

Run the script with the following command:
```bash
python main.py
```

To enable verbose mode (detailed logs output):
```bash
python main.py -v
```

Once execution is complete, the PDF file will be generated in the current directory as `<grow_log_name>.pdf`.

## Deactivating the Virtual Environment

When you are done, you can exit the virtual environment with:
```bash
deactivate
```

## Troubleshooting

### Error: `selenium.common.exceptions.WebDriverException: Message: 'chromedriver' executable needs to be in PATH`

Solution: Ensure `chromedriver` is installed and accessible via:
```bash
which chromedriver  # (or "where chromedriver" on Windows)
```
If not, download it and add its path to your `PATH` environment variable.

### Error: `ModuleNotFoundError: No module named 'dotenv'`

Solution: Ensure all dependencies are installed by running:
```bash
pip install -r requirements.txt
```
