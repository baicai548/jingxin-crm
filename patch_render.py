with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add os import if not exists
if "import os" not in content:
    content = "import os\n" + content

# Update the run line to use PORT env variable
old_line = '    app.run(debug=True,host="0.0.0.0",port=9999)'
new_line = '    port = int(os.environ.get("PORT", 9999))\n    app.run(debug=False,host="0.0.0.0",port=port)'
content = content.replace(old_line, new_line)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)
print("[OK] app.py updated for Render")