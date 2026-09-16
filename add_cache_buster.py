import os
import glob

pages_dir = r"D:\Akshay\Documents\scratch\farm-wise-ai\static\pages"

for file_path in glob.glob(os.path.join(pages_dir, "*.html")):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Add cache busters
    content = content.replace('"/static/css/main.css?v=3"', '"/static/css/main.css?v=4"')
    content = content.replace('"/static/js/main.js?v=3"', '"/static/js/main.js?v=4"')
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
        
print("Added cache busters v4 to all HTML files.")
