@echo off
REM Build script for React frontend (Windows) - run this before deploying to HF Spaces

echo Building React frontend for production...

cd frontend

REM Install dependencies
echo Installing dependencies...
call npm install

REM Build for production
echo Building production bundle...
call npm run build

echo Frontend build complete! Output in frontend/dist/
echo Files ready to be served statically by the Gradio app

cd ..
