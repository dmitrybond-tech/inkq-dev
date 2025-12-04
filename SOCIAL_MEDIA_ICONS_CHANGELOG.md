# Social Media Icons Enhancement - Changelog

## Overview
Enhanced the social media buttons on the public artist page to be ~3x larger with clean black-and-white SVG icons for better visibility and recognition.

## Changes

### 1. `src/pages/[lang]/artists/[username].astro`

#### Interface Update
- **Line 43**: Added `vk?: string | null;` field to `PublicArtistProfile` interface to support VK social links (future-proofing).

#### Social Links Logic
- **Line 80**: Updated `hasSocial` check to include VK: `!!profile.instagram || !!profile.telegram || !!profile.vk`

#### Social Links UI Replacement (Lines 141-207)
- **Replaced** small text-based buttons (with emoji icons) with large icon-only buttons
- **Size**: Changed from small text buttons (`text-xs`, `px-3 py-1.5`) to large circular buttons (`w-14 h-14`, ~3x larger)
- **Icons**: 
  - Replaced emoji icons (📸, 💬) with inline SVG icons
  - Added Telegram SVG icon (filled style, black & white)
  - Added Instagram SVG icon (outline style, black & white)
  - Added VK SVG icon (filled style, black & white)
- **Styling**:
  - Large circular buttons: `w-14 h-14 rounded-full`
  - Theme-aware colors using CSS variables: `bg-[var(--inkq-bg)] text-[var(--inkq-fg)]`
  - Border: `border-2 border-[var(--inkq-border)]`
  - Hover states: `hover:bg-[var(--inkq-bg-subtle)]`
  - Focus states: `focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--inkq-muted)]`
- **Accessibility**:
  - Added `aria-label` attributes: "Open artist Telegram profile", "Open artist Instagram profile", "Open artist VK profile"
  - Added `sr-only` spans with network names for screen readers
  - Changed `rel="noreferrer"` to `rel="noopener noreferrer"` for better security
  - Added `aria-hidden="true"` to SVG icons
- **Layout**:
  - Changed container from `gap-3` to `gap-4` for better spacing
  - Added `items-center` to ensure vertical alignment
  - Maintained `flex-wrap` for responsive behavior
- **Order**: Changed order to Telegram → Instagram → VK (alphabetical)

## Technical Details

### Icon Specifications
- **Telegram**: Filled SVG icon, 24x24 viewBox, uses `fill="currentColor"`
- **Instagram**: Outline SVG icon, 24x24 viewBox, uses `stroke="currentColor"` with `stroke-width="1.5"`
- **VK**: Filled SVG icon, 24x24 viewBox, uses `fill="currentColor"`
- All icons are sized at `w-7 h-7` (28px) inside `w-14 h-14` (56px) buttons

### Theme Support
- Uses CSS variables from the existing design system: `--inkq-bg`, `--inkq-fg`, `--inkq-border`, `--inkq-bg-subtle`, `--inkq-muted`
- Automatically adapts to light/dark theme via `data-theme` attribute on HTML element
- Light mode: White background, dark text/icons, light gray border
- Dark mode: Dark background, white text/icons, dark gray border

### Conditional Rendering
- Each social network button only renders if the corresponding profile URL is present
- No placeholder or hardcoded links
- Gracefully handles missing social links without breaking layout

## Files Modified
1. `src/pages/[lang]/artists/[username].astro` - Updated social media links section

## Files Not Modified
- No backend changes
- No API route changes
- No database schema changes
- No routing or i18n changes
- No other component changes

