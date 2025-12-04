# Changelog: Astro Frontmatter Syntax Fix

## Changes Summary

### 1. Fixed duplicate frontmatter markers in artist dashboard
   - **File:** `src/pages/[lang]/dashboard/artist/index.astro`
   - **Issue:** Two consecutive `---` markers at the start of the file caused "Unexpected 'return'" compilation error
   - **Fix:** Removed duplicate frontmatter marker; consolidated all imports, `getStaticPaths()`, and variable declarations into a single frontmatter block

### 2. Verified other dashboard pages (no changes needed)
   - `src/pages/[lang]/dashboard/studio/index.astro` - Already correct
   - `src/pages/[lang]/dashboard/model/index.astro` - Already correct

## Files Modified

1. `src/pages/[lang]/dashboard/artist/index.astro` - Removed duplicate frontmatter marker on line 2

## Impact

- ✅ Resolves compilation error preventing dashboard navigation for studio and artist users
- ✅ No changes to business logic, routing, or component behavior
- ✅ All imports, variables, and i18n usage preserved

