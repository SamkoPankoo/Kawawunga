# First import all required modules
import os
import uuid
import json
import shutil
import zipfile
import io
import tempfile
import time
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, send_file, make_response, after_this_request
from flask_cors import CORS

# Initialize Flask application
app = Flask(__name__)

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

# Logging function
def log_operation(api_key, action, file_id=None, filename=None):
    try:
        # Try using the imported logger if available
        return logger_log_operation(
            api_key=api_key,
            action=action,
            description=f"{action} operation",
            file_id=file_id,
            file_name=filename,
            operation_type=action
        )
    except Exception as e:
        # Fallback to simple console logging
        print(f"[LOG] Operation: {action}, File: {filename}, ID: {file_id}, API Key: {api_key[:5] if api_key else 'None'}...")
        return True

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

    # Try to get the file path from PdfOperations
    filepath = pdf_ops.get_zip_path(zip_id)

    if not filepath and zip_id in zip_storage:
        filepath = zip_storage[zip_id]['filepath']

    if not filepath:
        return jsonify({'error': 'ZIP file not found'}), 404

    filename = ""
    if zip_id in zip_storage:
        filename = zip_storage[zip_id]['filename']
    else:
        filename = f"download_{zip_id}.zip"

    try:
        # Create a response with the file
        response = make_response(send_file(
            filepath,
            download_name=filename,
            mimetype='application/zip',
            as_attachment=True
        ))

        # Add CORS headers explicitly
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Expose-Headers', 'Content-Disposition')

        return response
    except Exception as e:
        app.logger.error(f"Error sending ZIP file {filepath}: {str(e)}")
        return jsonify({'error': f'Error downloading ZIP file: {str(e)}'}), 500

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
        # Use the PdfOperations class to merge PDFs properly
        pdf_info = pdf_ops.merge_pdfs(files, output_filename)

        # Also store in the old system for compatibility with other functions
        file_storage[pdf_info['id']] = pdf_info

        # Log operation
        api_key = request.headers.get('X-API-Key')
        log_operation(api_key, 'merge', pdf_info['id'], pdf_info['filename'])

        # Return metadata (excluding internal filepath)
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

        # Log operation
        api_key = request.headers.get('X-API-Key')
        file_name = pdf_ops.pdf_storage[file_id]['filename'] if file_id in pdf_ops.pdf_storage else "Unknown"
        log_operation(api_key, 'split', file_id, file_name)

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

        # Log operation
        api_key = request.headers.get('X-API-Key')
        log_operation(api_key, 'rotate', pdf_info['id'], pdf_info['filename'])

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

        # Log operation
        api_key = request.headers.get('X-API-Key')
        log_operation(api_key, 'watermark', pdf_info['id'], pdf_info['filename'])

        # Return metadata (excluding internal filepath)
        response_info = pdf_info.copy()
        response_info.pop('filepath', None)

        return jsonify(response_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/pdf-to-image', methods=['POST', 'OPTIONS'])
def pdf_to_image():
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
        return response

    try:
        data = request.json
        if not data or 'file_id' not in data:
            return jsonify({'error': 'Missing required parameters'}), 400

        file_id = data['file_id']

        # Check if file exists in either system
        if file_id not in pdf_ops.pdf_storage and file_id not in file_storage:
            return jsonify({'error': 'File not found'}), 404

        # Get conversion parameters
        format = data.get('format', 'png')
        dpi = data.get('dpi', 300)
        create_zip = data.get('create_zip', True)

        # Handle page selection
        pages = None
        if 'pages' in data:
            pages = data['pages']
            # Make sure pages are integers
            if isinstance(pages, list):
                pages = [int(p) for p in pages if isinstance(p, (int, str)) and str(p).isdigit()]

        # Use the PdfOperations class to convert PDF to images
        result_files = pdf_ops.convert_pdf_to_images(file_id, format, dpi, pages, create_zip)

        # Also store in the old system for compatibility
        for file_info in result_files:
            if 'id' in file_info:
                file_storage[file_info['id']] = file_info

            # If there's zip info, store that too
            if 'zip_id' in file_info:
                zip_id = file_info['zip_id']
                for other_file in result_files:
                    if other_file.get('zip_id') == zip_id and 'zip_path' in other_file:
                        zip_storage[zip_id] = {
                            'id': zip_id,
                            'filename': os.path.basename(other_file['zip_path']),
                            'filepath': other_file['zip_path'],
                            'type': 'application/zip'
                        }
                        break

        # Log operation
        api_key = request.headers.get('X-API-Key')
        file_name = pdf_ops.pdf_storage[file_id]['filename'] if file_id in pdf_ops.pdf_storage else "Unknown"
        log_operation(api_key, 'pdf-to-image', file_id, file_name)

        # Return metadata (excluding internal filepaths)
        response_files = []
        for file_info in result_files:
            response_info = file_info.copy()
            response_info.pop('filepath', None)
            if 'zip_path' in response_info:
                response_info.pop('zip_path', None)
            response_files.append(response_info)

        # Make sure any zip URL doesn't have double slash
        for file_info in response_files:
            if 'zip_id' in file_info:
                file_info['zip_url'] = f"/download-zip/{file_info['zip_id']}"

        return jsonify({"files": response_files})
    except Exception as e:
        app.logger.error(f"Error in pdf-to-image: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/image-to-pdf', methods=['POST'])
def image_to_pdf():
    if len(request.files) < 1:
        return jsonify({'error': 'No image files provided'}), 400

    # Get all image files from the request
    image_files = []
    for key in request.files:
        file = request.files[key]
        if file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
            image_files.append(file)

    if len(image_files) < 1:
        return jsonify({'error': 'No valid image files provided'}), 400

    # Get parameters
    page_size = request.form.get('page_size', 'A4')
    orientation = request.form.get('orientation', 'portrait')

    try:
        # Use the PdfOperations class to convert images to PDF
        pdf_info = pdf_ops.convert_images_to_pdf(image_files, page_size, orientation)

        # Also store in the old system for compatibility
        file_storage[pdf_info['id']] = pdf_info

        # Log operation
        api_key = request.headers.get('X-API-Key')
        log_operation(api_key, 'image-to-pdf', pdf_info['id'], pdf_info['filename'])

        # Return metadata (excluding internal filepath)
        response_info = pdf_info.copy()
        response_info.pop('filepath', None)

        return jsonify(response_info)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/protect', methods=['POST'])
def protect_pdf():
    data = request.json
    if not data or 'file_id' not in data or 'user_password' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400

    file_id = data['file_id']
    if file_id not in file_storage:
        return jsonify({'error': 'File not found'}), 404

    # Get protection parameters
    user_password = data['user_password']
    owner_password = data.get('owner_password', user_password)
    allow_printing = data.get('allow_printing', True)
    allow_copying = data.get('allow_copying', True)

    # Get original file info
    original_file = file_storage[file_id]
    original_filepath = original_file['filepath']

    # Create a new file
    new_file_id = str(uuid.uuid4())
    new_filename = f"protected_{original_file['filename']}"
    new_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{new_file_id}.pdf")

    # Copy the original file (in a real implementation, we would add password protection)
    shutil.copy(original_filepath, new_filepath)

    # Store metadata
    file_info = {
        "id": new_file_id,
        "filename": new_filename,
        "filepath": new_filepath,
        "pages": original_file.get('pages', 1)
    }
    file_storage[new_file_id] = file_info

    # Log operation
    api_key = request.headers.get('X-API-Key')
    log_operation(api_key, 'protect', new_file_id, new_filename)

    # Return metadata (excluding internal filepath)
    response_info = file_info.copy()
    response_info.pop('filepath', None)

    return jsonify(response_info)

@app.route('/compress', methods=['POST'])
def compress_pdf():
    data = request.json
    if not data or 'file_id' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400

    file_id = data['file_id']
    if file_id not in file_storage:
        return jsonify({'error': 'File not found'}), 404

    # Get compression parameters
    compression_level = data.get('compression_level', 'medium')

    # Get original file info
    original_file = file_storage[file_id]
    original_filepath = original_file['filepath']

    # Create a new file
    new_file_id = str(uuid.uuid4())
    new_filename = f"compressed_{original_file['filename']}"
    new_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{new_file_id}.pdf")

    # Copy the original file (in a real implementation, we would compress the PDF)
    shutil.copy(original_filepath, new_filepath)

    # Store metadata
    file_info = {
        "id": new_file_id,
        "filename": new_filename,
        "filepath": new_filepath,
        "pages": original_file.get('pages', 1)
    }
    file_storage[new_file_id] = file_info

    # Log operation
    api_key = request.headers.get('X-API-Key')
    log_operation(api_key, 'compress', new_file_id, new_filename)

    # Return metadata (excluding internal filepath)
    response_info = file_info.copy()
    response_info.pop('filepath', None)

    return jsonify(response_info)

@app.route('/edit-metadata', methods=['POST'])
def edit_metadata():
    data = request.json
    if not data or 'file_id' not in data or 'metadata' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400

    file_id = data['file_id']
    if file_id not in file_storage:
        return jsonify({'error': 'File not found'}), 404

    # Get metadata parameters
    metadata = data['metadata']

    # Get original file info
    original_file = file_storage[file_id]
    original_filepath = original_file['filepath']

    # Create a new file
    new_file_id = str(uuid.uuid4())
    new_filename = f"metadata_{original_file['filename']}"
    new_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{new_file_id}.pdf")

    # Copy the original file (in a real implementation, we would update the metadata)
    shutil.copy(original_filepath, new_filepath)

    # Store metadata
    file_info = {
        "id": new_file_id,
        "filename": new_filename,
        "filepath": new_filepath,
        "pages": original_file.get('pages', 1)
    }
    file_storage[new_file_id] = file_info

    # Log operation
    api_key = request.headers.get('X-API-Key')
    log_operation(api_key, 'edit-metadata', new_file_id, new_filename)

    # Return metadata (excluding internal filepath)
    response_info = file_info.copy()
    response_info.pop('filepath', None)

    return jsonify(response_info)

@app.route('/metadata/<file_id>', methods=['GET'])
def get_metadata(file_id):
    if file_id not in file_storage:
        return jsonify({'error': 'File not found'}), 404

    # Get file info
    file_info = file_storage[file_id]

    # In a real implementation, we would read the actual metadata
    # For now, return placeholder metadata
    metadata = {
        "title": "Document Title",
        "author": "Document Author",
        "subject": "Document Subject",
        "keywords": "pdf, document, example"
    }

    return jsonify({"metadata": metadata})

@app.route('/api-docs', methods=['GET'])
def api_docs():
    # Read the Swagger JSON file if it exists
    try:
        with open('swagger.json', 'r') as f:
            swagger_data = json.load(f)
        return jsonify(swagger_data)
    except:
        return jsonify({"error": "Swagger documentation not available"}), 404

# Cleanup task for temporary files (run in production)
def cleanup_old_files():
    while True:
        time.sleep(3600)  # Sleep for 1 hour

        try:
            # Use the PdfOperations class to clean up files
            pdf_ops.cleanup_files(24)  # 24 hours

            # Also clean up any remaining files in the old system
            now = time.time()
            max_age = 24 * 3600  # 24 hours

            # Clean up old files
            for root, dirs, files in os.walk(app.config['UPLOAD_FOLDER']):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    if os.path.isfile(filepath):
                        file_age = now - os.path.getmtime(filepath)
                        if file_age > max_age:
                            try:
                                os.remove(filepath)
                                print(f"Removed old file: {filepath}")
                            except:
                                pass
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

if __name__ == '__main__':
    # Start cleanup task in a separate thread
    import threading
    cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
    cleanup_thread.start()

    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)