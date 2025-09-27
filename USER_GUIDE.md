# JIM AI - User Guide for Non-Technical Users

## 🎯 Three Easy Ways to Use JIM AI

### Method 1: Desktop Application (Recommended for Beginners)
**Best for**: Complete beginners, visual interface preferred

1. **Double-click**: `Start_GUI_Launcher.command`
2. **Wait**: GUI interface opens automatically
3. **For small files**: Click "🌐 Open Web Interface"
4. **For large data**: Click "Browse..." → Select your folder → Click "🚀 Process Large Data"

### Method 2: Web Interface Only
**Best for**: Users comfortable with web browsers

1. **Double-click**: `Start_JIM_AI.command`
2. **Open browser**: Go to http://localhost:8080
3. **Upload files**: Click "📁 Upload Case Files"
4. **Choose method**:
   - **📄 Select Files**: For individual documents
   - **📁 Select Folder**: For complete cell phone extractions

### Method 3: Complete Manual Control
**Best for**: Technical users who want full control

1. **Open Terminal**: Applications → Utilities → Terminal
2. **Navigate**: `cd /Users/jonscott/Downloads/jim-ai-complete`
3. **Start web**: `source jim-ai-env/bin/activate && python3 app.py`
4. **Process large data**: `python3 large-data-processor.py /path/to/data`

---

## 📱 Cell Phone Data - Step by Step

### What You Have:
- iPhone extraction folder (from Cellebrite, Oxygen, etc.)
- Android extraction folder
- Individual .db files (messages, contacts, calls)
- ZIP files containing phone data

### Steps:

#### Option A: Using Desktop Application
1. **Double-click**: `Start_GUI_Launcher.command`
2. **Wait for GUI**: Desktop application opens
3. **Click "Browse..."**: Select your cell phone folder
4. **Click "🚀 Process Large Data"**: Processing starts automatically
5. **Wait**: Progress shown in real-time (may take 3-6 hours for large data)
6. **When complete**: Click "🌐 Open Web Interface" to query data

#### Option B: Using Web Interface
1. **Double-click**: `Start_JIM_AI.command`
2. **Open browser**: http://localhost:8080
3. **Click**: "📁 Upload Case Files"
4. **Click**: "📁 Select Folder"
5. **Choose**: Your cell phone extraction folder
6. **Wait**: Files upload and process automatically

---

## 📄 Documents and Evidence Files

### What You Have:
- PDF reports
- Word documents
- Photos and images
- Individual database files
- Text files and logs

### Steps:
1. **Start JIM AI**: Double-click `Start_JIM_AI.command`
2. **Open browser**: http://localhost:8080
3. **Click**: "📁 Upload Case Files"
4. **Either**:
   - **Drag & drop** files into the upload area
   - **Click "📄 Select Files"** to browse for files
5. **Upload**: Files process automatically (5-15 minutes)

---

## 🔍 Querying Your Data

Once your data is processed, you can ask questions like:

### Text Messages & Communications:
- *"What messages were sent on March 15th?"*
- *"Show me WhatsApp conversations about drugs"*
- *"Find deleted text messages"*
- *"What calls were made after midnight?"*

### Contacts & People:
- *"List all contacts with Miami addresses"*
- *"Who has phone number 555-0123?"*
- *"Show me contacts added in the last month"*

### Photos & Media:
- *"What photos were taken on Friday night?"*
- *"Show me images with GPS locations"*
- *"Find photos taken at the crime scene address"*

### General Evidence:
- *"What evidence mentions the suspect's name?"*
- *"Timeline of events on the day of the incident"*
- *"Show me all files related to the case"*

---

## ⚠️ Troubleshooting

### "Nothing happens when I double-click"
**Fix**: Right-click the file → "Open With" → "Terminal"

### "Permission denied"
**Fix**: In Terminal, type: `chmod +x Start_JIM_AI.command`

### "Web page won't load"
**Solutions**:
1. Wait 30 seconds after starting
2. Try http://127.0.0.1:8080 instead
3. Check if another program is using port 8080

### "Upload failed" or "Processing failed"
**Check**:
1. Internet connection (required for AWS)
2. File sizes (100MB limit for web interface)
3. Available disk space (need 3x your data size)
4. Try desktop application instead

### "Running out of space"
**Solutions**:
1. Clean up `/tmp/claude/` folder
2. Use external drive for processing
3. Process data in smaller batches

---

## 📊 What to Expect

### File Size Limits:
| Method | Individual Files | Total Upload | Use Case |
|--------|-----------------|--------------|----------|
| Web Interface | 100MB | 500MB | Documents, small databases |
| Desktop App | No limit | No limit | Complete phone extractions |
| Drag & Drop | 100MB | 500MB | Mixed evidence files |

### Processing Times:
| Data Size | Processing | Upload | Ingestion | Total |
|-----------|------------|--------|-----------|-------|
| 100MB | 1-2 min | 2-5 min | 5-10 min | 8-17 min |
| 1GB | 3-5 min | 5-15 min | 10-20 min | 18-40 min |
| 10GB | 15-30 min | 30-60 min | 20-40 min | 1-2 hours |
| 100GB | 2-4 hours | 3-6 hours | 1-2 hours | 6-12 hours |

### What Gets Processed:
- **SQLite databases** → Converted to searchable text
- **ZIP/Archive files** → Extracted and contents processed
- **Large files** → Split into smaller searchable chunks
- **Photos** → Metadata extracted (GPS, timestamps)
- **Documents** → Full text made searchable

---

## 🆘 Getting Help

### Check System Status:
1. **In Desktop App**: Click "📊 Check Status"
2. **In Web Interface**: Look for green "Connected" indicator
3. **Manual check**: Visit http://localhost:8080/api/status

### Common Questions:

**Q: How do I know when processing is complete?**
A: You'll see "✅ Documents successfully processed" message and can start asking questions.

**Q: Can I upload more data later?**
A: Yes! Just repeat the upload process. New data will be added to existing data.

**Q: What if I close the application?**
A: Your uploaded data stays in the cloud. Just restart JIM AI and continue querying.

**Q: Is my data secure?**
A: Yes, data is encrypted in AWS S3 and only accessible through your local application.

**Q: Can I use this offline?**
A: No, internet connection required for AWS cloud processing and AI analysis.

---

## 🎓 Quick Start Checklist

- [ ] **Double-click** `Start_GUI_Launcher.command` (easiest)
- [ ] **OR double-click** `Start_JIM_AI.command` (web only)
- [ ] **Wait** for application to start (30 seconds)
- [ ] **Upload your data** using drag & drop or folder selection
- [ ] **Wait** for processing to complete (varies by data size)
- [ ] **Start asking questions** about your evidence!

### First Upload Recommendations:
1. **Start small**: Try with a few documents first
2. **Test queries**: Ask simple questions to verify data is searchable
3. **Then go big**: Upload your complete cell phone extraction
4. **Be patient**: Large datasets take time but results are worth it

---

**Need more help?** See the technical guides:
- `LARGE_DATA_GUIDE.md` - Detailed technical information
- `QUICK_START.md` - Command reference
- `PROJECT_SUMMARY.md` - System overview

**Your forensic analysis just got 100x easier!** 🚀