# Dynamic Studio / Model Pages by Slug - Changelog

## Overview
This changelog documents the implementation of dynamic Studio and Model public pages that load real data from the database using slug-based routing, replacing placeholder/mock data.

## Changes Summary

### Backend Changes

#### 1. Model Public Endpoint (`backend/app/routes/models.py`)
- **Updated endpoint**: Changed from `GET /api/v1/public/models/{username}` to `GET /api/v1/public/models/{slug}`
- **Added slug-based lookup**: Endpoint now supports lookup by `Model.slug` first, with fallback to `User.username` for backward compatibility
- **Added onboarding check**: Only returns models where `User.onboarding_completed == True`
- **Added import**: Added `or_` from `sqlalchemy` for query filtering
- **Auto-populate slug**: If model exists but slug is missing, automatically sets it from username

#### 2. Studio Public Endpoint (`backend/app/routes/studios.py`)
- **Added onboarding check**: Public studio endpoint now only returns studios where `Studio.onboarding_completed == True`
- **Existing functionality preserved**: Studio endpoint already supported slug lookup (username first, then slug fallback)
- **Consistent behavior**: Now matches the pattern used in Artist endpoint for public visibility

### Frontend Changes

#### 3. Studio Public Page (`src/pages/[lang]/studios/[username].astro`)
- **Removed stub data**: Replaced hardcoded `studioData` object with real API call
- **Added API integration**: Fetches studio data from `GET /api/v1/public/studios/{slug}`
- **Implemented full UI**: 
  - Banner and avatar display
  - Studio name, city, address, and session price label
  - Social media links (Instagram, Telegram, VK)
  - About section
  - Portfolio gallery with lightbox
  - Team members section showing resident artists
  - Aggregated styles display
- **Error handling**: Proper 404 and error state handling with i18n messages
- **Dynamic routing**: Changed `getStaticPaths` to use placeholder for dynamic slug resolution at runtime

#### 4. Model Public Page (`src/pages/[lang]/models/[username].astro`)
- **Updated API call**: Changed to use slug parameter instead of username (endpoint already updated)
- **Improved error handling**: Enhanced error messages with proper i18n support
- **Parameter naming**: Updated variable name from `usernameParam` to `slugParam` for clarity (route file still uses `[username].astro` due to Astro routing)

#### 5. Internationalization (`src/i18n/`)
- **Added error messages** to `ProfileTranslations` type:
  - `studioNotFound`: "Studio not found" / "Студия не найдена"
  - `modelNotFound`: "Model not found" / "Модель не найдена"
  - `errorLoadingStudio`: "Error loading studio" / "Ошибка загрузки студии"
  - `errorLoadingModel`: "Error loading model" / "Ошибка загрузки модели"
- **Updated translations**: Added corresponding entries in both `en.ts` and `ru.ts`

### Database Schema

#### 6. Slug Fields Verification
- **Studio model**: `slug` field already exists with unique index (`backend/app/models/studio.py:37`)
- **Model model**: `slug` field already exists with unique index (`backend/app/models/model.py:33`)
- **Init script**: Slug fields are automatically created when `Base.metadata.create_all()` runs in `init_db.py`
- **No migration needed**: Slug fields are already defined in SQLAlchemy models and will be created automatically

## API Endpoints

### Public Studio Endpoint
```
GET /api/v1/public/studios/{studio_slug}
```
- **Response**: `PublicStudioResponse`
- **Visibility**: Only studios with `onboarding_completed == True`
- **Lookup**: Tries `User.username` first, then `Studio.slug`

### Public Model Endpoint  
```
GET /api/v1/public/models/{slug}
```
- **Response**: `PublicModelResponse`
- **Visibility**: Only models with `User.onboarding_completed == True`
- **Lookup**: Tries `Model.slug` first, then `User.username` for backward compatibility

## File Changes

### Modified Files
1. `backend/app/routes/models.py` - Updated public endpoint to use slug and check onboarding
2. `backend/app/routes/studios.py` - Added onboarding check to public endpoint
3. `src/pages/[lang]/studios/[username].astro` - Replaced stub data with real API integration
4. `src/pages/[lang]/models/[username].astro` - Updated to use slug parameter
5. `src/i18n/types.ts` - Added error message keys to ProfileTranslations
6. `src/i18n/en.ts` - Added English error messages
7. `src/i18n/ru.ts` - Added Russian error messages

### Unchanged Files (Used as Reference)
- `src/pages/[lang]/artists/[username].astro` - Reference implementation (still uses mock data per requirements)

## Testing Notes

### Manual Verification Steps

1. **Backend Endpoints**:
   ```powershell
   # Test studio endpoint
   Invoke-WebRequest -Uri "http://localhost:8000/api/v1/public/studios/{studio-slug}" | Select-Object -ExpandProperty Content
   
   # Test model endpoint
   Invoke-WebRequest -Uri "http://localhost:8000/api/v1/public/models/{model-slug}" | Select-Object -ExpandProperty Content
   ```

2. **Frontend Pages**:
   - Navigate to `http://localhost:4321/en/studios/{studio-slug}`
   - Navigate to `http://localhost:4321/ru/studios/{studio-slug}`
   - Navigate to `http://localhost:4321/en/models/{model-slug}`
   - Navigate to `http://localhost:4321/ru/models/{model-slug}`

3. **Verify**:
   - Real data loads (not placeholder/mock data)
   - 404 page shows for non-existent slugs
   - Error messages are properly translated
   - Language switching works correctly
   - Gallery and team sections render properly

## Breaking Changes
None. All changes are backward compatible:
- Model endpoint still accepts username as fallback
- Studio endpoint already supported both username and slug
- Frontend route files keep the same structure (`[username].astro`)

## Dependencies
No new dependencies added. All changes use existing packages.

## Migration Notes
- Slug fields already exist in database models
- Existing Studio/Model records will work (slug auto-populated from username if missing)
- Public pages only show entities with `onboarding_completed == True`

