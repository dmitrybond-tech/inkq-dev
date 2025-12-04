# Navbar Active & Hover State Enhancement - Changelog

## Summary
Enhanced the navbar tile buttons to have distinct active and inactive states with different hover behaviors. Active tiles are clearly distinguishable with a border and maintain their selected appearance on hover, while inactive tiles have transparent backgrounds that show subtle hover feedback.

## Files Modified

### 1. `src/components/Header.astro`

**Changes:**

1. **Active State Detection (Lines 24-27)**:
   - Changed from `startsWith()` to `includes()` for better subpage support
   - Renamed variables to be more descriptive: `isArtistsSection`, `isStudiosSection`, `isModelsSection`
   - Now correctly detects active state on subpages like `/[lang]/artists/[slug]`, `/[lang]/studios/[slug]`, etc.

2. **Inactive State Styling (Lines 42-46, 52-56, 62-66)**:
   - Set base state to `bg-transparent` for inactive tiles
   - Added `hover:bg-[var(--inkq-bg-subtle)]` for subtle hover feedback on inactive tiles

3. **Active State Styling**:
   - Added persistent background: `bg-[var(--inkq-bg-subtle)]`
   - Added border for visual emphasis: `border border-[var(--inkq-border)]`
   - Added hover enhancement: `hover:shadow-sm` to provide subtle feedback while maintaining selected appearance
   - Border remains consistent on hover: `hover:border-[var(--inkq-border)]`

4. **Transition Enhancement**:
   - Changed from `transition-colors` to `transition-all` to smoothly animate border, background, and shadow changes

5. **Focus States**:
   - Maintained existing `focus-visible` styles that work for both active and inactive states
   - Focus rings remain clearly visible and distinguishable from hover/active states

**Technical Details:**
- **Inactive tiles**: Transparent background → hover shows subtle background
- **Active tiles**: Background + border → hover adds subtle shadow (still clearly selected)
- All changes use existing design tokens (`--inkq-bg-subtle`, `--inkq-border`, `--inkq-fg`)
- No new CSS variables or custom styles introduced

## Visual Behavior

### Inactive Tiles (e.g., "Studios" when on Artists page):
- Base: Transparent background, standard text color
- Hover: Subtle background appears (`bg-[var(--inkq-bg-subtle)]`)
- Focus: Clear ring outline visible

### Active Tiles (e.g., "Artists" when on Artists page):
- Base: Background with border (`bg-[var(--inkq-bg-subtle)]` + `border border-[var(--inkq-border)]`)
- Hover: Maintains background and border, adds subtle shadow (`hover:shadow-sm`)
- Focus: Clear ring outline visible (doesn't conflict with border)

## Impact

**User Experience:**
- Clear visual distinction between current section and other sections
- Hover feedback is obvious but doesn't override the active state appearance
- Keyboard navigation remains fully accessible with visible focus indicators

**Functional Changes:**
- Active state detection now works reliably on subpages (e.g., `/en/artists/some-artist`)
- Improved visual hierarchy makes navigation more intuitive

**No Breaking Changes:**
- All URLs, routes, and navigation logic remain unchanged
- Language switcher, theme toggle, and auth controls unchanged
- Mobile responsiveness maintained

