from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
from werkzeug.utils import secure_filename
import tempfile
from pdf_operations import PdfOperations
from watermark_operations import WatermarkOperations
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Register Swagger UI blueprint
SWAGGER_URL = '/api-docs'
API_URL = '/static/swagger.json'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "PDF Editor Python API"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

@app.route('/static/swagger.json')
def serve_swagger():
    return send_file('swagger.json')

# Initialize operations
pdf_ops = PdfOperations(UPLOAD_FOLDER)
watermark_ops = WatermarkOperations(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK", "message": "Python PDF Service is running"})

@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'pdf' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['pdf']

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        try:
            pdf_info = pdf_ops.save_pdf(file)
            return jsonify(pdf_info)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid file type"}), 400

@app.route('/merge', methods=['POST'])
def merge_pdfs():
    files = []
    output_filename = request.form.get('output_filename', 'merged.pdf')

    # Collect all files
    i = 1
    while f'file{i}' in request.files:
        file = request.files[f'file{i}']
        if file and file.filename != '' and allowed_file(file.filename):
            files.append(file)
        i += 1

    if len(files) < 2:
        return jsonify({"error": "At least two PDF files are required"}), 400

    try:
        result = pdf_ops.merge_pdfs(files, output_filename)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/split', methods=['POST'])
def split_pdf():
    data = request.json
    file_id = data.get('file_id')
    split_method = data.get('split_method', 'byPage')
    ranges = data.get('ranges', [])
    pages = data.get('pages', [])
    create_zip = data.get('create_zip', True)

    if not file_id:
        return jsonify({"error": "File ID is required"}), 400

    try:
        result_files = pdf_ops.split_pdf(file_id, split_method, ranges, pages, create_zip)
        return jsonify({"files": result_files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/watermark', methods=['POST'])
def add_watermark():
    data = request.json
    file_id = data.get('file_id')
    text = data.get('text')
    opacity = data.get('opacity', 0.3)
    size = data.get('size', 36)
    color = data.get('color', 'gray')
    angle = data.get('angle', 45)
    pages = data.get('pages', None)

    if not file_id:
        return jsonify({"error": "File ID is required"}), 400

    if not text:
        return jsonify({"error": "Watermark text is required"}), 400

    try:
        # Get source file info
        file_info = pdf_ops.pdf_storage.get(file_id)
        if not file_info:
            return jsonify({"error": "File not found"}), 404

        source_path = file_info['filepath']

        # Create output file
        output_id = str(uuid.uuid4())
        output_filename = f"watermarked_{output_id}.pdf"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

        # Apply watermark
        watermark_ops.add_watermark(
            source_path,
            output_path,
            text,
            opacity,
            size,
            color,
            angle,
            pages
        )

        # Create file info
        result_info = {
            "id": output_id,
            "filename": output_filename,
            "filepath": output_path
        }

        # Add to storage
        pdf_ops.pdf_storage[output_id] = result_info

        return jsonify(result_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<file_id>', methods=['GET'])
def download_pdf(file_id):
    filepath = pdf_ops.get_file_path(file_id)

    if not filepath:
        return jsonify({"error": "File not found"}), 404

    filename = os.path.basename(filepath).split('_', 1)[1] if '_' in os.path.basename(filepath) else os.path.basename(filepath)

    try:
        return send_file(
            filepath,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download-zip/<zip_id>', methods=['GET'])
def download_zip(zip_id):
    zip_path = pdf_ops.get_zip_path(zip_id)

    if not zip_path:
        return jsonify({"error": "Zip file not found"}), 404

    filename = os.path.basename(zip_path)

    try:
        return send_file(
            zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)