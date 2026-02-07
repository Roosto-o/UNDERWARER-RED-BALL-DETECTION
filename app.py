from flask import Flask, render_template, request, flash, redirect
from ultralytics import YOLO
import os
from PIL import Image
import numpy as np
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change-me")

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

model = YOLO("best.pt")  # Load model once


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("image")
        if not file or file.filename == "":
            flash("No file selected")
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash("File type not allowed")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)

        try:
            results = model(path)

            # Try to get the annotated image as a numpy array and overwrite the saved image
            annotated = None
            if len(results) > 0:
                annotated = results[0].plot()

            if isinstance(annotated, np.ndarray):
                # Convert to PIL Image and save (assume RGB)
                img = Image.fromarray(annotated)
                img.save(path)
            else:
                # Fallback: let the results.save() write outputs to the default folder
                try:
                    results.save()
                except Exception:
                    pass

            return render_template("index.html", img=path)

        except Exception as e:
            flash(f"Error processing image: {e}")
            return redirect(request.url)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
