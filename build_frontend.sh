#!/bin/bash
# Build script for React frontend - run this before deploying to HF Spaces

echo "🔨 Building React frontend for production..."

cd frontend

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build for production
echo "🏗️  Building production bundle..."
npm run build

echo "✅ Frontend build complete! Output in frontend/dist/"
echo "📁 Files ready to be served statically by the Gradio app"

cd ..
