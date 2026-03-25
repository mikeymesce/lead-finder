# Google Sheets Setup

This lets the scraper automatically log leads to a Google Sheet you can check from anywhere.

## Step-by-Step

### 1. Create a Google Cloud Project (free)
1. Go to https://console.cloud.google.com
2. Click "Select a project" at the top → "New Project"
3. Name it "Lead Finder" → Create

### 2. Enable Google Sheets API
1. In your project, go to "APIs & Services" → "Library"
2. Search for "Google Sheets API"
3. Click it → "Enable"

### 3. Create a Service Account
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Name it "lead-finder" → Create → Done
4. Click on the service account you just created
5. Go to "Keys" tab → "Add Key" → "Create new key" → JSON → Create
6. A `.json` file will download. **Move it to this project folder** and rename it `service-account.json`

### 4. Create Your Google Sheet
1. Go to https://sheets.google.com
2. Create a new blank spreadsheet
3. Name it "Lead Finder"
4. In row 1, add these headers:
   - A1: Date
   - B1: Company
   - C1: Industry
   - D1: Location
   - E1: Employees
   - F1: Asking Price
   - G1: Revenue
   - H1: Cash Flow / SDE
   - I1: Distress Signals
   - J1: Source
   - K1: URL
   - L1: Notes

### 5. Share the Sheet with Your Service Account
1. Open `service-account.json` and find the `client_email` field
2. In your Google Sheet, click "Share"
3. Paste the service account email and give it "Editor" access
4. Click "Send" (ignore the warning about sending outside your org)

### 6. Add the Sheet ID to Your .env File
1. Copy your Google Sheet URL — the long string between `/d/` and `/edit` is the Sheet ID
   - Example: `https://docs.google.com/spreadsheets/d/ABC123XYZ/edit` → ID is `ABC123XYZ`
2. Create a `.env` file in this project folder:
   ```
   GOOGLE_SHEET_ID=your-sheet-id-here
   ```

### 7. Test It
```bash
python3 main.py
```
Check your Google Sheet — you should see new rows!

## Troubleshooting

- **"Spreadsheet not found"** — Make sure you shared the sheet with the service account email
- **"credentials.json not found"** — Make sure `service-account.json` is in the project root
- **No data appearing** — Check `leads.csv` to see if the scraper found anything. If CSV has data but Sheet doesn't, it's an auth issue
