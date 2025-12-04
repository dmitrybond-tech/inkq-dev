# Artists Catalog Fix - Changelog

## Summary
Fixed the `/en/artists` page to correctly load artists from the backend without 500 errors, and extended the "Style" dropdown to support multi-select via checkboxes, passing selected styles as filters to the backend.

## Changes

### 1. Backend: Fixed Artists Browse Endpoint (`backend/app/routes/artists.py`)

**Issue**: The `list_public_artists` endpoint was not filtering by `onboarding_completed=True`, causing potential 500 errors when trying to serialize artists without complete profiles.

**Changes**:
- Added `User.onboarding_completed == True` filter to `list_public_artists` endpoint (line ~417)
- Added `User.onboarding_completed == True` filter to `get_public_artist_filters` endpoint (line ~475)
- Added comprehensive error handling with try/except blocks and proper HTTPException responses
- The styles filter already supported comma-separated values (no changes needed)
- Improved error messages to be more user-friendly

**Key modifications**:
```python
# Added onboarding filter
.filter(
    User.account_type == AccountType.ARTIST,
    User.onboarding_completed == True,
)

# Added error handling
try:
    # ... query logic ...
except Exception as e:
    logger.exception("Error in list_public_artists: %s", e)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to load artists: {str(e)}",
    )
```

### 2. Backend: Database Seeding (`backend/app/scripts/init_db.py`)

**Issue**: No demo data existed to test the catalog functionality.

**Changes**:
- Updated `seed_base_data()` function to create a demo artist with:
  - Email: `demo-artist@inkq.test`
  - Username: `demo-artist`
  - Password: `demo123` (properly hashed with bcrypt)
  - `onboarding_completed=True`
  - Styles: `["traditional", "blackwork"]`
  - City: `"Berlin"`
  - Session price: `150`
  - Instagram and Telegram handles
- Made seeding idempotent (checks for existing user before creating)

**Usage**:
```bash
# PowerShell:
cd backend
.\.venv\Scripts\activate
python -m app.scripts.init_db --drop-all --seed
```

### 3. Frontend: Multi-Select Style Dropdown (`src/pages/[lang]/artists/index.astro`)

**Issue**: The style filter used inline checkboxes instead of a proper dropdown.

**Changes**:
- Replaced inline checkbox layout with a dropdown button that:
  - Shows "Any style" when no styles are selected
  - Shows "N styles selected" when one or more styles are selected
  - Opens a dropdown menu with checkboxes when clicked
  - Closes when clicking outside
- Added JavaScript to:
  - Toggle dropdown visibility
  - Update label text based on selected styles
  - Collect selected styles on form submission
  - Pass styles as comma-separated query parameter
- Improved form submission to properly serialize selected styles

**Key UI changes**:
- Dropdown trigger button with dynamic label
- Dropdown menu with checkboxes (hidden by default, shown on click)
- Proper ARIA attributes for accessibility
- Click-outside-to-close functionality

### 4. Frontend: Internationalization (`src/i18n/en.ts`, `src/i18n/ru.ts`, `src/i18n/types.ts`)

**Changes**:
- Added `anyStyle` label: "Any style" (EN) / "Любой стиль" (RU)
- Added `stylesSelected` label: "{count} style{plural} selected" (EN) / "Выбрано стилей: {count}" (RU)
- Updated TypeScript types to include new catalog translation fields

## Testing Checklist

### Backend
- [x] Endpoint returns 200 with empty list when no artists exist
- [x] Endpoint filters by `onboarding_completed=True`
- [x] Endpoint supports city filter (case-insensitive)
- [x] Endpoint supports multi-style filter (comma-separated)
- [x] Endpoint returns proper error responses (400/500) with clear messages
- [x] Filters endpoint only includes cities from onboarded artists

### Frontend
- [x] Page loads without 500 errors
- [x] Style dropdown shows "Any style" when empty
- [x] Style dropdown shows "N styles selected" when styles are selected
- [x] Dropdown opens/closes correctly
- [x] Checkboxes toggle correctly
- [x] Form submission includes selected styles as comma-separated query param
- [x] "Clear filters" button resets all filters
- [x] "Retry" button preserves current filters
- [x] Error banner displays properly
- [x] Empty state shows when no artists match filters

### Database
- [x] Seed script creates demo artist with onboarding_completed=True
- [x] Seed script is idempotent (doesn't create duplicates)

## Files Modified

1. `backend/app/routes/artists.py` - Fixed endpoint filters and error handling
2. `backend/app/scripts/init_db.py` - Added demo artist seeding
3. `src/pages/[lang]/artists/index.astro` - Refactored style filter to dropdown
4. `src/i18n/en.ts` - Added style dropdown labels
5. `src/i18n/ru.ts` - Added style dropdown labels (Russian)
6. `src/i18n/types.ts` - Updated TypeScript types

## Acceptance Criteria Status

✅ **AC1**: Visiting `/en/artists` shows artist cards without internal server errors (when at least one artist is seeded)
✅ **AC2**: Endpoint responds with 200 and empty list when no artists exist (no 500, no crash)
✅ **AC3**: Style dropdown opens a list of styles with checkboxes, allows multi-select, and shows dynamic label
✅ **AC4**: Applying filters sends `city` and `styles` query params to backend and shows matching artists
✅ **AC5**: Clearing filters resets to "All cities" + "Any style" and refetches all visible artists
✅ **AC6**: Backend doesn't throw 500 for normal user interactions; frontend shows graceful error banner with working "Retry" button

## Next Steps (Optional Improvements)

- Add pagination UI improvements
- Add loading states during filter application
- Add URL state management for bookmarkable filter combinations
- Add keyboard navigation for dropdown
- Add animation/transitions for dropdown open/close

