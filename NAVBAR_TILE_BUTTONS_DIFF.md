# Unified Diff - Navbar Tile Buttons Transformation

## File: src/components/Header.astro

```diff
---
 import type { Lang, I18nSchema } from '../i18n/types';
 import LanguageSwitcher from './LanguageSwitcher.astro';
 import ThemeToggle from './ThemeToggle.astro';

 interface Props {
   lang: Lang;
   t: I18nSchema;
   currentPath: string;
 }

 const { lang, t, currentPath } = Astro.props;
 // Current authenticated user is provided by middleware via Astro.locals.currentUser.
 // Use `any` here to avoid tight coupling to backend user schema types.
 // eslint-disable-next-line @typescript-eslint/no-explicit-any
 const currentUser = (Astro.locals as any).currentUser as any | null | undefined;
 const username: string | undefined = currentUser?.username;
 const userInitial = username ? username.charAt(0).toUpperCase() : '';
 const dashboardHref =
   currentUser && currentUser.account_type
     ? `/${lang}/dashboard/${currentUser.account_type}`
     : `/${lang}/dashboard`;
 
+// Determine active navigation links based on current path
+const isActiveArtists = currentPath.startsWith(`/${lang}/artists`);
+const isActiveStudios = currentPath.startsWith(`/${lang}/studios`);
+const isActiveModels = currentPath.startsWith(`/${lang}/models`);
 ---
 
 <header class="border-b border-[var(--inkq-border)] bg-[var(--inkq-surface)] sticky top-0 z-50">
   <div class="max-w-6xl mx-auto px-4">
-    <nav class="flex items-center justify-between h-16">
+    <nav class="flex items-center justify-between py-4">
       <!-- Logo -->
       <a href={`/${lang}/`} class="text-xl font-bold text-[var(--inkq-fg)]">
         {t.common.appName}
       </a>
 
       <!-- Navigation links -->
-      <div class="hidden md:flex items-center gap-6">
+      <div class="hidden md:flex items-center gap-2">
         <a
           href={`/${lang}/artists`}
-          class="text-sm font-medium text-[var(--inkq-fg)] hover:text-[var(--inkq-muted)] transition-colors"
+          class={`px-4 py-2 rounded-lg text-sm md:text-base font-medium text-[var(--inkq-fg)] transition-colors ${
+            isActiveArtists
+              ? 'bg-[var(--inkq-bg-subtle)]'
+              : 'hover:bg-[var(--inkq-bg-subtle)]'
+          } focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--inkq-border)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--inkq-surface)]`}
         >
           {t.header.navArtists}
         </a>
         <a
           href={`/${lang}/studios`}
-          class="text-sm font-medium text-[var(--inkq-fg)] hover:text-[var(--inkq-muted)] transition-colors"
+          class={`px-4 py-2 rounded-lg text-sm md:text-base font-medium text-[var(--inkq-fg)] transition-colors ${
+            isActiveStudios
+              ? 'bg-[var(--inkq-bg-subtle)]'
+              : 'hover:bg-[var(--inkq-bg-subtle)]'
+          } focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--inkq-border)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--inkq-surface)]`}
         >
           {t.header.navStudios}
         </a>
         <a
           href={`/${lang}/models`}
-          class="text-sm font-medium text-[var(--inkq-fg)] hover:text-[var(--inkq-muted)] transition-colors"
+          class={`px-4 py-2 rounded-lg text-sm md:text-base font-medium text-[var(--inkq-fg)] transition-colors ${
+            isActiveModels
+              ? 'bg-[var(--inkq-bg-subtle)]'
+              : 'hover:bg-[var(--inkq-bg-subtle)]'
+          } focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--inkq-border)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--inkq-surface)]`}
         >
           {t.header.navModels}
         </a>
       </div>
 
       <!-- Right side: Auth or user block, Language, Theme -->
       <div class="flex items-center gap-3">
         {currentUser ? (
           <details class="relative">
             <summary class="flex items-center gap-2 rounded-full px-2 py-1 hover:bg-[var(--inkq-bg-subtle)] transition-colors max-w-[12rem] cursor-pointer list-none">
               {currentUser.avatar_url ? (
                 <img
                   src={currentUser.avatar_url}
                   alt={username || 'User avatar'}
                   class="h-8 w-8 rounded-full object-cover"
                   loading="lazy"
                 />
               ) : username ? (
                 <div
                   class="h-8 w-8 rounded-full bg-[var(--inkq-bg-subtle)] flex items-center justify-center text-xs font-semibold text-[var(--inkq-fg)]"
                   aria-hidden="true"
                 >
                   {userInitial}
                 </div>
               ) : (
                 <img
                   src="/placeholder-avatar.svg"
                   alt="User avatar"
                   class="h-8 w-8 rounded-full object-cover"
                   loading="lazy"
                 />
               )}
               {username && (
                 <span class="text-sm font-medium text-[var(--inkq-fg)] truncate">
                   {username}
                 </span>
               )}
             </summary>
             <div class="absolute right-0 mt-2 w-40 rounded-md border border-[var(--inkq-border)] bg-[var(--inkq-surface)] shadow-lg py-1 z-20">
               <a
                 href={dashboardHref}
                 class="block px-4 py-2 text-sm text-[var(--inkq-fg)] hover:bg-[var(--inkq-bg-subtle)] transition-colors"
               >
                 {t.common.dashboard}
               </a>
               <form method="post" action="/api/v1/auth/signout" class="border-t border-[var(--inkq-border)] mt-1">
                 <input type="hidden" name="lang" value={lang} />
                 <button
                   type="submit"
                   class="w-full text-left px-4 py-2 text-sm text-[var(--inkq-fg)] hover:bg-[var(--inkq-bg-subtle)] transition-colors"
                 >
                   {t.common.signOut}
                 </button>
               </form>
             </div>
           </details>
         ) : (
           <>
             <a
               href={`/${lang}/signin`}
               class="px-3 py-2 rounded-md text-sm font-medium text-[var(--inkq-fg)] hover:bg-[var(--inkq-bg-subtle)] transition-colors"
             >
               {t.common.signIn}
             </a>
             <a
               href={`/${lang}/signup`}
               class="px-3 py-2 rounded-md text-sm font-medium bg-[var(--inkq-fg)] text-[var(--inkq-bg)] hover:opacity-90 transition-opacity"
             >
               {t.common.signUp}
             </a>
           </>
         )}
         <LanguageSwitcher currentLang={lang} currentPath={currentPath} />
         <ThemeToggle />
       </div>
     </nav>
   </div>
 </header>
 
 <style>
   /* Hide default summary marker */
   details summary::-webkit-details-marker {
     display: none;
   }
   details summary::marker {
     display: none;
   }
 </style>
```

## Summary of Changes

### Added (Lines 24-27):
- Active state detection logic for Artists, Studios, and Models navigation links

### Modified:

1. **Navbar container (Line 32)**:
   - Changed from fixed height `h-16` to padding-based height `py-4` for increased vertical space

2. **Navigation links container (Line 39)**:
   - Reduced gap from `gap-6` to `gap-2` for tighter spacing between tile buttons

3. **Artists link (Lines 40-49)**:
   - Added tile-like styling: `px-4 py-2 rounded-lg`
   - Increased font size: `text-sm md:text-base`
   - Added conditional active state: `bg-[var(--inkq-bg-subtle)]` when active
   - Changed hover from text color to background: `hover:bg-[var(--inkq-bg-subtle)]`
   - Added keyboard focus styles: `focus-visible:ring-2` with proper offset

4. **Studios link (Lines 50-59)**:
   - Same changes as Artists link with active state detection for Studios

5. **Models link (Lines 60-69)**:
   - Same changes as Artists link with active state detection for Models

### Preserved:
- All URLs and routing paths remain unchanged
- Language switcher, theme toggle, and auth controls unchanged
- Mobile responsiveness (links hidden on mobile with `hidden md:flex`)
- All existing color tokens and design system usage

