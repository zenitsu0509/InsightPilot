# 🚀 HF Spaces Deployment Checklist

Use this checklist to ensure smooth deployment to Hugging Face Spaces.

## Pre-Deployment

- [ ] **Get Groq API Key**
  - Sign up at https://console.groq.com/
  - Generate API key
  - Keep it safe for Step 5

- [ ] **Create HF Account**
  - Sign up at https://huggingface.co/join
  - Verify email

- [ ] **Build Frontend (Optional)**
  - Windows: Run `build_frontend.bat`
  - Mac/Linux: Run `./build_frontend.sh`
  - Verify `frontend/dist/` folder exists

## Deployment Steps

### 1. Create New Space
- [ ] Go to https://huggingface.co/new-space
- [ ] Set Space name (e.g., `insightpilot`)
- [ ] Choose SDK: **Gradio**
- [ ] Choose License: **MIT**
- [ ] Choose Hardware: **CPU basic** (free)
- [ ] Set Visibility: Public or Private
- [ ] Click **Create Space**

### 2. Prepare Files
- [ ] Copy/create these files:
  ```
  ✅ app.py
  ✅ requirements.txt
  ✅ README_HF.md → rename to README.md
  ✅ backend/ (entire folder)
  ✅ data/ (optional - sample data)
  ✅ frontend/dist/ (optional - if built)
  ```

### 3. Upload to Space

**Option A: Git (Recommended)**
- [ ] Clone your Space:
  ```bash
  git clone https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME
  cd SPACE_NAME
  ```
- [ ] Copy files into the cloned directory
- [ ] Add files:
  ```bash
  git add .
  git commit -m "Initial deployment of InsightPilot"
  git push
  ```

**Option B: Web Upload**
- [ ] Go to your Space page
- [ ] Click **Files** → **Add file** → **Upload files**
- [ ] Drag and drop all files
- [ ] Commit changes

### 4. Configure Space

- [ ] Go to **Settings** → **Repository secrets**
- [ ] Click **New secret**
- [ ] Add:
  - Name: `GROQ_API_KEY`
  - Value: Your Groq API key
- [ ] Click **Add**

### 5. Monitor Build

- [ ] Go to **Logs** tab
- [ ] Wait for build to complete (3-5 minutes)
- [ ] Check for errors
- [ ] Wait for "Running" status

### 6. Test Deployment

- [ ] Visit your Space URL
- [ ] Test **API Access** tab:
  - [ ] Enter a question
  - [ ] Click Analyze
  - [ ] Verify response
  
- [ ] Test **Upload Dataset** tab:
  - [ ] Upload a CSV
  - [ ] Verify success message
  
- [ ] Test **Analytics Dashboard** (if frontend built):
  - [ ] Check UI loads
  - [ ] Try sample questions
  - [ ] Verify visualizations
  - [ ] Download PDF report

## Post-Deployment

### Optional Enhancements

- [ ] **Add README badge** to your GitHub repo:
  ```markdown
  [![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME)
  ```

- [ ] **Enable Analytics**
  - Settings → Enable analytics
  - Track visitor count

- [ ] **Customize Space**
  - Edit README.md for better description
  - Add screenshots
  - Update emoji/colors in metadata

- [ ] **Set up monitoring**
  - Check Logs regularly
  - Monitor Usage in Settings

### Troubleshooting Common Issues

- [ ] **Build failed**: Check `requirements.txt` syntax
- [ ] **Import errors**: Verify all backend files uploaded
- [ ] **GROQ_API_KEY error**: Check secret name matches exactly
- [ ] **Frontend not loading**: Verify `frontend/dist/` uploaded
- [ ] **Port errors**: App uses 7860 (HF default)
- [ ] **Database errors**: Check file paths in backend

## Success Indicators

✅ Space shows "Running" status
✅ No errors in Logs
✅ Can ask questions and get responses
✅ Can upload CSV files
✅ Can download PDF reports
✅ Visualizations appear correctly

## Share Your Space

Once deployed, share at:
```
https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME
```

Add to:
- [ ] GitHub README
- [ ] LinkedIn
- [ ] Twitter
- [ ] Portfolio

---

**🎉 Congratulations on deploying InsightPilot to Hugging Face Spaces!**

Need help? See `DEPLOYMENT.md` for detailed instructions.
