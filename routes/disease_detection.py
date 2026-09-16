"""
Farm Wise AI – Disease Detection Routes
"""

import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, DiseaseDetection
from ml_models.disease_model import get_disease_model
import uuid

disease_bp = Blueprint("disease", __name__, url_prefix="/disease")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@disease_bp.route("/")
@login_required
def detection():
    recent = DiseaseDetection.query.filter_by(
        user_id=current_user.id
    ).order_by(DiseaseDetection.created_at.desc()).limit(5).all()
    return render_template("disease/detection.html", recent_detections=recent)


@disease_bp.route("/analyze", methods=["POST"])
@login_required
def analyze():
    if "plant_image" not in request.files:
        flash("No image file uploaded.", "danger")
        return redirect(url_for("disease.detection"))

    file = request.files["plant_image"]
    if file.filename == "":
        flash("No file selected.", "danger")
        return redirect(url_for("disease.detection"))

    if not allowed_file(file.filename):
        flash("Invalid file type. Please upload PNG, JPG, or JPEG.", "danger")
        return redirect(url_for("disease.detection"))

    image_bytes = file.read()
    if len(image_bytes) > 16 * 1024 * 1024:
        flash("File too large. Maximum size is 16 MB.", "danger")
        return redirect(url_for("disease.detection"))

    # Save image
    ext = secure_filename(file.filename).rsplit(".", 1)[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)

    with open(filepath, "wb") as f:
        f.write(image_bytes)

    # Run ML prediction
    model = get_disease_model()
    plant_type = request.form.get("plant_type", "Unknown")
    result = model.predict(image_bytes, plant_type=plant_type)

    # Save to DB
    detection = DiseaseDetection(
        user_id=current_user.id,
        image_path=filename,
        plant_type=plant_type or result["plant_type"],
        disease_name=result["disease_name"],
        confidence=result["confidence"],
        symptoms=result["symptoms"],
        treatment=result["treatment"],
        medicine=result["medicine"],
        organic_solution=result["organic_solution"],
        preventive_measures=result["preventive_measures"],
        is_healthy=result["is_healthy"],
    )
    db.session.add(detection)
    db.session.commit()

    recent = DiseaseDetection.query.filter_by(
        user_id=current_user.id
    ).order_by(DiseaseDetection.created_at.desc()).limit(5).all()

    return render_template(
        "disease/detection.html",
        result=result,
        image_filename=filename,
        recent_detections=recent,
    )


@disease_bp.route("/history")
@login_required
def history():
    detections = DiseaseDetection.query.filter_by(
        user_id=current_user.id
    ).order_by(DiseaseDetection.created_at.desc()).all()
    return render_template("disease/history.html", detections=detections)
