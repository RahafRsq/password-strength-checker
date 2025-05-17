@echo off
cd /d D:\Downloads\password-checker

echo 🔄 Adding updated password_results.xlsx...
git add password_results.xlsx

echo 💬 Committing changes...
git commit -m "🔁 Auto-update password results"

echo 🚀 Pushing to GitHub...
git push

echo ✅ Done!
pause
