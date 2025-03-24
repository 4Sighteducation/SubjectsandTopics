# Setup script for SubjectsandTopics
# This script helps initialize and push the project to GitHub

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
npm install

# Create .env file from example
if (-not (Test-Path ".env")) {
    Write-Host "Creating .env file from example..." -ForegroundColor Cyan
    Copy-Item ".env.example" ".env"
    Write-Host "Please edit the .env file to add your OpenRouter API key." -ForegroundColor Yellow
}

# Git setup
$repoExists = git remote -v 2>$null
if (-not $repoExists) {
    Write-Host "Setting up Git repository..." -ForegroundColor Cyan
    git init
    git remote add origin https://github.com/4Sighteducation/SubjectsandTopics.git
}

# Add files and commit
Write-Host "Adding files to Git..." -ForegroundColor Cyan
git add .

Write-Host "Committing files..." -ForegroundColor Cyan
git commit -m "Initial commit: Setup Curriculum Topic Generator"

# Prompt to push
$pushToRepo = Read-Host "Do you want to push to GitHub now? (y/n)"
if ($pushToRepo -eq "y") {
    Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
    git push -u origin main
}

Write-Host "Setup complete!" -ForegroundColor Green
Write-Host "To start the application, run: npm start" -ForegroundColor Cyan
