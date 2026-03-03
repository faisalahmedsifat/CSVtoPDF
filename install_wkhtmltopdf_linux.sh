#!/usr/bin/env bash
# Install wkhtmltopdf on Linux (Debian/Ubuntu/WSL)
set -e
echo "🔧 Installing wkhtmltopdf on Linux..."
sudo apt-get update -q
sudo apt-get install -y wkhtmltopdf
echo "✅ Done! $(wkhtmltopdf --version)"
