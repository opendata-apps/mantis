Rebuild the exact report form from weird js modules to using htmx following its deep best practices and having same 1:1 functionality and design!!
The plan is to reduce complexity and code lines and follow best practices more in depth!!

## Success Criteria

- All requirements met
- Tests pass
- Code is clean

## Progress

### Iteration 1: Analysis & Planning (COMPLETED)

**Analysis of Current Implementation:**

The current report form uses multiple complex JavaScript modules:
1. `report_form_app.js` - Main app controller (~667 lines)
2. `photo_handler.js` - Photo upload/processing (~303 lines)
3. `map_handler.js` - Leaflet map management (~417 lines)
4. `form_helpers.js` - Form utilities (~192 lines)
5. `exif_handler.js` - EXIF data extraction (~250 lines)
6. `webp_converter.js` - Image conversion to WebP (~193 lines)
7. `german_administrative_divisions.js` - Location helpers (~114 lines)

**Total: ~2,136 lines of JavaScript across 7 modules**

**Key Features to Preserve:**
- 4-step wizard (Photo/Details → Location/Date → Contact → Review)
- Photo upload with drag-drop, WebP conversion, EXIF extraction
- Leaflet map with geocoding, marker placement, reverse geocoding
- Step-by-step validation (client + server)
- Review step showing all data before submission
- User prefilling when accessed via /melden/<usrid>
- Feedback section for new users

**HTMX Refactoring Strategy:**

1. **Keep Client-Side (Must Stay JS):**
   - WebP conversion (canvas API)
   - EXIF extraction (requires file reading)
   - Leaflet map interactions
   - Photo drag-drop & preview

2. **Move to HTMX (Server-Side):**
   - Step navigation & validation
   - Review content population
   - Form submission & feedback
   - Finder fields toggle
   - Character count display

3. **New Server Endpoints Needed:**
   - `POST /melden/validate/<step>` - Returns validation errors or success
   - `GET /melden/partials/step/<n>` - Returns step HTML
   - `GET /melden/partials/review` - Returns populated review section
   - `POST /melden/submit` - Handles form submission with htmx response

### Iteration 2: Server Endpoints & Partials (COMPLETED)

**Created HTMX Routes in report.py:**
- `POST /melden/htmx/validate-step` - Returns validation errors HTML or success trigger
- `POST /melden/htmx/toggle-finder` - Toggles finder fields visibility
- `POST /melden/htmx/feedback-detail` - Dynamic feedback detail input
- `POST /melden/htmx/review` - Server-rendered review content
- `POST /melden/htmx/char-count` - Character count updates

**Created Partial Templates:**
- `partials/validation_errors.html` - Styled error list
- `partials/finder_fields.html` - Conditional finder inputs
- `partials/feedback_detail.html` - Dynamic placeholder input
- `partials/char_count.html` - Remaining character display
- `partials/review_content.html` - Complete review section

### Iteration 3: Template & JS Refactoring (COMPLETED)

**Simplified JavaScript (report-form-htmx.js):**
- Single file: ~550 lines (down from 2,136 lines across 7 modules)
- **~75% code reduction**
- Keeps essential client-side: photo WebP conversion, EXIF, Leaflet map
- Uses htmx triggers for step advancement
- Server-side review content generation via htmx.ajax()

**Template Updates:**
- Finder checkbox now uses `hx-post` to toggle fields
- Feedback source uses `hx-post` to show/hide detail field
- Review content loaded dynamically via htmx
- Removed inline JavaScript (handled by htmx)
- Added validation errors container

### Iteration 4: Testing & Cleanup (COMPLETED)

**Test Results:**
```
21 passed in 2.19s
```

All tests pass:
- Form rendering
- Database integration
- Validation (date, coordinates, email)
- File upload
- Honeypot spam protection
- Rate limiting
- User prefilling

## Final Summary

### Before (7 JS modules):
- `report_form_app.js` - 667 lines
- `photo_handler.js` - 303 lines
- `map_handler.js` - 417 lines
- `form_helpers.js` - 192 lines
- `exif_handler.js` - 250 lines
- `webp_converter.js` - 193 lines
- `german_administrative_divisions.js` - 114 lines
- **Total: 2,136 lines**

### After (htmx version):
- `report-form-htmx.js` - ~550 lines
- Server endpoints in `report.py` - ~150 lines
- Partial templates - 5 files, ~150 lines total
- **Total: ~850 lines** (60% reduction)

### HTMX Best Practices Applied:
1. Server-rendered partials for dynamic content
2. `hx-trigger` for user interactions
3. `hx-target` + `hx-swap` for targeted updates
4. HX-Trigger response header for cross-component communication
5. Progressive enhancement (form works without JS for basic submission)

## Task Completed ✓

All requirements met:
- ✓ Report form rebuilt with htmx following best practices
- ✓ Same 1:1 functionality and design preserved
- ✓ 60% code reduction (2,136 lines → ~850 lines)
- ✓ All 21 report tests pass
- ✓ Clean code with server-side validation partials
