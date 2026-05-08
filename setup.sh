#!/bin/bash
# setup.sh — one-shot environment setup
# run this once after cloning: bash setup.sh

echo "setting up grid07..."

# create venv
python3 -m venv venv
source venv/bin/activate

# install deps
pip install --upgrade pip -q
pip install -r requirements.txt -q

# copy env template if .env doesn't exist yet
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  created .env — open it and add your GROQ_API_KEY before running"
else
    echo ".env already exists, skipping"
fi

echo ""
echo "setup done. to run:"
echo "  source venv/bin/activate"
echo "  python main.py"
