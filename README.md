# Marketing KPIs Dashboard

A dashboard to track your Meta ad creative performance and win rates.

---

## PART 1: Getting the Dashboard Running (10 minutes)

### Step 1: Open Terminal

1. On your Mac, press `Cmd + Space` to open Spotlight
2. Type `Terminal` and press Enter
3. A black/white window will open - this is where you'll type commands

### Step 2: Go to the Dashboard Folder

Copy and paste this command into Terminal, then press Enter:

```
cd ~/Desktop/Marketing\ KPIs
```

### Step 3: Install Python (if you don't have it)

Copy and paste this command:

```
python3 --version
```

If you see a version number like `Python 3.11.0`, skip to Step 4.

If you see an error, you need to install Python:
1. Go to https://www.python.org/downloads/
2. Click the big yellow "Download Python" button
3. Open the downloaded file and follow the installer
4. Close Terminal and open it again
5. Run the `cd` command from Step 2 again

### Step 4: Install Required Packages

Copy and paste this command (it will take 1-2 minutes):

```
pip3 install -r requirements.txt
```

You'll see a lot of text scrolling. Wait until you see a new line where you can type.

### Step 5: Start the Dashboard

Copy and paste this command:

```
streamlit run app.py
```

Your web browser will automatically open with the dashboard!

### Step 6: Test with Demo Data

1. In the dashboard, look at the left sidebar
2. Check the box that says "Use Demo Data"
3. You'll see sample metrics and data appear

**Congratulations! The dashboard is running!**

To stop it, go back to Terminal and press `Ctrl + C`

---

## PART 2: Connect Your Real Meta Ads Account (30 minutes)

### Step 1: Create a Meta Developer Account

1. Go to: https://developers.facebook.com/
2. Click "Get Started" in the top right
3. Log in with your Facebook account
4. Accept the terms and complete the setup

### Step 2: Create an App

1. Click "My Apps" in the top right
2. Click "Create App"
3. Select "Other" for use case, click Next
4. Select "Business" as app type, click Next
5. Enter a name like "My Marketing Dashboard"
6. Enter your email
7. Click "Create App"

### Step 3: Add Marketing API to Your App

1. In your app dashboard, scroll down to "Add products to your app"
2. Find "Marketing API" and click "Set Up"
3. Done! The Marketing API is now added

### Step 4: Get Your App ID and Secret

1. In the left sidebar, click "App Settings" → "Basic"
2. You'll see:
   - **App ID**: A number like `123456789012345` (copy this)
   - **App Secret**: Click "Show", enter your Facebook password, then copy it

### Step 5: Get Your Access Token

1. Go to: https://developers.facebook.com/tools/explorer/
2. In the top right, select your app from the dropdown
3. Click "Generate Access Token"
4. A Facebook popup will ask for permissions - click "Continue" and allow everything
5. Copy the long text that appears in the "Access Token" field

**Important**: This token expires in 1 hour. See Part 3 for a longer-lasting token.

### Step 6: Find Your Ad Account ID

1. Go to: https://business.facebook.com/
2. Click the gear icon (Settings) in the bottom left
3. Click "Ad Accounts" under "Accounts"
4. Click on your ad account
5. Look for "Ad Account ID" - it looks like `act_123456789`
6. Copy the entire thing including `act_`

### Step 7: Get an Anthropic API Key (for AI features)

1. Go to: https://console.anthropic.com/
2. Create an account or log in
3. Go to "API Keys" in the left menu
4. Click "Create Key"
5. Name it "Marketing Dashboard"
6. Copy the key (starts with `sk-ant-`)

**Note**: Anthropic requires adding payment method. AI analysis costs ~$0.01 per ad creative.

### Step 8: Save Your Credentials

1. Open Finder
2. Go to Desktop → Marketing KPIs folder
3. Find the file called `.env.example`
4. Right-click it → "Duplicate"
5. Rename the duplicate to `.env` (remove the `.example` part)
6. Right-click `.env` → "Open With" → "TextEdit"
7. Replace the placeholder text with your real values:

```
META_APP_ID=paste_your_app_id_here
META_APP_SECRET=paste_your_app_secret_here
META_ACCESS_TOKEN=paste_your_access_token_here
META_AD_ACCOUNT_ID=act_paste_your_account_id_here
ANTHROPIC_API_KEY=sk-ant-paste_your_key_here
```

8. Save the file (Cmd + S) and close TextEdit

### Step 9: Run with Real Data

1. Go back to Terminal
2. If the dashboard is still running, press `Ctrl + C` to stop it
3. Start it again:

```
streamlit run app.py
```

4. In the sidebar, UNCHECK "Use Demo Data"
5. Your real ad data should now appear!

---

## PART 3: Get a Long-Lasting Access Token (Optional but Recommended)

The token from Step 5 expires in 1 hour. Here's how to get one that lasts 60 days:

1. Go to: https://developers.facebook.com/tools/explorer/
2. Generate a token like in Step 5
3. Go to: https://developers.facebook.com/tools/debug/accesstoken/
4. Paste your token and click "Debug"
5. Click "Extend Access Token" at the bottom
6. Copy the new extended token
7. Update your `.env` file with the new token

**Set a reminder** to repeat this every 60 days, or the dashboard will stop working.

---

## How the Dashboard Works

### Win Rate

A creative is a "winner" when it meets BOTH conditions:
- ROAS is 2.0 or higher (you can change this)
- Spent at least $100 (you can change this)

Change these numbers in the sidebar under "Win Rules"

### AI Angle Detection

The dashboard uses AI to automatically categorize your ad creatives:
- Problem/Solution
- UGC Style
- Social Proof
- Product Demo
- Before/After
- And more...

This helps you see which creative angles perform best.

### Tabs

- **Funnel**: Performance by TOF/MOF/BOF (based on campaign objective)
- **Format**: Video vs Image vs Carousel
- **Angle**: AI-detected creative angles
- **Creator**: Performance by creator (if in your ad names)
- **Monthly**: Performance by launch month

---

## Troubleshooting

### "No data available"
- Make sure "Use Demo Data" is unchecked
- Check that your `.env` file has the correct credentials
- Your access token might have expired - generate a new one

### Dashboard won't start
- Make sure you're in the right folder: `cd ~/Desktop/Marketing\ KPIs`
- Try reinstalling packages: `pip3 install -r requirements.txt`

### "ModuleNotFoundError"
Run this command:
```
pip3 install streamlit pandas facebook-business python-dotenv plotly anthropic requests
```

### Need help?
Feel free to ask! Describe what you see on your screen and any error messages.
