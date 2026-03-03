#!/usr/bin/env bash
# Install wkhtmltopdf on macOS via Homebrew
set -e
echo "🔧 Installing wkhtmltopdf on macOS..."
if ! command -v brew &> /dev/null; then
  echo "❌ Homebrew not found. Install it first: https://brew.sh"
  exit 1
fi
brew install --cask wkhtmltopdf
echo "✅ Done! $(wkhtmltopdf --version)"
