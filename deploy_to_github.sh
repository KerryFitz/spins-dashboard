#!/bin/bash

# SPINS Dashboard GitHub Deployment Script
# This script helps you deploy your dashboard to GitHub + Streamlit Cloud

echo "=================================================="
echo "SPINS Dashboard - GitHub Deployment Helper"
echo "=================================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Error: Git is not installed"
    echo "Install from: https://git-scm.com/downloads"
    exit 1
fi

echo "✅ Git is installed"
echo ""

# Get GitHub username
read -p "Enter your GitHub username: " github_username

if [ -z "$github_username" ]; then
    echo "❌ GitHub username is required"
    exit 1
fi

# Get repository name
read -p "Enter repository name (default: spins-dashboard): " repo_name
repo_name=${repo_name:-spins-dashboard}

echo ""
echo "📋 Summary:"
echo "   GitHub User: $github_username"
echo "   Repository: $repo_name"
echo "   URL: https://github.com/$github_username/$repo_name"
echo ""

read -p "Continue? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "Cancelled"
    exit 0
fi

echo ""
echo "🚀 Starting deployment..."
echo ""

# Initialize git if not already initialized
if [ ! -d .git ]; then
    echo "📁 Initializing git repository..."
    git init
    echo "✅ Git initialized"
else
    echo "✅ Git already initialized"
fi

# Rename README for GitHub
if [ -f README_FOR_GITHUB.md ]; then
    echo "📝 Setting up README..."
    cp README_FOR_GITHUB.md README.md
    # Update placeholders
    sed -i '' "s/YOUR_USERNAME/$github_username/g" README.md
    sed -i '' "s/YOUR_DEPLOYED_URL/https://$github_username-$repo_name.streamlit.app/g" README.md
    echo "✅ README configured"
fi

# Add all files
echo "📦 Adding files to git..."
git add .
echo "✅ Files added"

# Create initial commit
echo "💾 Creating initial commit..."
git commit -m "Initial commit: SPINS Dashboard deployment"
echo "✅ Commit created"

# Set branch to main
echo "🌿 Setting branch to main..."
git branch -M main
echo "✅ Branch set"

# Add remote
echo "🔗 Connecting to GitHub..."
git remote add origin "https://github.com/$github_username/$repo_name.git"
echo "✅ Remote added"

echo ""
echo "=================================================="
echo "✅ Local setup complete!"
echo "=================================================="
echo ""
echo "📝 NEXT STEPS:"
echo ""
echo "1. Create GitHub repository:"
echo "   → Go to: https://github.com/new"
echo "   → Name: $repo_name"
echo "   → Privacy: PRIVATE (recommended for proprietary data)"
echo "   → Don't initialize with README"
echo "   → Click 'Create repository'"
echo ""
echo "2. Push your code:"
echo "   → Run: git push -u origin main"
echo "   → Enter GitHub credentials when prompted"
echo ""
echo "3. Deploy to Streamlit Cloud:"
echo "   → Go to: https://share.streamlit.io"
echo "   → Click 'New app'"
echo "   → Select your repository: $repo_name"
echo "   → Main file: spins_dashboard.py"
echo "   → Click 'Deploy'"
echo ""
echo "4. Your dashboard will be live at:"
echo "   → https://$github_username-$repo_name.streamlit.app"
echo ""
echo "5. Share with your team!"
echo ""
echo "=================================================="
echo ""
echo "💡 For detailed instructions, see:"
echo "   → DEPLOYMENT_GUIDE.md"
echo ""
echo "Need help? Check the deployment guide for troubleshooting."
echo ""
