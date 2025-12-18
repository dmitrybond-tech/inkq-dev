# Auth Routing Fix - Manual Test Checklist

## Prerequisites

- Local development environment running
- Preprod/prod environment access (for deployment testing)
- Test user credentials available

## Local Testing

### 1. Signin Flow

- [ ] Navigate to `http://localhost:4321/en/signin`
- [ ] Submit form with valid credentials
- [ ] Verify 302 redirect response (not 422 JSON error)
- [ ] Verify `inkq_session` cookie is set in browser DevTools:
  - `httpOnly: true`
  - `sameSite: lax`
  - `secure: false` (in dev)
  - `path: /`
  - `maxAge: 604800` (7 days)
- [ ] Verify redirect destination:
  - If onboarding incomplete: `/{lang}/onboarding/{account_type}`
  - If onboarding complete: `/{lang}/dashboard/{account_type}`
- [ ] Verify navbar shows avatar and "Sign out" (not "Sign in" / "Sign up")

#### curl Test (Local)
```bash
curl -i -X POST http://localhost:4321/auth/signin \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Referer: http://localhost:4321/en/signin" \
  -d "login=testuser&password=testpass" \
  -c cookies.txt
```

**Expected:**
- Status: `302 Found`
- `Set-Cookie: inkq_session=...; Path=/; Max-Age=604800; HttpOnly; SameSite=Lax`
- `Location: /en/dashboard/{account_type}` or `/en/onboarding/{account_type}`

### 2. Signup Flow

- [ ] Navigate to `http://localhost:4321/en/signup`
- [ ] Fill in all required fields (email, username, password, account type)
- [ ] Submit form
- [ ] Verify 302 redirect response
- [ ] Verify `inkq_session` cookie is set
- [ ] Verify auto-login works (redirected to onboarding/dashboard)
- [ ] Verify navbar shows avatar and "Sign out"

#### curl Test (Local)
```bash
curl -i -X POST http://localhost:4321/auth/signup \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Referer: http://localhost:4321/en/signup" \
  -d "email=newuser@example.com&username=newuser&password=password123&accountType=artist" \
  -c cookies.txt
```

**Expected:**
- Status: `302 Found`
- `Set-Cookie: inkq_session=...; Path=/; Max-Age=604800; HttpOnly; SameSite=Lax`
- `Location: /en/onboarding/artist` (for new users)

### 3. Signout Flow

- [ ] While authenticated, click "Sign out" in navbar dropdown
- [ ] Verify 302 redirect to home page `/{lang}`
- [ ] Verify `inkq_session` cookie is cleared (check DevTools)
- [ ] Verify navbar shows "Sign in" / "Sign up" (not avatar)

#### curl Test (Local)
```bash
# First sign in to get a cookie
curl -i -X POST http://localhost:4321/auth/signin \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Referer: http://localhost:4321/en/signin" \
  -d "login=testuser&password=testpass" \
  -c cookies.txt

# Then sign out
curl -i -X POST http://localhost:4321/auth/signout \
  -H "Referer: http://localhost:4321/en/dashboard/artist" \
  -b cookies.txt \
  -c cookies.txt
```

**Expected:**
- Status: `302 Found`
- `Set-Cookie: inkq_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax`
- `Location: /en`

### 4. Error Handling

- [ ] Signin with invalid credentials → Should redirect to `/{lang}/signin?error=Invalid login or password`
- [ ] Signin with missing fields → Should redirect to `/{lang}/signin?error=Login and password are required`
- [ ] Signup with duplicate email → Should redirect to `/{lang}/signup?error=Email or username already exists`
- [ ] Signup with missing fields → Should redirect to `/{lang}/signup?error=All fields are required`

### 5. Language Support

- [ ] Test signin with `/{ru}/signin` → Should redirect to `/{ru}/dashboard/{account_type}`
- [ ] Test signup with `/{ru}/signup` → Should redirect to `/{ru}/onboarding/{account_type}`
- [ ] Test signout from Russian page → Should redirect to `/{ru}`

## Preprod/Prod Testing

### 1. Deploy Changes

- [ ] Deploy to preprod environment
- [ ] Verify endpoints are accessible at `https://preprod-domain.com/auth/signin`, `/auth/signup`, `/auth/signout`

### 2. Signin Flow (Preprod)

- [ ] Navigate to `https://preprod-domain.com/en/signin`
- [ ] Submit form with valid credentials
- [ ] Verify 302 redirect (not 422 error)
- [ ] Verify `inkq_session` cookie is set with `secure: true`
- [ ] Verify redirect to dashboard/onboarding
- [ ] Verify navbar shows authenticated state

#### curl Test (Preprod)
```bash
curl -i -X POST https://preprod-domain.com/auth/signin \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Referer: https://preprod-domain.com/en/signin" \
  -d "login=testuser&password=testpass" \
  -c cookies.txt
```

**Expected:**
- Status: `302 Found`
- `Set-Cookie: inkq_session=...; Path=/; Max-Age=604800; HttpOnly; Secure; SameSite=Lax`
- `Location: /en/dashboard/{account_type}`

### 3. Signup Flow (Preprod)

- [ ] Test signup form submission
- [ ] Verify cookie is set with `secure: true`
- [ ] Verify redirect and authenticated state

### 4. Signout Flow (Preprod)

- [ ] Test signout from navbar
- [ ] Verify cookie is cleared
- [ ] Verify redirect to home and unauthenticated state

## Regression Testing

- [ ] Verify backend `/api/v1/auth/*` endpoints still work for API clients
- [ ] Verify existing `/api/v1/auth/*` Astro routes are still accessible (if any direct API calls exist)
- [ ] Verify no console errors in browser DevTools
- [ ] Verify no server errors in logs

## Success Criteria

✅ All form submissions return 302 redirects (not 422 errors)  
✅ `inkq_session` cookie is properly set after signin/signup  
✅ Cookie is properly cleared after signout  
✅ Navbar shows authenticated state after signin/signup  
✅ Navbar shows unauthenticated state after signout  
✅ Language is correctly preserved in redirects  
✅ Error messages are displayed correctly via query params  
✅ All tests pass in both local and preprod/prod environments  

