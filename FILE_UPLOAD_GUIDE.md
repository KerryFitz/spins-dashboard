# File Upload Feature Guide

## Overview

The dashboard now includes a built-in file upload feature, allowing you to load new weekly SPINS data directly through the web interface without using command line scripts.

## How to Upload New Data

### Step 1: Access the Upload Panel

1. Open the dashboard at `http://localhost:8501`
2. In the **sidebar**, locate the **"📁 Upload New Data Files"** section
3. Click to expand it

### Step 2: Select Your Files

You can upload one or both files:

- **Brand & Retailers File**: Your SPINS brand and retailers Excel file
- **Trend Data File**: Your SPINS Humble trended sales Excel file

Click "Browse files" or drag and drop your Excel files into the upload areas.

### Step 3: Load the Data

1. Once you've selected your file(s), click the **"Load Files"** button
2. The dashboard will:
   - Load the new data
   - Clear the cache
   - Refresh automatically
3. You'll see a success message: "✓ Brand data loaded" or "✓ Trend data loaded"

### Step 4: Verify the New Data

- Check the **time period filter** - you should see new dates
- Review the **Executive Overview** to confirm the data looks correct
- The dashboard will show "📊 Using uploaded data" to confirm you're viewing the uploaded files

## Resetting to Default Data

If you want to go back to the original data files:

1. Click the **"Reset to Default"** button in the upload panel
2. The dashboard will reload the original data files from the directory
3. You'll see "📂 Using default data files"

## Tips

### File Format Requirements

- Files must be Excel format (`.xlsx`)
- Files must have a "Raw" sheet with the expected data structure
- Column names should match the standard SPINS format

### What Gets Uploaded

- **Brand File** should contain: Multiple brands, retailers, time periods, and 50+ metrics
- **Trend File** should contain: HUMBLE time series data with rolling 12-week periods

### When to Upload

- **Every Monday**: When you receive new weekly SPINS data
- **Mid-month**: For any data corrections or updates
- **Any time**: You want to analyze different data sets or time ranges

### Troubleshooting

**"Error loading data"**
- Verify the file is a valid Excel file
- Check that it has a "Raw" sheet
- Ensure column names match the expected format

**Dashboard not refreshing**
- Click "Load Files" again
- Try the "Reset to Default" button first, then re-upload
- Refresh your browser page (F5 or Cmd+R)

**Uploaded data not showing**
- Check the indicator at the bottom of the upload panel
- Verify you clicked "Load Files" (not just uploaded the files)
- Check that the time period filter includes your new data dates

## Comparison: Upload vs Command Line

### Built-in Upload (New Way) ✓
- **Pros:**
  - No command line needed
  - User-friendly interface
  - Instant feedback
  - Easy to reset
  - Works from anywhere (if dashboard is shared on network)

- **Cons:**
  - Data not permanently saved to disk
  - Lost when dashboard restarts (unless you save files to directory)

### Command Line Script (Old Way)
- **Pros:**
  - Permanently saves files
  - Archives old data
  - Better for automated workflows

- **Cons:**
  - Requires terminal access
  - Less user-friendly
  - Need to remember commands

## Best Practice Workflow

### For Quick Analysis (Use Upload Feature)
1. Receive new SPINS data via email
2. Download to your computer
3. Open dashboard at http://localhost:8501
4. Upload files through the interface
5. Analyze immediately

### For Permanent Updates (Use Both)
1. Receive new SPINS data
2. First, upload through dashboard to analyze immediately
3. Then, run the command line script to archive and permanently save:
   ```bash
   python3 update_data.py --brand-file "path/to/file.xlsx" --trend-file "path/to/file.xlsx"
   ```
4. Reset dashboard to default to use the permanently saved files

## Examples

### Weekly Marketing Review
```
Monday morning:
1. Download new SPINS data from email
2. Open dashboard
3. Expand "Upload New Data Files"
4. Upload both files
5. Click "Load Files"
6. Navigate to "Executive Overview"
7. Check YoY growth and key metrics
8. Share findings in team meeting
```

### Comparing Different Periods
```
Want to compare this week vs last week?
1. Start with default data (last week)
2. Take screenshots of key metrics
3. Upload new data (this week)
4. Compare metrics side-by-side
5. Reset to default when done
```

### Testing New Data
```
Not sure if the new data is correct?
1. Keep default data loaded
2. Upload new data to test
3. Review for any anomalies
4. If good, use command line to make it permanent
5. If bad, just click "Reset to Default"
```

## Security Note

Uploaded files are processed in memory and not permanently written to disk by the upload feature. For permanent storage, use the command line update script.

## Support

For issues with:
- **Upload feature not working**: Refresh the browser or restart dashboard
- **Wrong data loading**: Check file format and structure
- **Performance issues**: Use command line for very large files (>50MB)

---

**Quick Reference:**
- Upload Panel: Sidebar → "📁 Upload New Data Files"
- Supported Format: Excel (.xlsx)
- Required Sheet: "Raw"
- Reset Option: "Reset to Default" button
- Status Indicator: Bottom of upload panel
