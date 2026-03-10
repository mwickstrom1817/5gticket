# 5G Security Portal — PWA Wrapper

Makes the Streamlit portal installable as a home screen app on iOS and Android.

## Files

| File | Purpose |
|---|---|
| `index.html` | App shell — loads the portal in a full-screen iframe |
| `manifest.json` | Tells browsers this is an installable PWA |
| `sw.js` | Service worker — handles offline splash screen |
| `offline.html` | Shown when the user has no internet connection |
| `_redirects` | Cloudflare Pages routing config |
| `icon-192.png` | App icon (you provide) — 192×192px PNG |
| `icon-512.png` | App icon (you provide) — 512×512px PNG |

## Setup

### 1. Add your icons
Place two PNG versions of your logo in this folder:
- `icon-192.png` — 192×192px
- `icon-512.png` — 512×512px

Square logos work best. Use a transparent or dark background.

### 2. Deploy to Cloudflare Pages

1. Push this `pwa/` folder to a GitHub repo (can be the same repo as your portal,
   or a separate one)
2. Go to [Cloudflare Pages](https://pages.cloudflare.com) → Create a project
3. Connect your GitHub repo
4. Set build settings:
   - Build command: *(leave blank)*
   - Build output directory: `pwa` (or `/` if it's the root)
5. Deploy — Cloudflare gives you a free `*.pages.dev` URL immediately

### 3. Add a custom domain (optional but recommended)
In Cloudflare Pages → Custom Domains → add `portal.fivegsecurity.net` or similar.
If your domain is already on Cloudflare DNS this takes about 30 seconds.

---

## How clients install it

### iPhone (Safari)
1. Open the portal URL in Safari
2. Tap the Share button (box with arrow)
3. Tap **Add to Home Screen**
4. Tap **Add**

### Android (Chrome)
1. Open the portal URL in Chrome
2. Tap the three-dot menu
3. Tap **Add to Home Screen** (or Chrome may show an install banner automatically)

---

## Updating the portal URL
If your Streamlit URL changes, edit the `src` in `index.html`:
```html
<iframe src="https://5gticket.streamlit.app" ...>
```
Then redeploy to Cloudflare Pages (just push to GitHub — auto-deploys).
