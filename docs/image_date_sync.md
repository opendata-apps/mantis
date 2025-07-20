# Image Date Synchronization

## Overview

This document describes the image date synchronization feature that ensures image files are moved to the correct date-based folders when the sighting date (`dat_fund_von`) is updated through the admin interface.

## Problem Statement

Previously, when administrators changed the sighting date (`dat_fund_von`) in the all_data view, only the database was updated. The image files remained in their original folders based on the initial sighting date, creating a mismatch between the database records and the file system structure.

## Solution

The system now automatically moves image files to the correct date-based folder when `dat_fund_von` is updated.

### How It Works

1. **Date Change Detection**: When an admin updates `dat_fund_von` through the all_data view, the `update_cell` function detects this change.

2. **Image Relocation**: The `update_report_image_date` function is called to:
   - Find the associated image file
   - Create a new directory structure based on the new date
   - Move the image file to the new location
   - Update the database with the new file path
   - Clean up empty directories

3. **Transaction Safety**: If the image move fails, the database change is rolled back to maintain consistency.

### File Structure

Images are stored in a date-based hierarchy:
```
app/datastore/
├── YYYY/                  # Year from dat_fund_von
│   └── YYYY-MM-DD/        # Full date from dat_fund_von
│       └── {location}-{timestamp}-{userid}.webp
```

### Error Handling

The system handles various error scenarios:
- Missing image files
- Invalid filename formats
- File system permission issues
- No image associated with the report

### Example

If a sighting date is changed from 2024-07-15 to 2024-08-20:
- Old path: `app/datastore/2024/2024-07-15/Berlin-20240715120000-user123.webp`
- New path: `app/datastore/2024/2024-08-20/Berlin-20240820000000-user123.webp`

The filename timestamp is also updated to reflect the new date.

## Technical Details

### Modified Functions

1. **`update_cell` (admin.py:882-982)**
   - Added detection for `dat_fund_von` changes
   - Calls `update_report_image_date` when needed
   - Implements transaction rollback on failure

2. **`update_report_image_date` (admin.py:519-584)**
   - Enhanced error handling
   - Supports both string and datetime inputs
   - Cleans up empty directories
   - Returns detailed status information

### Database Fields

- `TblMeldungen.dat_fund_von`: The sighting date that determines folder structure
- `TblFundorte.ablage`: Stores the relative path to the image file

## Testing

A test suite is provided in `tests/test_image_date_update.py` that verifies:
- Successful image moves when dates change
- Proper handling of reports without images
- Directory cleanup after moves
- Database consistency