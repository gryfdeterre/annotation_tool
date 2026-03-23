# 🖼️ Image Annotation Tool

A fast, keyboard-friendly web app to annotate image classification datasets locally.

## Setup

```bash
pip install flask
python app.py
```

Then open http://localhost:5000 in your browser.

## Usage

1. **Input folders** — enter one or more absolute paths (one per line). Subfolders are scanned recursively for images (`.jpg`, `.png`, `.webp`, `.gif`, `.bmp`, `.tiff`).
2. **Output folder** — where the annotated dataset will be saved. Created automatically if missing.
3. **Classes** — one label per line (e.g. `cat`, `dog`, `bird`). The first 9 get keyboard shortcuts (1–9).
4. Click **Start annotating**.

## Annotating

- Click a **class button** or press its **number key** to assign a label and auto-advance.
- Press **S** or click **Skip** to skip an image.
- Use **← →** arrow keys (or buttons) to navigate freely.
- Use the **Jump to** field to go to a specific image number.

## Export

Click **Export dataset** to copy all annotated images into:

```
output_folder/
  cat/
    img1.jpg
    img2.jpg
  dog/
    img3.jpg
  bird/
    img4.jpg
```

Filename collisions are handled automatically (a counter suffix is added).

## Notes

- Only annotated images (not skipped or pending) are exported.
- You can export multiple times; the tool copies files, never moves them.
- The session is in-memory — refreshing the page resets it.
