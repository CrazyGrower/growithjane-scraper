# GrowLog Scraper 🌱

A simple tool to extract your grow logs from GrowWithJane and generate a detailed PDF report and video summary.

## 🚀 Features

- Web interface for easy URL input and options
- Automatic extraction of your GrowWithJane journal
- Clean PDF generation with your photos and actions
- Optional video generation summarizing the growth process
- Progress tracking (germination, growth, etc.)
- Complete history of watering and nutrients
- Automatic date and duration formatting

## 📂 Project Structure

```
growithjane-scraper/
├── src/                    # Source code
│   ├── __init__.py        # Package initialization
│   ├── scraper.py         # Web scraping functionality
│   ├── pdf_generator.py   # PDF generation
│   ├── video_generator.py # Video generation
│   ├── web_interface.py   # Web interface
│   └── utils.py           # Utility functions
├── static/                # Static files for web interface
│   └── css/              
│       └── style.css
├── templates/             # HTML templates
│   ├── index.html        # Web interface template
│   └── template.html     # PDF template
├── output/               # Generated files
│   ├── *.pdf            # Generated PDFs
│   ├── planteName/*.     # Image  extract for video
│   └── *.mp4            # Generated videos
├── tests/                # Test files
│   ├── __init__.py
│   ├── test_scraper.py
│   └── test_pdf_generator.py
├── .gitignore           # Git ignore rules
├── LICENSE              # MIT License
├── README.md           # This file
└── requirements.txt    # Python dependencies
```

## 📋 Prerequisites

Before installing the script, make sure you have:

- Python 3.x installed
- Internet access

## 💾 Installation

1. **Clone the repository**
```bash
git clone git@github.com:CrazyGrower/growithjane-scraper.git
or
git clone https://github.com/CrazyGrower/growithjane-scraper.git
cd growithjane-scraper
```

2. **Create a virtual environment**
```bash
# On Linux/macOS
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
playwright install
```

## 🎯 Usage

1. **Start the web server**
```bash
python main.py
```

2. **Access the web interface**
- Open your browser and go to `http://localhost:8000`
- Enter your GrowWithJane URL in the format: `https://growithjane.com/growlog/your-growlog-id`
- Choose your options:
  - Generate video (optional)
  - Verbose mode for detailed logs
- Click "Generate Report"

The PDF and video (if selected) will be generated in the `output` folder.

## 🧪 Running Tests

To run the test suite:
```bash
python -m unittest discover tests
```

## 📸 Output Example

The generated files include:

### PDF Report
- A title page with your grow name
- A progress status (In Progress/Completed)
- Journal entries with:
  - Date and grow day
  - Plant state
  - Actions (watering, nutrients, etc.)
  - Progress photos

### Video Summary (Optional)
- Time-lapse of your grow progress
- Dated photos showing plant development
- Automatic duration adjustment

## 🔧 Troubleshooting

### Error: "No module named 'playwright'"
**Solution:**
```bash
pip install -r requirements.txt
playwright install
```

### Error: "Invalid URL"
**Solution:**
Make sure your URL follows the correct format:
```
https://growithjane.com/growlog/your-unique-identifier/
```

### Error: "Failed to launch browser"
**Solution:**
```bash
playwright install chromium
```

## 📄 License

This project is under MIT License. See the [LICENSE](LICENSE) file for more details.
