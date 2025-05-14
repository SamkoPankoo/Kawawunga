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
        return jsonify({'error': str(e)}), 500

@app.route('/rotate', methods=['POST'])
def rotate_pdf():
    data = request.json
    if not data or 'file_id' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400

    file_id = data['file_id']

    # Check if file exists in either system
    if file_id not in pdf_ops.pdf_storage and file_id not in file_storage:
        return jsonify({'error': 'File not found'}), 404

    # Get rotation parameters
    angle = data.get('rotation', 90)  # For compatibility with frontend
    if 'angle' in data:  # If explicit angle is provided
        angle = data['angle']

    # Handle page selection
    pages = None
    if 'page' in data:  # Single page
        pages = [int(data['page'])]
    elif 'pages' in data:  # Multiple pages
        pages = data['pages']

    try:
        # Use the PdfOperations class to rotate PDF
        pdf_info = pdf_ops.rotate_pdf(file_id, angle, pages)

        # Also store in the old system for compatibility
        file_storage[pdf_info['id']] = pdf_info

        # Get API key for logging
        api_key = get_api_key_from_request()

        # Get original filename for better description
        original_filename = "unknown"
        if file_id in pdf_ops.pdf_storage:
            original_filename = pdf_ops.pdf_storage[file_id].get('filename', 'unknown')

        # Create detailed description
        page_desc = "all pages"
        if pages:
            if len(pages) == 1:
                page_desc = f"page {pages[0]}"
            else:
                page_desc = f"{len(pages)} pages"

        description = f"Rotated {page_desc} by {angle}° in {original_filename}"

        # Log with full details
        log_success = logger_log_operation(
            api_key=api_key,
            action='rotate',
            description=description,
            file_id=pdf_info['id'],
            file_name=pdf_info['filename'],
            operation_type='rotate'
        )

        if not log_success:
            print("WARNING: Failed to log rotate operation")

        # Return metadata (excluding internal filepath)
        response_info = pdf_info.copy()
        response_info.pop('filepath', None)

        return jsonify(response_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/watermark', methods=['POST'])
def add_watermark():
    data = request.json
    if not data or 'file_id' not in data or 'text' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400

    file_id = data['file_id']

    # Check if file exists in either system
    if file_id not in pdf_ops.pdf_storage and file_id not in file_storage:
        return jsonify({'error': 'File not found'}), 404

    # Get watermark parameters
    watermark_text = data['text']
    opacity = data.get('opacity', 0.3)

    # Handle color (could be an object with a 'value' property from frontend)
    if isinstance(data.get('color'), dict) and 'value' in data['color']:
        color = data['color']['value']
    else:
        color = data.get('color', 'gray')

    size = data.get('size', 36)

    # Handle angle (could be string from frontend)
    angle = data.get('angle', 45)
    if isinstance(angle, str):
        try:
            angle = int(angle)
        except ValueError:
            angle = 45

    # Handle page selection
    page_selection = data.get('pageSelection', 'all')
    pages = data.get('pages', [])

    # If no specific pages were provided but we have custom selection method
    if not pages:
        if page_selection == 'current' and 'currentPage' in data:
            pages = [int(data['currentPage'])]
        elif page_selection == 'range' and 'pageRange' in data:
            start = int(data['pageRange'].get('from', 1))
            end = int(data['pageRange'].get('to', 1))
            pages = list(range(start, end + 1))
        elif page_selection == 'custom' and 'customPages' in data:
            # Parse custom pages (comma-separated list)
            pages = [int(p.strip()) for p in data['customPages'].split(',') if p.strip().isdigit()]

    try:
        # Use the PdfOperations class to add watermark
        pdf_info = pdf_ops.add_watermark(file_id, watermark_text, opacity, color, size, angle, pages)

        # Also store in the old system for compatibility
        file_storage[pdf_info['id']] = pdf_info

        # Get API key for logging
        api_key = get_api_key_from_request()

        # Create a descriptive message
        page_desc = "all pages"
        if pages:
            if len(pages) == 1:
                page_desc = f"page {pages[0]}"
            else:
                page_desc = f"{len(pages)} pages"

        description = f"Added watermark '{watermark_text}' to {page_desc}"

        # Log operation
        log_operation(
            api_key,
            'watermark',
            pdf_info['id'],
            pdf_info['filename'],
            description
        )

        # Return metadata (excluding internal filepath)
        response_info = pdf_info.copy()
        response_info.pop('filepath', None)

        return jsonify(response_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


    try:
        return send_file(
            filepath,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/protect', methods=['POST'])
def protect_pdf_route():
    data = request.json
    if not data or 'file_id' not in data or 'user_password' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400

    file_id = data['file_id']
    user_password = data['user_password']
    owner_password = data.get('owner_password', user_password)
    allow_printing = data.get('allow_printing', True)
    allow_copying = data.get('allow_copying', True)
    preview_only = data.get('preview_only', False)

    try:
        # Use the PdfOperations class to protect PDF
        pdf_info = pdf_ops.protect_pdf(
            file_id,
            user_password,
            owner_password,
            allow_printing,
            allow_copying
        )

        # Get API key for logging
        api_key = get_api_key_from_request()

        # Create descriptive message
        permissions = []
        if allow_printing:
            permissions.append("printing allowed")
        else:
            permissions.append("printing disabled")

        if allow_copying:
            permissions.append("copying allowed")
        else:
            permissions.append("copying disabled")

        description = f"Protected PDF with password ({', '.join(permissions)})"

        # Log operation (only if not preview)
        if not preview_only:
            log_operation(
                api_key,
                'protect',
                pdf_info['id'],
                pdf_info['filename'],
                description
            )

        # Return metadata (excluding internal filepath)
        response_info = pdf_info.copy()
        response_info.pop('filepath', None)

        return jsonify(response_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/compress', methods=['POST'])
def compress_pdf_route():
    data = request.json
    if not data or 'file_id' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400

    file_id = data['file_id']

    try:
        # Get compression parameters
        compression_level = data.get('compression_level', 'medium')
        preview_only = data.get('preview_only', False)

        # Important: use file_storage if file_id is not in pdf_ops.pdf_storage
        if file_id not in pdf_ops.pdf_storage and file_id in file_storage:
            # Copy file info to pdf_ops storage
            pdf_ops.pdf_storage[file_id] = file_storage[file_id]

        # Use the PdfOperations class to compress PDF
        pdf_info = pdf_ops.compress_pdf(file_id, compression_level)

        # Also store in the old system for compatibility
        file_storage[pdf_info['id']] = pdf_info

        # Get API key for logging
        api_key = get_api_key_from_request()

        # Create descriptive message
        # Include compression ratio if available
        compression_ratio = None
        if 'compression_ratio' in pdf_info:
            compression_ratio = pdf_info['compression_ratio']
            description = f"Compressed PDF by {round(compression_ratio * 100)}% ({compression_level} level)"
        else:
            description = f"Compressed PDF ({compression_level} level)"

        # Log operation (only if not preview)
        if not preview_only:
            log_operation(
                api_key,
                'compress',
                pdf_info['id'],
                pdf_info['filename'],
                description
            )

        # Return metadata (excluding internal filepath)
        response_info = pdf_info.copy()
        response_info.pop('filepath', None)

        return jsonify(response_info)
    except Exception as e:
        print(f"Error compressing PDF: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/remove-pages', methods=['POST'])
def remove_pages_route():
    data = request.json
    if not data or 'file_id' not in data or 'pages' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400

    file_id = data['file_id']
    pages_to_remove = data['pages']
    preview_only = data.get('preview_only', False)

    try:
        # Make sure the file exists in pdf_ops storage
        if file_id not in pdf_ops.pdf_storage and file_id in file_storage:
            pdf_ops.pdf_storage[file_id] = file_storage[file_id]

        # Create a preview or actually remove the pages
        if preview_only:
            pdf_info = pdf_ops.preview_remove_pages(file_id, pages_to_remove)
        else:
            pdf_info = pdf_ops.remove_pages(file_id, pages_to_remove)

        # Also store in the old system for compatibility
        file_storage[pdf_info['id']] = pdf_info

        # Get API key for logging
        api_key = get_api_key_from_request()

        # Create descriptive message
        description = f"Removed {len(pages_to_remove)} pages from PDF"

        # Log operation (only for actual removal, not preview)
        if not preview_only:
            log_operation(
                api_key,
                'remove-pages',
                pdf_info['id'],
                pdf_info['filename'],
                description
            )

        # Return metadata (excluding internal filepath)
        response_info = pdf_info.copy()
        response_info.pop('filepath', None)

        return jsonify(response_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/preview-remove-pages', methods=['POST'])
def preview_remove_pages_route():
    data = request.json
    if not data or 'file_id' not in data or 'pages' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400

    file_id = data['file_id']
    pages_to_remove = data['pages']

    try:
        # Make sure the file exists in pdf_ops storage
        if file_id not in pdf_ops.pdf_storage and file_id in file_storage:
            pdf_ops.pdf_storage[file_id] = file_storage[file_id]

        # Create a preview
        pdf_info = pdf_ops.preview_remove_pages(file_id, pages_to_remove)

        # Also store in the old system for compatibility
        file_storage[pdf_info['id']] = pdf_info

        # Return metadata (excluding internal filepath)
        response_info = pdf_info.copy()
        response_info.pop('filepath', None)

        return jsonify(response_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    if not file_id:
        return jsonify({"error": "File ID is required"}), 400
@app.route('/edit-metadata', methods=['POST'])
def edit_metadata_route():
    data = request.json
    if not data or 'file_id' not in data or 'metadata' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400

    if not pages:
        return jsonify({"error": "Page numbers are required"}), 400
    file_id = data['file_id']
    metadata = data['metadata']
    preview_only = data.get('preview_only', False)

    # Implement page removal in pdf_operations.py first
    return jsonify({"error": "Not implemented yet"}), 501
    try:
        # Make sure the file exists in pdf_ops storage
        if file_id not in pdf_ops.pdf_storage and file_id in file_storage:
            pdf_ops.pdf_storage[file_id] = file_storage[file_id]

        # Edit metadata
        pdf_info = pdf_ops.edit_metadata(file_id, metadata, preview_only)

        # Also store in the old system for compatibility
        file_storage[pdf_info['id']] = pdf_info

        # Get API key for logging
        api_key = get_api_key_from_request()

        # Create descriptive message - list the fields that were updated
        fields = []
        if metadata.get('title'):
            fields.append('title')
        if metadata.get('author'):
            fields.append('author')
        if metadata.get('subject'):
            fields.append('subject')
        if metadata.get('keywords'):
            fields.append('keywords')

        description = f"Updated PDF metadata ({', '.join(fields)})"

        # Log operation (only for actual edit, not preview)
        if not preview_only:
            log_operation(
                api_key,
                'edit-metadata',
                pdf_info['id'],
                pdf_info['filename'],
                description
            )

        # Return metadata (excluding internal filepath)
        response_info = pdf_info.copy()
        response_info.pop('filepath', None)

        return jsonify(response_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/metadata/<file_id>', methods=['GET'])
def get_metadata_route(file_id):
    if file_id not in pdf_ops.pdf_storage and file_id in file_storage:
        pdf_ops.pdf_storage[file_id] = file_storage[file_id]

    if file_id not in pdf_ops.pdf_storage:
        return jsonify({'error': 'File not found'}), 404

    try:
        metadata = pdf_ops.get_metadata(file_id)
        return jsonify({"metadata": metadata})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)