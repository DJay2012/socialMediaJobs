# Testing Folder

This folder contains all the improved versions and test files created during the development process. These are kept for testing and reference purposes.

## 📁 Contents

### **Test Scripts**
- `test_improved_system.py` - Tests the improved configuration system
- `test_new_structure.py` - Tests the new folder structure

### **Improved Versions (for reference)**
- `youtube_scraper_improved.py` - Improved YouTube scraper
- `twitter_scraper_improved.py` - Improved Twitter scraper
- `run_social_media_jobs.sh` - Linux/Mac runner script
- `run_social_media_jobs.ps1` - Windows PowerShell runner script

### **Setup and Documentation**
- `setup.py` - Setup script for the improved system
- `environment_template.txt` - Environment variables template
- `README_IMPROVED.md` - Documentation for improved system
- `README_NEW_STRUCTURE.md` - Documentation for new structure

## 🧪 How to Use for Testing

### **Test the New Structure**
```bash
cd testing
python test_new_structure.py
```

### **Test Individual Improved Scrapers**
```bash
cd testing
python youtube_scraper_improved.py
python twitter_scraper_improved.py
```

### **Run Setup Script**
```bash
cd testing
python setup.py
```

## 🔄 Current vs Testing Versions

| **Current (Root)** | **Testing Version** | **Purpose** |
|-------------------|-------------------|-------------|
| `main.py` | `run_social_media_jobs.ps1` | Job runner |
| `youtube/youtube_scraper.py` | `youtube_scraper_improved.py` | YouTube scraping |
| `twitter/twitter_scraper.py` | `twitter_scraper_improved.py` | Twitter scraping |
| `config.py` | `environment_template.txt` | Configuration |

## 📊 Benefits of Testing Folder

- ✅ **Safe Testing** - Test new features without affecting production
- ✅ **Version Control** - Keep track of different implementations
- ✅ **Reference** - Compare old vs new approaches
- ✅ **Development** - Continue improving the system
- ✅ **Documentation** - Keep all related docs together

## 🚀 Development Workflow

1. **Test new features** in this folder first
2. **Compare performance** between versions
3. **Document changes** before moving to production
4. **Keep backups** of working versions

## 📅 Created

September 10, 2025 - During project reorganization
