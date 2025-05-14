from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import uuid
import json
import shutil
import zipfile
import io
import tempfile
import fnmatch
import time
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, send_file, make_response, after_this_request
from flask_cors import CORS

# Initialize Flask application
app = Flask(__name__)
ADMIN_API_KEY = None

# Configure CORS before using any app configuration
CORS(app, resources={r"/*": {"origins": "*",
                            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                            "allow_headers": ["Content-Type", "Authorization", "X-API-Key"]}},
     supports_credentials=True)

# Set up app configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max upload

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Now import application-specific modules that might depend on Flask
from pdf_operations import PdfOperations

# Initialize PDF operations handler
pdf_ops = PdfOperations(app.config['UPLOAD_FOLDER'])

# Storage for file metadata (for operations not yet migrated to PdfOperations)
file_storage = {}
zip_storage = {}

# Import simple_logger if available
try:
    from simple_logger import log_operation as logger_log_operation
except ImportError:
    # Fallback if simple_logger is not available
    def logger_log_operation(api_key, action, description=None, file_id=None, file_name=None, operation_type=None):
        print(f"[LOG] Operation: {action}, File: {file_name}, ID: {file_id}")
        return True

def get_admin_api_key():
    global ADMIN_API_KEY
    if ADMIN_API_KEY:
        return ADMIN_API_KEY

    try:
        import urllib.request
        import json

        # Získať API kľúč z debug endpointu
        backend_url = os.environ.get('BACKEND_URL', 'http://backend:3000/api')
        response = urllib.request.urlopen(f"{backend_url}/pdfLogs/debug-key")
        data = json.loads(response.read().decode('utf-8'))
        ADMIN_API_KEY = data.get('apiKey')
        print(f"Loaded admin API key: {ADMIN_API_KEY[:10]}...")
        return ADMIN_API_KEY
    except Exception as e:
        print(f"Failed to get admin API key: {e}")
        return "admin-api-key-placeholder"

# Helper function to get API key from request
def get_api_key_from_request():
    api_key = None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    # Try to get API key from X-API-Key header
    if 'X-API-Key' in request.headers:
        api_key = request.headers.get('X-API-Key')

    # If not found, try Authorization header (Bearer token)
    elif 'Authorization' in request.headers and request.headers.get('Authorization', '').startswith('Bearer '):
        api_key = request.headers.get('Authorization')[7:]  # Remove "Bearer " prefix

    # If still no API key, use admin key as fallback
    if not api_key:
        api_key = get_admin_api_key()
        print(f"Using admin API key for logging: {api_key[:10] if api_key else 'None'}...")

    return api_key


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'OK', 'message': 'PDF Service is running'})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'pdf' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['pdf']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'File must be a PDF'}), 400

    try:
        # Use the PdfOperations class to handle the upload
        pdf_info = pdf_ops.save_pdf(file)

        # Log the upload operation
        api_key = get_api_key_from_request()
        log_operation(
            api_key=api_key,
            action='upload',
            file_id=pdf_info['id'],
            filename=pdf_info['filename'],
            description=f"Uploaded file: {pdf_info['filename']}"
        )

        # Return metadata (excluding internal filepath)
        response_info = pdf_info.copy()
        response_info.pop('filepath', None)

        # Also store in the old system for compatibility with other functions
        file_storage[pdf_info['id']] = pdf_info

        return jsonify(response_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<file_id>', methods=['GET', 'OPTIONS'])
def download_file(file_id):
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        return response

    # Try to get the file path from PdfOperations
    filepath = pdf_ops.get_file_path(file_id)

    if not filepath and file_id in file_storage:
        filepath = file_storage[file_id]['filepath']

    if not filepath:
        return jsonify({'error': 'File not found'}), 404

    filename = ""
    mime_type = "application/pdf"  # Default MIME type

    if file_id in file_storage:
        filename = file_storage[file_id]['filename']
        if 'type' in file_storage[file_id]:
            mime_type = file_storage[file_id]['type']
    elif file_id in pdf_ops.pdf_storage:
        filename = pdf_ops.pdf_storage[file_id]['filename']
        if 'type' in pdf_ops.pdf_storage[file_id]:
            mime_type = pdf_ops.pdf_storage[file_id]['type']
    else:
        filename = f"download_{file_id}.pdf"

    try:
        # Log the download operation
        api_key = get_api_key_from_request()
        log_operation(
            api_key=api_key,
            action='download',
            file_id=file_id,
            filename=filename,
            description=f"Downloaded file: {filename}"
        )

        # Create a response with the file
        response = make_response(send_file(
            filepath,
            download_name=filename,
            mimetype=mime_type,
            as_attachment=True
        ))

        # Add CORS headers explicitly
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Expose-Headers', 'Content-Disposition')

        return response
    except Exception as e:
        app.logger.error(f"Error sending file {filepath}: {str(e)}")
        return jsonify({'error': f'Error downloading file: {str(e)}'}), 500

@app.route('/download-zip/<zip_id>', methods=['GET', 'OPTIONS'])
def download_zip(zip_id):
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        return response

    try:
        app.logger.info(f"Requesting ZIP file with ID: {zip_id}")

        # Find the ZIP file information
        zip_filepath = None
        zip_filename = f"images_{zip_id}.zip"

        # Method 1: Look in pdf_ops.pdf_storage for direct matches
        if zip_id in pdf_ops.pdf_storage:
            file_info = pdf_ops.pdf_storage[zip_id]
            if 'filepath' in file_info:
                zip_filepath = file_info['filepath']
                zip_filename = file_info.get('filename', zip_filename)
                app.logger.info(f"Found direct match in pdf_storage: {zip_filepath}")

        # Method 2: Look in pdf_ops.pdf_storage for references to zip_id
        if not zip_filepath:
            for file_id, file_info in pdf_ops.pdf_storage.items():
                if 'zip_id' in file_info and file_info['zip_id'] == zip_id:
                    # Check various possible keys where the zip path might be stored
                    if 'zip_path' in file_info:
                        zip_filepath = file_info['zip_path']
                        app.logger.info(f"Found zip_path in pdf_storage: {zip_filepath}")
                        break
                    elif 'zip_filepath' in file_info:
                        zip_filepath = file_info['zip_filepath']
                        app.logger.info(f"Found zip_filepath in pdf_storage: {zip_filepath}")
                        break

        # Method 3: Check the old zip_storage dictionary
        if not zip_filepath and zip_id in zip_storage:
            zip_info = zip_storage[zip_id]
            if 'filepath' in zip_info:
                zip_filepath = zip_info['filepath']
                zip_filename = zip_info.get('filename', zip_filename)
                app.logger.info(f"Found in zip_storage: {zip_filepath}")

        # Method 4: Look for ZIP files in the uploads directory
        if not zip_filepath:
            search_pattern = f"*{zip_id}*.zip"
            for filename in os.listdir(app.config['UPLOAD_FOLDER']):
                if zip_id in filename and filename.endswith('.zip'):
                    zip_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    app.logger.info(f"Found by filesystem search: {zip_filepath}")
                    break

        # If we still couldn't find it, create a new ZIP from the images
        if not zip_filepath:
            app.logger.info(f"ZIP not found, attempting to create it from individual files")

            # Find all image files with this zip_id reference
            image_files = []
            for file_id, file_info in pdf_ops.pdf_storage.items():
                if 'zip_id' in file_info and file_info['zip_id'] == zip_id and 'filepath' in file_info:
                    image_files.append(file_info)

            if image_files:
                # Create a new ZIP file
                zip_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"images_{zip_id}.zip")

                with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for img_info in image_files:
                        img_path = img_info['filepath']
                        img_name = img_info['filename']
                        if os.path.exists(img_path):
                            zip_file.write(img_path, img_name)

                app.logger.info(f"Created new ZIP file: {zip_filepath}")

        # Final check if we have a valid file
        if not zip_filepath or not os.path.exists(zip_filepath):
            app.logger.error(f"ZIP file not found for ID: {zip_id}")
            return jsonify({'error': 'ZIP file not found'}), 404

        app.logger.info(f"Sending ZIP file: {zip_filepath}")

        # Log the download operation
        api_key = get_api_key_from_request()
        log_operation(
            api_key=api_key,
            action='download-zip',
            file_id=zip_id,
            filename=zip_filename,
            description=f"Downloaded ZIP archive: {zip_filename}"
        )

        try:
            # Create a response with the file
            response = make_response(send_file(
                zip_filepath,
                download_name=zip_filename,
                mimetype='application/zip',
                as_attachment=True
            ))

            # Add CORS headers explicitly
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Expose-Headers', 'Content-Disposition')

            return response
        except Exception as e:
            app.logger.error(f"Error sending ZIP file {zip_filepath}: {str(e)}")
            return jsonify({'error': f'Error downloading ZIP file: {str(e)}'}), 500
    except Exception as e:
        app.logger.error(f"General error in download_zip route for ID {zip_id}: {str(e)}")

        # Create a custom error response
        error_response = jsonify({'error': f'Error processing ZIP download request: {str(e)}'})
        error_response.status_code = 500

        # Add CORS headers to error response
        error_response.headers.add('Access-Control-Allow-Origin', '*')

        return error_response

@app.route('/merge', methods=['POST'])
def merge_files():
    # Check if we have at least one file
    if len(request.files) < 1:
        return jsonify({'error': 'Need at least one PDF file to merge'}), 400

    # Get all PDF files from the request
    files = []
    for key in request.files:
        file = request.files[key]
        if file.filename.lower().endswith('.pdf'):
            files.append(file)

    if len(files) < 2:
        return jsonify({'error': 'Need at least two valid PDF files to merge'}), 400

    # Get output filename from request or generate one
    if 'output_filename' in request.form:
        output_filename = secure_filename(request.form['output_filename'])
    else:
        output_filename = f"merged_{len(files)}_files.pdf"

    try:
        pdf_info = pdf_ops.merge_pdfs(files, output_filename)
        file_storage[pdf_info['id']] = pdf_info

        # Get API key for logging
        api_key = get_api_key_from_request()

        # Create detailed description
        filenames = ", ".join([f.filename for f in files])
        description = f"Merged {len(files)} files: {filenames}"

        # Log the operation
        log_success = logger_log_operation(
            api_key=api_key,
            action='merge',
            description=description,
            file_id=pdf_info['id'],
            file_name=pdf_info['filename'],
            operation_type='merge'
        )

        if not log_success:
            print(f"WARNING: Failed to log merge operation with API key: {api_key[:10] if api_key else 'None'}...")

        response_info = pdf_info.copy()
        response_info.pop('filepath', None)
        return jsonify(response_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/split', methods=['POST'])
def split_pdf():
    data = request.json
    if not data or 'file_id' not in data or 'split_method' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400

    file_id = data['file_id']

    # Check if file exists in either system
    if file_id not in pdf_ops.pdf_storage and file_id not in file_storage:
        return jsonify({'error': 'File not found'}), 404

    split_method = data['split_method']
    create_zip = data.get('create_zip', True)

    # Handle ranges for byRanges method
    ranges = None
    if split_method == 'byRanges' and 'ranges' in data:
        ranges = data['ranges']

    # Handle pages for extractPages method
    pages = None
    if split_method == 'extractPages' and 'pages' in data:
        pages = data['pages']
        # Make sure pages are integers
        if isinstance(pages, list):
            pages = [int(p) for p in pages]
        elif isinstance(pages, str):
            # If pages came as a string (e.g., from extractPages field)
            pages = [int(p.strip()) for p in pages.split(',') if p.strip().isdigit()]

    try:
        # Use the PdfOperations class to split PDF
        result_files = pdf_ops.split_pdf(file_id, split_method, ranges, pages, create_zip)

        # Also store in the old system for compatibility
        for file_info in result_files:
            if 'id' in file_info:
                file_storage[file_info['id']] = file_info

            # If there's zip info, store that too
            if 'zip_id' in file_info and 'zip_path' in file_info:
                zip_storage[file_info['zip_id']] = {
                    'id': file_info['zip_id'],
                    'filename': file_info['zip_filename'],
                    'filepath': file_info['zip_path']
                }

        # Get API key for logging
        api_key = get_api_key_from_request()

        # Create a descriptive message based on the split method
        if split_method == 'byPage':
            description = f"Split PDF into {len(result_files)} individual pages"
        elif split_method == 'byRanges':
            description = f"Split PDF into {len(ranges) if ranges else 0} ranges"
        elif split_method == 'extractPages':
            description = f"Extracted {len(pages) if pages else 0} pages from PDF"
        else:
            description = f"Split PDF using method: {split_method}"

        # Get original filename
        original_filename = None
        if file_id in pdf_ops.pdf_storage:
            original_filename = pdf_ops.pdf_storage[file_id].get('filename', 'Unknown')
        elif file_id in file_storage:
            original_filename = file_storage[file_id].get('filename', 'Unknown')

        # Log operation using a representative file (first one)
        if result_files:
            log_operation(
                api_key,
                'split',
                file_id=result_files[0].get('id'),
                filename=result_files[0].get('filename'),
                description=description
            )

        # Return metadata (excluding internal filepaths)
        response_files = []
        for file_info in result_files:
            response_info = file_info.copy()
            response_info.pop('filepath', None)
            if 'zip_path' in response_info:
                response_info.pop('zip_path', None)
            response_files.append(response_info)

        return jsonify({"files": response_files})
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

@app.route('/rotate', methods=['POST'])
def rotate_page():
    data = request.json
    file_id = data.get('file_id')
    page_number = data.get('page', 1)
    rotation = data.get('rotation', 90)

    if not file_id:
        return jsonify({"error": "File ID is required"}), 400

    # Implement rotation in pdf_operations.py first
    return jsonify({"error": "Not implemented yet"}), 501

@app.route('/remove-pages', methods=['POST'])
def remove_pages():
    data = request.json
    file_id = data.get('file_id')
    pages = data.get('pages', [])

    if not file_id:
        return jsonify({"error": "File ID is required"}), 400

    if not pages:
        return jsonify({"error": "Page numbers are required"}), 400

    # Implement page removal in pdf_operations.py first
    return jsonify({"error": "Not implemented yet"}), 501

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)