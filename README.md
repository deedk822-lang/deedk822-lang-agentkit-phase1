<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/drive/1ZlqlqMORGxqxJ2KhfsRwjDVKaFI9ODx7

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

## 🔄 Integration-Lifecycle Commands (new)

| Command | Example | Autonomy |
|---|---|---|
| `CHECK_INTEGRATION_STATUS service=meta_lead_ads` | Low | ✅ instant |
| `REFRESH_TOKEN service=zapier` | Medium | ⚠️ judge approval |
| `CONNECT_INTEGRATION service=squarespace` | High | 🚫 blocked – opens ticket |
| `SYNC_AUDIENCE audience_id=abc123 dest=meta` | Medium | ⚠️ judge approval |

> The agent now **manages** integrations, not merely **pushes** content.
