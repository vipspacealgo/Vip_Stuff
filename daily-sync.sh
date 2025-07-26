#!/bin/bash
# Daily Git Sync Script for Trading Repository

# Navigate to the repository
cd "/Users/vipusingh/Documents/Vip-Stuff/Github"

echo "🔄 Starting daily sync..."

# Check if there are any changes
if [[ -z $(git status --porcelain) ]]; then
    echo "✅ No changes to commit. Repository is up to date."
    exit 0
fi

# Show what changed
echo "📁 Files changed:"
git status --short

# Add all changes
git add .

# Get current date for commit message
DATE=$(date '+%Y-%m-%d %H:%M')

# Check if there are new strategies or significant changes
if git diff --cached --name-only | grep -q "strategies/"; then
    COMMIT_MSG="📈 Trading strategy updates - $DATE

- Updated Jesse trading strategies
- Modified strategy configurations
- Added new backtesting results

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
else
    COMMIT_MSG="🔄 Daily sync - $DATE

- Updated project files
- Synced latest changes

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"
fi

# Commit changes
git commit -m "$COMMIT_MSG"

# Push to GitHub
echo "⬆️ Pushing to GitHub..."
git push

if [ $? -eq 0 ]; then
    echo "✅ Successfully synced to GitHub!"
    echo "🌐 View at: https://github.com/vipspacealgo/Vip_Stuff"
else
    echo "❌ Push failed. Check your internet connection and try again."
fi