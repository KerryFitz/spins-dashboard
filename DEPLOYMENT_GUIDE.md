# SPINS Dashboard Deployment Guide

Complete guide for sharing your dashboard with your Humble Brands team.

---

## 🏆 OPTION 1: Streamlit Cloud (RECOMMENDED)

**Best for:** Most teams - Free, easy, professional

### Pros:
- ✅ **100% Free** (unlimited viewers)
- ✅ **Zero setup for users** (just share URL)
- ✅ **Auto-updates** when you push changes
- ✅ **Professional URL** (humble-spins.streamlit.app)
- ✅ **SSL/HTTPS** included
- ✅ **No server management**

### Cons:
- ⚠️ Data files stored on Streamlit's servers
- ⚠️ Can be public or private (requires GitHub account to access private apps)

### Setup Steps:

#### Step 1: Create GitHub Repository

1. Go to https://github.com and sign in (or create account)
2. Click "New Repository"
   - Name: `spins-dashboard`
   - Privacy: Choose **Private** (keeps your data confidential)
   - Don't initialize with README
3. Click "Create repository"

#### Step 2: Push Your Code to GitHub

Open Terminal in your dashboard directory and run:

```bash
cd /Users/kerryfitzmaurice/Desktop/SPINS/2025

# Initialize git repository
git init

# Add all files (except those in .gitignore)
git add .

# Create first commit
git commit -m "Initial SPINS dashboard deployment"

# Connect to GitHub (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/spins-dashboard.git

# Push to GitHub
git branch -M main
git push -u origin main
```

**IMPORTANT:** The .gitignore file prevents your SPINS data files (*.xlsx) from being committed. Your proprietary data stays local.

#### Step 3: Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click "Sign up" and sign in with GitHub
3. Click "New app"
4. Select:
   - **Repository**: spins-dashboard
   - **Branch**: main
   - **Main file path**: spins_dashboard.py
5. Click "Advanced settings"
   - Add **Secrets** if needed (we'll cover this below)
6. Click "Deploy!"

Wait 3-5 minutes for deployment...

#### Step 4: Upload Data Files

Since we don't commit data files to GitHub (for security), you need to upload them:

**Option A: Use the built-in file uploader**
- Users upload data files through the dashboard interface
- Files are temporary per session

**Option B: Use Streamlit Secrets (for default data)**
This is more complex but provides default data:
1. Convert your Excel files to a format suitable for secrets
2. Use `st.secrets` to load data
3. Not recommended for large SPINS files

**Option C: Use a secure file storage**
- Upload files to Google Drive/Dropbox
- Share with Streamlit app using service account
- More complex setup

**RECOMMENDED:** Use Option A (file uploader) - your dashboard already has this feature!

#### Step 5: Share with Team

Your dashboard will be live at: `https://YOUR-USERNAME-spins-dashboard.streamlit.app`

- Share this URL with your team
- For private repos: Team members need GitHub accounts and access to your repo
- They can access from any device with internet

### Updating the Dashboard

When you make changes:

```bash
git add .
git commit -m "Description of changes"
git push
```

Streamlit Cloud will automatically redeploy (takes 1-2 minutes).

---

## 💻 OPTION 2: Local Network Deployment

**Best for:** Teams in the same office/VPN who want full control

### Pros:
- ✅ **Complete data control** (stays on your network)
- ✅ **No external dependencies**
- ✅ **Fast performance**
- ✅ **No cloud costs**

### Cons:
- ⚠️ Requires a computer/server to stay running
- ⚠️ Team must be on same network or VPN
- ⚠️ You manage updates manually

### Setup Steps:

#### Option 2A: Run on Your Mac

**Your Mac stays on and team accesses via your IP**

1. Find your Mac's local IP address:
```bash
ipconfig getifaddr en0
```
(Example output: 10.12.18.196)

2. Start dashboard:
```bash
cd /Users/kerryfitzmaurice/Desktop/SPINS/2025
streamlit run spins_dashboard.py --server.port 8501 --server.address 0.0.0.0
```

3. Share with team: `http://YOUR-IP:8501`
   - Example: `http://10.12.18.196:8501`
   - Team must be on same WiFi/network

4. Keep your Mac awake and dashboard running

**To keep it running 24/7:**
- Prevent Mac from sleeping (System Preferences → Energy Saver)
- Or use `caffeinate` command to prevent sleep

#### Option 2B: Run on Dedicated Server

**Use a spare computer or cloud VM as dedicated server**

Requirements:
- Mac, Linux, or Windows computer/VM
- Python 3.9+
- Always on, connected to network

Setup:
1. Install Python on server
2. Copy dashboard files to server
3. Install dependencies: `pip install -r requirements.txt`
4. Run dashboard: `streamlit run spins_dashboard.py --server.address 0.0.0.0`
5. Share server IP with team

**For production use:**
- Use `screen` or `tmux` to keep dashboard running
- Set up systemd service (Linux) for auto-restart
- Configure firewall to allow port 8501

---

## ☁️ OPTION 3: Cloud VM Deployment

**Best for:** Teams who want control + remote access without Streamlit Cloud

### Options:
- **AWS EC2** (t3.small = ~$15/month)
- **DigitalOcean Droplet** ($6/month basic)
- **Google Cloud Compute** (~$10/month)
- **Azure VM** (~$15/month)

### Pros:
- ✅ **Accessible from anywhere**
- ✅ **Full control**
- ✅ **Your own domain possible**
- ✅ **Data stays in your cloud account**

### Cons:
- ⚠️ Costs ~$10-20/month
- ⚠️ Requires some technical setup
- ⚠️ You manage updates and security

### Quick Setup (DigitalOcean Example):

1. Create DigitalOcean account ($100 free credit for new users)
2. Create Ubuntu 22.04 Droplet ($6/month)
3. SSH into server
4. Install Python and dependencies:
```bash
sudo apt update
sudo apt install python3-pip
pip3 install -r requirements.txt
```
5. Upload your dashboard files (use scp or git)
6. Run with systemd or docker (see detailed instructions below)
7. Access via: `http://YOUR_DROPLET_IP:8501`

**Optional: Add domain name**
- Point your domain to droplet IP
- Set up nginx reverse proxy
- Add SSL certificate (Let's Encrypt free)
- Result: `https://spins.humblebrands.com`

---

## 📦 OPTION 4: Standalone Executable

**Best for:** Non-technical users who want desktop app

### Pros:
- ✅ **No installation needed** (just download & run)
- ✅ **Works offline**
- ✅ **Feels like a native app**

### Cons:
- ⚠️ Large file size (~150MB)
- ⚠️ Need to rebuild for each OS (Mac/Windows/Linux)
- ⚠️ Updates require redistributing file

### Build with PyInstaller:

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --name SPINSDashboard \
            --onefile \
            --add-data "spins_dashboard.py:." \
            --hidden-import streamlit \
            spins_dashboard.py
```

Distribute the executable in `dist/` folder.

**Note:** This is complex for Streamlit apps and not the recommended approach.

---

## 🔐 Security Considerations

### Data Security:

**If deploying to cloud:**
1. ✅ Use private GitHub repo (not public)
2. ✅ Don't commit Excel data files (.gitignore prevents this)
3. ✅ Use file uploader for data (not hardcoded files)
4. ✅ Consider password protection (see below)
5. ✅ Review who has access regularly

**For sensitive data:**
- Use authentication (Streamlit Cloud supports GitHub auth)
- Add password protection (code example below)
- Use VPN for network deployments
- Encrypt data at rest

### Adding Password Protection:

Add this to the top of `spins_dashboard.py`:

```python
import streamlit as st
import hashlib

def check_password():
    """Returns True if user entered correct password."""

    def password_entered():
        """Checks whether password is correct."""
        if hashlib.sha256(st.session_state["password"].encode()).hexdigest() == \
           "YOUR_HASHED_PASSWORD_HERE":  # Change this
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()

# Rest of your dashboard code here...
```

Generate hashed password:
```python
import hashlib
password = "your_password"
print(hashlib.sha256(password.encode()).hexdigest())
```

---

## 📊 Recommended Setup for Humble Brands

Based on your needs, here's my recommendation:

### Phase 1: Quick Start (This Week)
**Use Streamlit Cloud**
- Free, fast setup
- Share URL with team immediately
- Team uploads data files as needed
- Perfect for getting feedback

### Phase 2: Production (If Needed)
**If data security is critical:**
- Switch to local network deployment (Option 2)
- Or use cloud VM with VPN (Option 3)
- Add password protection
- Set up regular data backups

### Phase 3: Scale (Future)
**When dashboard usage grows:**
- Consider dedicated server
- Set up automated data pipeline
- Add user management
- Create mobile-friendly views

---

## 🚀 Quick Start Commands

### For Streamlit Cloud:
```bash
cd /Users/kerryfitzmaurice/Desktop/SPINS/2025
git init
git add .
git commit -m "Initial commit"
# Follow GitHub setup above
```

### For Local Network:
```bash
cd /Users/kerryfitzmaurice/Desktop/SPINS/2025
streamlit run spins_dashboard.py --server.address 0.0.0.0
# Share your IP with team
```

### For Cloud VM (DigitalOcean/AWS):
```bash
# On your VM:
git clone https://github.com/YOUR_USERNAME/spins-dashboard.git
cd spins-dashboard
pip3 install -r requirements.txt
streamlit run spins_dashboard.py --server.port 80 --server.address 0.0.0.0
```

---

## 🆘 Support & Troubleshooting

### Common Issues:

**"ModuleNotFoundError"**
- Solution: `pip install -r requirements.txt`

**"Address already in use"**
- Solution: Change port: `--server.port 8502`

**"Connection refused"**
- Solution: Check firewall settings, use `--server.address 0.0.0.0`

**Team can't access**
- Check they're on same network (for local)
- Verify firewall allows port 8501
- Test with your phone on same WiFi

---

## 📞 Next Steps

1. **Choose your deployment method** (I recommend Streamlit Cloud)
2. **Follow the setup steps** above
3. **Test with one team member** before rolling out
4. **Share URL and upload instructions**
5. **Gather feedback** and iterate

Need help with setup? Let me know which option you want to pursue and I can provide more detailed guidance!
