# GrowLog Scraper

This script scrapes grow logs from the GrowWithJane website and generates a PDF report.

## Installation

### 1. Clone the Repository
```bash
git clone <repository_url>
cd <repository_name>
```

### 2. Create a Virtual Environment (MacOS)
```bash
python3 -m venv myenv
source myenv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## Configuration

### 1. Environment Variables
Copy the `.env.example` file and rename it to `.env`:
```bash
cp .env.example .env
```
Edit the `.env` file and set the `GROWLOG_URL` variable with the grow log URL:
```plaintext
GROWLOG_URL=https://growithjane.com/growlog/growlog-exemple/
```

## Usage

Run the script with:
```bash
python main.py
```
For verbose output, use:
```bash
python main.py -v
```

## Deactivating the Virtual Environment
To exit the virtual environment, run:
```bash
deactivate
```

## License
This project is licensed under the MIT License.

