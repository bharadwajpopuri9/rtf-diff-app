# RTF Comparison Web Application

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/YOUR_USERNAME/rtf-diff-app)

A Flask web application for comparing RTF files with intelligent boilerplate filtering and side-by-side diff viewing.

## 🚀 Quick Deploy to Render

1. **Fork this repository** to your GitHub account
2. **Click the "Deploy to Render" button** above
3. **Configure your service** (optional - defaults work fine)
4. **Deploy!** Your app will be live in minutes

## ✨ Features

- **Drag & Drop Upload**: Upload RTF files with visual feedback
- **Smart Filtering**: Automatically removes SAS output headers and timestamps
- **Side-by-Side Diffs**: Beautiful HTML diff viewer with syntax highlighting
- **Multiple Formats**: Word-level and line-level comparison modes
- **Export Options**: Download HTML reports and CSV summaries
- **Production Ready**: Secure, scalable, and monitored

## 🛠 Local Development

```bash
git clone https://github.com/YOUR_USERNAME/rtf-diff-app.git
cd rtf-diff-app
chmod +x run.sh
./run.sh
```

Visit http://localhost:5000

## 📝 Usage

1. Upload one source/reference RTF file
2. Upload one or more comparison RTF files
3. Configure comparison options (ignore case, punctuation, etc.)
4. View results and download reports

## 🔧 Configuration

The app works out-of-the-box with default settings. For customization:

- **File Limits**: 15MB per file, 20 files maximum
- **Formats**: Only RTF files supported
- **Security**: Automatic file validation and cleanup

## 📊 Deployment Options

- **Render** (recommended): One-click deployment
- **Heroku**: `git push heroku main`
- **Docker**: `docker-compose up`
- **Self-hosted**: See full documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - feel free to use for any purpose.

---

**Perfect for:** SAS output comparison, document versioning, regulatory submissions, and any RTF file comparison needs.
