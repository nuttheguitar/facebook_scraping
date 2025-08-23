# Facebook UI Screenshot Scraper

A specialized Facebook scraper that captures **UI screenshots** of posts with **content expansion** for OCR (Optical Character Recognition) processing.

## 🎯 **Purpose**

This scraper is designed specifically for:
- **OCR Processing**: Capture screenshots that can be processed by OCR tools
- **Content Expansion**: Automatically click "Read More" buttons to show full text
- **UI Preservation**: Maintain the exact visual layout of Facebook posts
- **Complete Content**: Ensure all text is visible before screenshot capture

## 🚀 **Key Features**

- **Automatic Content Expansion**: Clicks "Read More", "See More", "Show More" buttons
- **UI Screenshot Capture**: Takes screenshots of each expanded post
- **Content Validation**: Ensures posts are fully expanded before capture
- **Comment Expansion**: Also expands comment sections when available
- **Smart Scrolling**: Scrolls posts into optimal view before capture
- **Cropped Screenshots**: Captures only the post content area (when PIL is available)

## 🔄 **How It Works**

1. **Navigate to Target**: Goes to specified Facebook page/group
2. **Find Posts**: Locates all visible post elements
3. **Expand Content**: Clicks all "Read More" buttons to show full text
4. **Scroll into View**: Ensures each post is properly positioned
5. **Capture Screenshot**: Takes screenshot of the expanded post
6. **Save & Process**: Stores screenshot and metadata for OCR processing

## 📋 **Requirements**

- Python 3.7+
- Chrome browser
- ChromeDriver
- PIL (Pillow) for image cropping (optional but recommended)
- Required Python packages (see `requirements.txt`)

## 🛠️ **Installation**

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Pillow for image cropping (recommended):
```bash
pip install Pillow
```

3. Ensure Chrome browser is installed

## 🚀 **Usage**

### Basic Usage

```python
from strategies.facebook_scraper import FacebookUIScraper

# Initialize scraper
scraper = FacebookUIScraper(
    db_path="facebook_ui_posts.db",
    fast_mode=False  # Set to True for faster scraping
)

# Setup Chrome driver
scraper.setup_driver(headless=False)  # Set to True for headless mode

# Scrape posts and capture screenshots
target_url = "https://www.facebook.com/groups/your_group_id"
max_posts = 10
posts_data = scraper.scrape_facebook_posts(target_url, max_posts)

# Save results
scraper.save_posts_to_database(posts_data)
scraper.save_posts_to_json(posts_data, "ui_screenshots.json")

# Clean up
scraper.close()
```

### Run Example Script

```bash
python example_ui_screenshot.py
```

## 📁 **Output Structure**

### Screenshots Directory
```
facebook_screenshots/
├── post_001_20240115_143022.png
├── post_002_20240115_143045.png
├── post_003_20240115_143108.png
└── ...
```

### Post Data Structure
```json
{
  "post_id": "post_1705312200_1234",
  "author": "John Doe",
  "content_preview": "Beautiful room available for rent...",
  "timestamp": "2 hours ago",
  "post_url": "https://www.facebook.com/permalink/...",
  "screenshot_path": "facebook_screenshots/post_001_20240115_143022.png",
  "screenshot_timestamp": "2024-01-15 14:30:22",
  "likes_count": 42,
  "comments_count": 12,
  "shares_count": 3,
  "scraped_at": "2024-01-15 14:30:22",
  "scraping_method": "ui_screenshot",
  "content_expanded": true
}
```

## 🔍 **Content Expansion Features**

### Automatic Button Detection
The scraper automatically finds and clicks:
- **"See more"** buttons
- **"Read more"** buttons  
- **"Show more"** buttons
- **"..."** (ellipsis) indicators
- **"View more comments"** buttons

### Expansion Process
1. **Primary Expansion**: Clicks main "Read More" buttons
2. **Nested Expansion**: Handles nested/cascading content
3. **Comment Expansion**: Expands comment sections
4. **Validation**: Waits for content to fully expand
5. **Screenshot**: Captures the fully expanded post

## 🖼️ **Screenshot Capture**

### Capture Process
1. **Position Post**: Scrolls post into optimal view
2. **Full Page Screenshot**: Captures entire page
3. **Element Cropping**: Crops to just the post area (when PIL available)
4. **File Naming**: `post_001_20240115_143022.png`
5. **Quality**: High-resolution PNG format

### Screenshot Features
- **Full Content**: All expanded text is visible
- **Proper Layout**: Maintains Facebook's visual design
- **Comment Sections**: Includes expanded comments
- **Image Content**: Shows any images in the post
- **Engagement Info**: Likes, comments, shares visible

## ⚙️ **Configuration Options**

### Scraper Options
- **fast_mode**: Enable for quicker processing
- **headless**: Run Chrome in background mode
- **screenshot_dir**: Custom directory for screenshots

### Chrome Options
- **Window Size**: Optimized for 1920x1080 screenshots
- **Human Behavior**: Simulates natural browsing patterns
- **Profile Usage**: Can use existing Chrome profiles

## 🔧 **OCR Integration**

### Screenshot Preparation
Each screenshot is optimized for OCR:
- **Full Text Visible**: No truncated content
- **High Resolution**: Clear text for OCR engines
- **Proper Contrast**: Facebook's default styling works well
- **Consistent Format**: Uniform layout across all posts

### OCR Processing Workflow
1. **Capture Screenshots**: Use this scraper
2. **Process Images**: Feed to OCR engine (Tesseract, Azure, etc.)
3. **Extract Text**: Get full post content as text
4. **Post-Process**: Clean and structure the extracted text

### Recommended OCR Tools
- **Tesseract**: Open-source OCR engine
- **Azure Computer Vision**: Cloud-based OCR service
- **Google Cloud Vision**: High-accuracy OCR
- **AWS Textract**: Document and text extraction

## 📊 **Performance & Statistics**

### Scraping Statistics
```python
stats = scraper.get_scraping_stats()
print(f"Screenshots captured: {stats['screenshot_stats']['screenshots_found']}")
print(f"Total size: {stats['screenshot_stats']['total_size_mb']:.2f} MB")
print(f"Content expansion: {stats['content_expansion']}")
```

### Screenshot Summary
```python
summary = scraper.get_screenshot_summary()
print(f"Files: {summary['screenshot_files']}")
print(f"Directory: {summary['screenshot_dir']}")
```

## 🚨 **Important Notes**

### Rate Limiting
- Facebook may rate-limit excessive requests
- Use `fast_mode=False` for more natural behavior
- Consider adding delays between scraping sessions

### Authentication
- **Recommended**: Authenticate with Facebook for better access
- **Public Access**: Can scrape public posts without login
- **Session Management**: Maintains login during scraping

### Legal Considerations
- Respect Facebook's Terms of Service
- Only capture publicly available content
- Use for legitimate research/analysis purposes
- Be aware of Facebook's anti-automation measures

## 🔧 **Troubleshooting**

### Common Issues

1. **Screenshots Not Capturing**
   - Check if Chrome driver is working
   - Verify target page is accessible
   - Ensure posts are visible on page

2. **Content Not Expanding**
   - Facebook may have changed button selectors
   - Check if "Read More" buttons are visible
   - Try authenticating with Facebook

3. **Poor Screenshot Quality**
   - Ensure Chrome window is properly sized
   - Check if post is fully in view
   - Verify no overlapping elements

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 **Performance Tips**

1. **Batch Processing**: Process multiple pages in sequence
2. **Fast Mode**: Use `fast_mode=True` for bulk operations
3. **Headless Mode**: Use `headless=True` for server environments
4. **Parallel Processing**: Run multiple scrapers on different targets

## 🔮 **Future Enhancements**

- **Video Screenshots**: Capture video post thumbnails
- **Dynamic Content**: Handle JavaScript-heavy posts
- **Batch OCR**: Integrated OCR processing
- **Quality Optimization**: Enhanced image processing
- **Multi-Platform**: Support for other social media platforms

## 📝 **Example OCR Workflow**

```python
# 1. Capture screenshots
posts_data = scraper.scrape_facebook_posts(target_url, 20)

# 2. Process with OCR (example using Tesseract)
import pytesseract
from PIL import Image

for post in posts_data:
    screenshot_path = post['screenshot_path']
    image = Image.open(screenshot_path)
    
    # Extract text using OCR
    text = pytesseract.image_to_string(image)
    
    # Store OCR results
    post['ocr_text'] = text
    post['ocr_processed'] = True

# 3. Save OCR results
scraper.save_posts_to_json(posts_data, "posts_with_ocr.json")
```

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 **License**

This project is for educational and research purposes. Please respect Facebook's Terms of Service and applicable laws when using this scraper.

## 🆘 **Support**

For issues and questions:
1. Check the troubleshooting section
2. Review the example scripts
3. Check browser console for errors
4. Verify Facebook page accessibility
