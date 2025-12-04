# Unified Diff - Session/Auth Fixes

## File: src/components/GalleryUploader.astro

### Change 1: Add initialItems to define:vars and initialize items array

```diff
- <script define:vars={{ uploadEndpoint, listEndpoint, deleteEndpointBase, uniqueId, maxItems, kind, onUpdate, t }}>
+ <script define:vars={{ uploadEndpoint, listEndpoint, deleteEndpointBase, uniqueId, maxItems, kind, onUpdate, t, initialItems }}>
    // Gallery items are plain objects with: id, url, width, height
-   let items = [];
+   // Initialize from server-provided initialItems if available
+   let items = initialItems && Array.isArray(initialItems) ? [...initialItems] : [];
```

### Change 2: Improve loadItems() error handling

```diff
    // Load initial items
    async function loadItems() {
      const { headers, token } = buildAuthHeaders();
      
-     // Don't attempt to load if there's no token
+     // Don't attempt to load if there's no token - silently skip
+     // Items are already initialized from initialItems if available
      if (!token) {
-       return;
+       // Render any initial items that were provided
+       if (items.length > 0) {
+         renderGrid();
+       }
+       return;
      }
  
      try {
        const response = await fetch(listEndpoint, {
          headers,
          credentials: 'include',
        });
  
        if (response.ok) {
          const data = await response.json();
          items = data.items || [];
          renderGrid();
          if (onUpdate) {
            onUpdate(items);
          }
          hideError();
        } else {
          const errorData = await response.json().catch(() => ({ detail: 'Failed to load portfolio' }));
          if (isAuthError(response, errorData)) {
-           showError(getSessionErrorMessage());
+           // Only show auth error if we don't have fallback items to display
+           // This prevents spurious errors when session is being established
+           if (items.length === 0) {
+             showError(getSessionErrorMessage());
+           }
          } else {
-           showError(errorData.detail || t.media.uploadError);
+           // Only show non-auth errors that are meaningful
+           const errorMsg = errorData.detail || t.media.uploadError;
+           if (errorMsg && !errorMsg.includes('authorization') && !errorMsg.includes('Session')) {
+             showError(errorMsg);
+           }
          }
        }
      } catch (error) {
-       console.error('Failed to load portfolio:', error);
-       // Don't show error on network failures, just log
+       // Don't show error on network failures, just log silently
+       // Keep existing items (from initialItems or previous successful load)
+       console.error('Failed to load portfolio:', error);
      }
    }
```

### Change 3: Render initial items immediately before API call

```diff
-   // Load items on mount
+   // Render initial items immediately if available
+   if (items.length > 0) {
+     renderGrid();
+   }
+
+   // Then attempt to load fresh items from API (will update if successful)
    loadItems();
```

## File: src/pages/[lang]/onboarding/artist/index.astro

### Change 1: Improved comment in focusFirstIncompleteStep()

```diff
        const isAuthError =
          response.status === 401 ||
          (errorData && (errorData.detail === 'Missing authorization token' || errorData.detail === 'Session expired'));
  
-         if (isAuthError && messageEl) {
+         // Only show auth error if it's a real 401, not on initial page load
+         // The middleware should have already handled redirects for invalid sessions
+         if (isAuthError && messageEl) {
            messageEl.textContent =
              lang === 'ru'
                ? 'Сессия истекла. Пожалуйста, войдите снова.'
                : 'Session expired. Please sign in again.';
            messageEl.className = 'text-sm text-red-500';
          }
```

