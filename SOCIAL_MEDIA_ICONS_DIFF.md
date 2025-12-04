# Unified Diff - Social Media Icons Enhancement

```diff
diff --git a/src/pages/[lang]/artists/[username].astro b/src/pages/[lang]/artists/[username].astro
index 0000000..1111111 100644
--- a/src/pages/[lang]/artists/[username].astro
+++ b/src/pages/[lang]/artists/[username].astro
@@ -35,6 +35,7 @@ interface PublicArtistProfile {
   session_price?: number | null;
   instagram?: string | null;
   telegram?: string | null;
+  vk?: string | null;
   avatar_url?: string | null;
   banner_url?: string | null;
   portfolio: PublicArtistPortfolioItem[];
@@ -78,7 +79,7 @@ if (notFound || !profile) {
 }
 
 const artistName = profile.username;
-const hasSocial = !!profile.instagram || !!profile.telegram;
+const hasSocial = !!profile.instagram || !!profile.telegram || !!profile.vk;
 ---
 
 <PublicLayout title={artistName} lang={lang} t={t} currentPath={currentPath}>
@@ -138,28 +139,67 @@ if (notFound || !profile) {
       </div>
 
       {hasSocial && (
-        <div class="flex flex-wrap gap-3">
+        <div class="flex flex-wrap items-center gap-4">
+          {profile.telegram && (
+            <a
+              href={profile.telegram.startsWith('http') ? profile.telegram : `https://t.me/${profile.telegram.replace('@', '')}`}
+              target="_blank"
+              rel="noopener noreferrer"
+              aria-label="Open artist Telegram profile"
+              class="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[var(--inkq-bg)] text-[var(--inkq-fg)] border-2 border-[var(--inkq-border)] hover:bg-[var(--inkq-bg-subtle)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--inkq-muted)] transition-colors"
+            >
+              <svg
+                class="w-7 h-7"
+                fill="currentColor"
+                viewBox="0 0 24 24"
+                xmlns="http://www.w3.org/2000/svg"
+                aria-hidden="true"
+              >
+                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.13-.31-1.09-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
+              </svg>
+              <span class="sr-only">Telegram</span>
+            </a>
+          )}
           {profile.instagram && (
             <a
               href={profile.instagram.startsWith('http') ? profile.instagram : `https://instagram.com/${profile.instagram.replace('@', '')}`}
               target="_blank"
-              rel="noreferrer"
-              class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--inkq-bg-subtle)] text-[var(--inkq-fg)] text-xs hover:bg-[var(--inkq-border)] transition-colors"
+              rel="noopener noreferrer"
+              aria-label="Open artist Instagram profile"
+              class="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[var(--inkq-bg)] text-[var(--inkq-fg)] border-2 border-[var(--inkq-border)] hover:bg-[var(--inkq-bg-subtle)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--inkq-muted)] transition-colors"
             >
-              <span>📸</span>
-              <span>Instagram</span>
+              <svg
+                class="w-7 h-7"
+                fill="none"
+                stroke="currentColor"
+                stroke-width="1.5"
+                viewBox="0 0 24 24"
+                xmlns="http://www.w3.org/2000/svg"
+                aria-hidden="true"
+              >
+                <rect x="2" y="2" width="20" height="20" rx="5" ry="5"/>
+                <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
+                <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/>
+              </svg>
+              <span class="sr-only">Instagram</span>
             </a>
           )}
-          {profile.telegram && (
+          {profile.vk && (
             <a
-              href={profile.telegram.startsWith('http') ? profile.telegram : `https://t.me/${profile.telegram.replace('@', '')}`}
+              href={profile.vk.startsWith('http') ? profile.vk : `https://vk.com/${profile.vk.replace('@', '')}`}
               target="_blank"
-              rel="noreferrer"
-              class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[var(--inkq-bg-subtle)] text-[var(--inkq-fg)] text-xs hover:bg-[var(--inkq-border)] transition-colors"
+              rel="noopener noreferrer"
+              aria-label="Open artist VK profile"
+              class="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[var(--inkq-bg)] text-[var(--inkq-fg)] border-2 border-[var(--inkq-border)] hover:bg-[var(--inkq-bg-subtle)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--inkq-muted)] transition-colors"
             >
-              <span>💬</span>
-              <span>Telegram</span>
+              <svg
+                class="w-7 h-7"
+                fill="currentColor"
+                viewBox="0 0 24 24"
+                xmlns="http://www.w3.org/2000/svg"
+                aria-hidden="true"
+              >
+                <path d="M12.785 16.241s.287-.029.435-.18c.135-.137.131-.393.131-.393s-.02-1.123.515-1.288c.526-.164 1.2 1.09 1.912 1.57.54.36.95.281.95.281l1.912-.027s1-.064.525-.855c-.039-.064-.277-.576-1.425-1.63-1.205-1.11-1.043-.931.408-2.853.28-.37.785-1.23.785-1.23s.18-.43-.09-.667c-.27-.235-.64-.155-.64-.155l-1.846.011s-.27-.03-.47.09c-.193.117-.315.39-.315.39s-.563 1.5-1.31 2.776c-1.58 2.52-2.214 2.655-2.472 2.503-.6-.352-.45-1.41-.45-2.163 0-2.353.35-3.337-.685-3.59-.345-.085-.598-.143-1.48-.152-1.13-.01-2.085.003-2.625.27-.36.18-.638.58-.47.603.21.03.686.13.94.475.33.45.318 1.46.318 1.46s.19 2.81-.445 3.157c-.437.24-1.04-.25-2.33-2.5-.66-1.14-1.16-2.4-1.16-2.4s-.1-.24-.27-.37c-.21-.16-.5-.21-.5-.21l-1.76.011s-.53.016-.725.24c-.17.19-.13.48-.13.48s1.05 2.48 2.24 4.67c2.09 3.5 3.01 4.11 3.01 4.11s.18.12.28.07c.1-.05.68-.44 1.36-1.48.86-1.33 1.51-2.76 1.51-2.76s.12-.24.3-.03c.18.21.69.85 1.48 1.63 1 .95 1.75 1.25 1.75 1.25z"/>
+              </svg>
+              <span class="sr-only">VK</span>
             </a>
           )}
         </div>
       )}
```

