# Extractor

A web automation tool that uses Selenium to extract data from web applications.

## Prerequisites

- Python 3.7 or higher ([3.12 recommended](https://www.python.org/downloads/release/python-31210/))
- Google Chrome browser
- Internet connection**

## Setup Instructions

### Setting up Python Environment

1. **Install Python** (if not already installed):
   - Download from [python.org](https://www.python.org/downloads/)
   - Ensure you check "Add Python to PATH" during installation

2. **Create a virtual environment** (recommended):
   ```bash
   # Navigate to the project directory
   cd extractor
   
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

### Installing Dependencies

Install all required packages using the [`requirements.txt`](requirements.txt) file:

```bash
pip install -r requirements.txt
```

## ChromeDriver Compatibility

If you encounter an error message like:
```
SessionNotCreatedException: Message: session not created: This version of ChromeDriver only supports Chrome version XX
```

This indicates a version mismatch between ChromeDriver and Google Chrome.

### How to Update Google Chrome

#### On Windows:
1. Click the three dots in the upper right corner of Chrome
2. Go to **Help** > **About Google Chrome**
3. Chrome will automatically check for and install updates
4. Click **Relaunch** once the update is complete

#### On macOS:
1. Open the App Store
2. Click on the **Updates** tab
3. If Chrome update is available, click **Update**

#### On Linux:
```bash
sudo apt update
sudo apt upgrade google-chrome-stable
```

## Usage

Run the main script to start the extraction process:

```bash
python main.py
```

## Running Scripts Individually

To run scripts individually, you need to navigate to the `/scripts` directory using the command line. Follow these steps:

1. Open a terminal or command prompt.
2. Use the `cd` command to navigate to the `/scripts` directory:
   ```bash
   cd scripts
   ```
3. Run the desired script using Python. For example:
   ```bash
   python k36-custom.py
   ```

## Customizing Date Range

To define a custom date range for scripts with the "-custom" suffix (e.g., `k36-custom.py`), you need to modify the `daterange.py` file located in `/scripts/utils`.

1. Open the `daterange.py` file in a text editor.
2. Update the `start_date` and `end_date` variables to your desired date range. For example:
   ```python
   start_date = (2025, 5, 1)  # (Year, Month, Day)
   end_date = (2025, 5, 4)    # (Year, Month, Day)
   ```
3. Save the file.

The updated date range will be used by the scripts in `/scripts` that rely on `daterange.py`.

## Troubleshooting

- **ChromeDriver not found**: Ensure ChromeDriver is installed and in your system PATH
- **Login failures**: Verify your credentials (located under the directory /.key) are correct
- **Element not found errors**: The website structure may have changed, requiring script updates
