#!/bin/bash
# Quick setup script for HF Spaces deployment

echo "🚀 Setting up InsightPilot for Hugging Face Spaces deployment"
echo ""

# Check if we should build frontend
read -p "Build React frontend? (y/n - takes a few minutes): " build_frontend

if [ "$build_frontend" = "y" ] || [ "$build_frontend" = "Y" ]; then
    echo "📦 Building frontend..."
    cd frontend
    npm install
    npm run build
    cd ..
    echo "✅ Frontend built successfully!"
else
    echo "⏭️  Skipping frontend build (app will work without it)"
fi

echo ""
echo "📝 Next steps:"
echo ""
echo "1. Create a new Space on Hugging Face:"
echo "   → https://huggingface.co/new-space"
echo "   → Choose SDK: Gradio"
echo "   → Choose Hardware: CPU basic (free)"
echo ""
echo "2. Clone your new Space:"
echo "   git clone https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME"
echo ""
echo "3. Copy files to your Space:"
echo "   cp app.py YOUR_SPACE/"
echo "   cp requirements.txt YOUR_SPACE/"
echo "   cp README_HF.md YOUR_SPACE/README.md"
echo "   cp -r backend YOUR_SPACE/"
echo "   cp -r data YOUR_SPACE/"
if [ "$build_frontend" = "y" ] || [ "$build_frontend" = "Y" ]; then
    echo "   cp -r frontend/dist YOUR_SPACE/frontend/dist"
fi
echo ""
echo "4. Push to Hugging Face:"
echo "   cd YOUR_SPACE"
echo "   git add ."
echo "   git commit -m 'Initial deployment'"
echo "   git push"
echo ""
echo "5. Add your GROQ_API_KEY in Space Settings → Repository secrets"
echo ""
echo "📖 Full deployment guide: See DEPLOYMENT.md"
echo ""
echo "✨ Done! Ready to deploy to Hugging Face Spaces!"
