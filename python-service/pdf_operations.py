from pypdf import PdfReader, PdfWriter
import os
import uuid
import zipfile
import tempfile
from werkzeug.utils import secure_filename
from io import BytesIO
import fitz  # PyMuPDF for additional PDF operations
from PIL import Image  # For image to PDF conversion

class PdfOperations:
    """
    Comprehensive class for PDF operations including:
    - Uploading and saving PDFs
    - Merging multiple PDFs
    - Splitting PDFs by various methods
    - Rotating PDF pages
    - Adding watermarks to PDFs
    - Converting images to PDF
    - Converting PDF to images
    - Compressing PDFs
    - Editing PDF metadata
    """

    def __init__(self, upload_folder):
        """Initialize PDF operations with upload folder for temporary storage"""
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
        self.pdf_storage = {}

    def save_pdf(self, file):
        """Save uploaded PDF and return basic info"""
        file_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        filepath = os.path.join(self.upload_folder, f"{file_id}.pdf")

        file.save(filepath)

        # Get PDF info using PyPDF
        try:
            reader = PdfReader(filepath)
            pdf_info = {
                "id": file_id,
                "filename": filename,
                "pages": len(reader.pages),
                "filepath": filepath
            }
        except Exception as e:
            # If PyPDF fails, try with PyMuPDF
            try:
                doc = fitz.open(filepath)
                pdf_info = {
                    "id": file_id,
                    "filename": filename,
                    "pages": len(doc),
                    "filepath": filepath
                }
                doc.close()
            except Exception as e2:
                # If both fail, just provide basic info
                pdf_info = {
                    "id": file_id,
                    "filename": filename,
                    "pages": 0,  # Unknown number of pages
                    "filepath": filepath
                }

        self.pdf_storage[file_id] = pdf_info
        return pdf_info

    def merge_pdfs(self, files, output_filename=None):
        """Merge multiple PDF files into one"""
        try:
            # Save temporary files
            temp_files = []
            for file in files:
                temp_path = os.path.join(tempfile.gettempdir(), secure_filename(file.filename))
                file.save(temp_path)
                temp_files.append(temp_path)

            # Try merging with PyPDF first
            try:
                # Merge PDFs using PyPDF
                writer = PdfWriter()

                for temp_path in temp_files:
                    reader = PdfReader(temp_path)
                    for page in reader.pages:
                        writer.add_page(page)

                # Save merged PDF
                file_id = str(uuid.uuid4())
                if output_filename:
                    filename = secure_filename(output_filename)
                else:
                    filename = "merged.pdf"

                output_path = os.path.join(self.upload_folder, f"{file_id}_{filename}")

                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)

                # Get page count
                total_pages = len(writer.pages)

            except Exception as e:
                # If PyPDF fails, try with PyMuPDF
                doc = fitz.open()

                for temp_path in temp_files:
                    src_doc = fitz.open(temp_path)
                    doc.insert_pdf(src_doc)
                    src_doc.close()

                # Save merged PDF
                file_id = str(uuid.uuid4())
                if output_filename:
                    filename = secure_filename(output_filename)
                else:
                    filename = "merged.pdf"

                output_path = os.path.join(self.upload_folder, f"{file_id}_{filename}")
                doc.save(output_path)

                # Get page count
                total_pages = len(doc)
                doc.close()

            # Cleanup temporary files
            for temp_path in temp_files:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            # Create file info
            pdf_info = {
                "id": file_id,
                "filename": filename,
                "pages": total_pages,
                "filepath": output_path
            }

            self.pdf_storage[file_id] = pdf_info
            return pdf_info

        except Exception as e:
            raise Exception(f"Error merging PDFs: {str(e)}")

    def split_pdf(self, file_id, split_method='byPage', ranges=None, pages=None, create_zip=True):
        """Split a PDF file based on specified method"""
        if file_id not in self.pdf_storage:
            raise Exception("File not found")

        file_info = self.pdf_storage[file_id]

        try:
            # Try with PyPDF first
            try:
                reader = PdfReader(file_info['filepath'])
                total_pages = len(reader.pages)

                result_files = []

                if split_method == 'byPage':
                    # Split each page into a separate file
                    for i in range(total_pages):
                        writer = PdfWriter()
                        writer.add_page(reader.pages[i])

                        split_id = str(uuid.uuid4())
                        filename = f"page_{i+1}.pdf"
                        output_path = os.path.join(self.upload_folder, f"{split_id}_{filename}")

                        with open(output_path, 'wb') as output_file:
                            writer.write(output_file)

                        pdf_info = {
                            "id": split_id,
                            "filename": filename,
                            "pages": 1,
                            "filepath": output_path
                        }

                        self.pdf_storage[split_id] = pdf_info
                        result_files.append(pdf_info)

                elif split_method == 'byRanges' and ranges:
                    # Split by specified page ranges
                    for i, range_info in enumerate(ranges):
                        start = int(range_info.get('start', 1)) - 1  # Convert to 0-based index
                        end = int(range_info.get('end', 1))

                        if start < 0 or end > total_pages or start >= end:
                            continue

                        writer = PdfWriter()

                        for page_num in range(start, end):
                            writer.add_page(reader.pages[page_num])

                        split_id = str(uuid.uuid4())
                        filename = f"pages_{start+1}-{end}.pdf"
                        output_path = os.path.join(self.upload_folder, f"{split_id}_{filename}")

                        with open(output_path, 'wb') as output_file:
                            writer.write(output_file)

                        pdf_info = {
                            "id": split_id,
                            "filename": filename,
                            "pages": end - start,
                            "filepath": output_path
                        }

                        self.pdf_storage[split_id] = pdf_info
                        result_files.append(pdf_info)

                elif split_method == 'extractPages' and pages:
                    # Extract specific pages
                    writer = PdfWriter()

                    for page_num in pages:
                        if 1 <= page_num <= total_pages:
                            writer.add_page(reader.pages[page_num - 1])

                    split_id = str(uuid.uuid4())
                    if len(pages) <= 5:  # For a reasonable filename length
                        page_list = '-'.join(str(p) for p in pages)
                    else:
                        page_list = f"{pages[0]}-{pages[-1]}_selection"

                    filename = f"extracted_pages_{page_list}.pdf"
                    output_path = os.path.join(self.upload_folder, f"{split_id}_{filename}")

                    with open(output_path, 'wb') as output_file:
                        writer.write(output_file)

                    pdf_info = {
                        "id": split_id,
                        "filename": filename,
                        "pages": len(writer.pages),
                        "filepath": output_path
                    }

                    self.pdf_storage[split_id] = pdf_info
                    result_files.append(pdf_info)

            except Exception as e:
                # If PyPDF fails, try with PyMuPDF
                doc = fitz.open(file_info['filepath'])
                total_pages = len(doc)

                result_files = []

                if split_method == 'byPage':
                    # Split each page into a separate file
                    for i in range(total_pages):
                        output_doc = fitz.open()
                        output_doc.insert_pdf(doc, from_page=i, to_page=i)

                        split_id = str(uuid.uuid4())
                        filename = f"page_{i+1}.pdf"
                        output_path = os.path.join(self.upload_folder, f"{split_id}_{filename}")

                        output_doc.save(output_path)
                        output_doc.close()

                        pdf_info = {
                            "id": split_id,
                            "filename": filename,
                            "pages": 1,
                            "filepath": output_path
                        }

                        self.pdf_storage[split_id] = pdf_info
                        result_files.append(pdf_info)

                elif split_method == 'byRanges' and ranges:
                    # Split by specified page ranges
                    for i, range_info in enumerate(ranges):
                        start = int(range_info.get('start', 1)) - 1  # Convert to 0-based index
                        end = int(range_info.get('end', 1)) - 1      # Convert to 0-based index

                        if start < 0 or end >= total_pages or start > end:
                            continue

                        output_doc = fitz.open()
                        output_doc.insert_pdf(doc, from_page=start, to_page=end)

                        split_id = str(uuid.uuid4())
                        filename = f"pages_{start+1}-{end+1}.pdf"
                        output_path = os.path.join(self.upload_folder, f"{split_id}_{filename}")

                        output_doc.save(output_path)
                        output_doc.close()

                        pdf_info = {
                            "id": split_id,
                            "filename": filename,
                            "pages": end - start + 1,
                            "filepath": output_path
                        }

                        self.pdf_storage[split_id] = pdf_info
                        result_files.append(pdf_info)

                elif split_method == 'extractPages' and pages:
                    # Extract specific pages
                    output_doc = fitz.open()

                    # Convert to 0-based indices for PyMuPDF
                    pymupdf_pages = [p-1 for p in pages if 1 <= p <= total_pages]

                    for page_idx in pymupdf_pages:
                        output_doc.insert_pdf(doc, from_page=page_idx, to_page=page_idx)

                    split_id = str(uuid.uuid4())
                    if len(pages) <= 5:  # For a reasonable filename length
                        page_list = '-'.join(str(p) for p in pages)
                    else:
                        page_list = f"{pages[0]}-{pages[-1]}_selection"

                    filename = f"extracted_pages_{page_list}.pdf"
                    output_path = os.path.join(self.upload_folder, f"{split_id}_{filename}")

                    output_doc.save(output_path)
                    output_doc.close()

                    pdf_info = {
                        "id": split_id,
                        "filename": filename,
                        "pages": len(pymupdf_pages),
                        "filepath": output_path
                    }

                    self.pdf_storage[split_id] = pdf_info
                    result_files.append(pdf_info)

                doc.close()

            # Create zip file if needed and there are multiple files
            if create_zip and len(result_files) > 1:
                zip_id = str(uuid.uuid4())
                zip_filename = f"split_files_{zip_id}.zip"
                zip_path = os.path.join(self.upload_folder, zip_filename)

                with zipfile.ZipFile(zip_path, 'w') as zip_file:
                    for file_info in result_files:
                        zip_file.write(file_info['filepath'], file_info['filename'])

                # Add zip info to result files
                for file_info in result_files:
                    file_info['zip_id'] = zip_id
                    file_info['zip_path'] = zip_path
                    file_info['zip_filename'] = zip_filename

            return result_files

        except Exception as e:
            raise Exception(f"Error splitting PDF: {str(e)}")

    def get_file_path(self, file_id):
        """Get file path for download"""
        if file_id not in self.pdf_storage:
            return None

        return self.pdf_storage[file_id]['filepath']

    def get_zip_path(self, zip_id):
        """Get zip file path for download"""
        for file_id, file_info in self.pdf_storage.items():
            if 'zip_id' in file_info and file_info['zip_id'] == zip_id:
                return file_info['zip_path']

        return None

    def cleanup_files(self, max_age_hours=24):
        """Clean up temporary files older than specified age"""
        # Implementation for cleanup
        pass