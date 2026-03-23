import os
import sys
import shutil
import json
import base64
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}

# In-memory state
state = {
    "input_folders": [],
    "output_folder": "",
    "classes": [],
    "images": [],       # list of {path, status, assigned_class}
    "current_index": 0,
}

def scan_images(folders):
    images = []
    for folder in folders:
        p = Path(folder)
        if p.exists() and p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.suffix.lower() in IMAGE_EXTENSIONS:
                    images.append({"path": str(f), "status": "pending", "assigned_class": None})
    return images

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/state", methods=["GET"])
def get_state():
    total = len(state["images"])
    done = sum(1 for i in state["images"] if i["status"] == "done")
    skipped = sum(1 for i in state["images"] if i["status"] == "skipped")
    return jsonify({
        "input_folders": state["input_folders"],
        "output_folder": state["output_folder"],
        "classes": state["classes"],
        "total": total,
        "done": done,
        "skipped": skipped,
        "current_index": state["current_index"],
    })

@app.route("/api/setup", methods=["POST"])
def setup():
    data = request.json
    folders = [f.strip() for f in data.get("input_folders", []) if f.strip()]
    output = data.get("output_folder", "").strip()
    classes = [c.strip() for c in data.get("classes", []) if c.strip()]

    missing = [f for f in folders if not Path(f).exists()]
    if missing:
        return jsonify({"error": f"Folders not found: {', '.join(missing)}"}), 400
    if not output:
        return jsonify({"error": "Output folder is required"}), 400
    if not classes:
        return jsonify({"error": "At least one class is required"}), 400

    state["input_folders"] = folders
    state["output_folder"] = output
    state["classes"] = classes
    state["images"] = scan_images(folders)
    state["current_index"] = 0

    if not state["images"]:
        return jsonify({"error": "No images found in the specified folders"}), 400

    return jsonify({"success": True, "total": len(state["images"])})

@app.route("/api/image/<int:index>", methods=["GET"])
def get_image(index):
    if index < 0 or index >= len(state["images"]):
        return jsonify({"error": "Index out of range"}), 404
    img = state["images"][index]
    path = Path(img["path"])
    ext = path.suffix.lower().lstrip(".")
    mime_map = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "gif": "gif",
                "bmp": "bmp", "webp": "webp", "tiff": "tiff", "tif": "tiff"}
    mime = f"image/{mime_map.get(ext, 'jpeg')}"
    with open(img["path"], "rb") as f:
        data = base64.b64encode(f.read()).decode()
    return jsonify({
        "index": index,
        "path": img["path"],
        "filename": path.name,
        "folder": str(path.parent),
        "status": img["status"],
        "assigned_class": img["assigned_class"],
        "data": f"data:{mime};base64,{data}",
        "total": len(state["images"]),
    })

@app.route("/api/annotate", methods=["POST"])
def annotate():
    data = request.json
    index = data.get("index")
    cls = data.get("class")
    skip = data.get("skip", False)

    if index is None or index < 0 or index >= len(state["images"]):
        return jsonify({"error": "Invalid index"}), 400

    img = state["images"][index]

    if skip:
        img["status"] = "skipped"
        img["assigned_class"] = None
    else:
        if cls not in state["classes"]:
            return jsonify({"error": "Invalid class"}), 400
        img["status"] = "done"
        img["assigned_class"] = cls

    # Advance to next pending
    next_idx = index + 1
    while next_idx < len(state["images"]) and state["images"][next_idx]["status"] == "done":
        next_idx += 1

    state["current_index"] = next_idx if next_idx < len(state["images"]) else index

    done = sum(1 for i in state["images"] if i["status"] == "done")
    return jsonify({"success": True, "next_index": state["current_index"], "done": done})

@app.route("/api/export", methods=["POST"])
def export():
    output = Path(state["output_folder"])
    output.mkdir(parents=True, exist_ok=True)

    # Create class subfolders
    for cls in state["classes"]:
        (output / cls).mkdir(exist_ok=True)

    copied = 0
    errors = []
    for img in state["images"]:
        if img["status"] == "done" and img["assigned_class"]:
            src = Path(img["path"])
            dst_dir = output / img["assigned_class"]
            dst = dst_dir / src.name
            # Handle name collisions
            if dst.exists():
                stem = src.stem
                suffix = src.suffix
                counter = 1
                while dst.exists():
                    dst = dst_dir / f"{stem}_{counter}{suffix}"
                    counter += 1
            try:
                shutil.copy2(src, dst)
                copied += 1
            except Exception as e:
                errors.append(str(e))

    summary = {}
    for cls in state["classes"]:
        summary[cls] = sum(1 for i in state["images"] if i["assigned_class"] == cls)

    return jsonify({
        "success": True,
        "copied": copied,
        "output_folder": str(output),
        "summary": summary,
        "errors": errors,
    })

@app.route("/api/reset", methods=["POST"])
def reset():
    state.update({"input_folders": [], "output_folder": "", "classes": [],
                  "images": [], "current_index": 0})
    return jsonify({"success": True})

@app.route("/api/jump", methods=["POST"])
def jump():
    index = request.json.get("index", 0)
    if 0 <= index < len(state["images"]):
        state["current_index"] = index
        return jsonify({"success": True})
    return jsonify({"error": "Invalid index"}), 400

if __name__ == "__main__":
    print("\n🖼️  Image Annotation Tool")
    print("━" * 40)
    print("Open: http://localhost:5000")
    print("━" * 40 + "\n")
    app.run(debug=False, port=5000)
