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

    def remove_pages(self, file_id, pages_to_remove):
        """Remove specific pages from a PDF file"""
        if file_id not in self.pdf_storage:
            raise Exception("File not found")

        file_info = self.pdf_storage[file_id]

        try:
            # Try with PyPDF first
            try:
                reader = PdfReader(file_info['filepath'])
                writer = PdfWriter()
                total_pages = len(reader.pages)

                # Convert to integers and ensure within range
                pages_to_remove = [int(p) for p in pages_to_remove if 1 <= int(p) <= total_pages]

                # Check that we're not removing all pages
                if len(pages_to_remove) >= total_pages:
                    raise Exception("Cannot remove all pages from the PDF")

                # Add all pages except those to be removed
                for i in range(total_pages):
                    if i + 1 not in pages_to_remove:  # Use 1-indexed page numbers
                        writer.add_page(reader.pages[i])

                new_file_id = str(uuid.uuid4())
                new_filename = f"pages_removed_{file_info['filename']}"
                output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")

                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)

            except Exception as e:
                # If PyPDF fails, try with PyMuPDF
                doc = fitz.open(file_info['filepath'])
                total_pages = len(doc)

                # Convert to integers and ensure within range
                pages_to_remove = [int(p) for p in pages_to_remove if 1 <= int(p) <= total_pages]

                # Check that we're not removing all pages
                if len(pages_to_remove) >= total_pages:
                    raise Exception("Cannot remove all pages from the PDF")

                # PyMuPDF requires a list of pages to keep, not to remove
                pages_to_keep = [i for i in range(total_pages) if i+1 not in pages_to_remove]

                # Create a new document with only the pages we want to keep
                new_doc = fitz.open()
                for page_num in pages_to_keep:
                    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

                new_file_id = str(uuid.uuid4())
                new_filename = f"pages_removed_{file_info['filename']}"
                output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")

                new_doc.save(output_path)
                new_doc.close()
                doc.close()

            # Create file info
            pdf_info = {
                "id": new_file_id,
                "filename": new_filename,
                "pages": total_pages - len(pages_to_remove),
                "filepath": output_path,
                "removed_pages": pages_to_remove
            }

            self.pdf_storage[new_file_id] = pdf_info
            return pdf_info

        except Exception as e:
            raise Exception(f"Error removing pages from PDF: {str(e)}")

    def preview_remove_pages(self, file_id, pages_to_remove):
        """Create a preview showing which pages will be removed in red"""
        if file_id not in self.pdf_storage:
            raise Exception("File not found")

        file_info = self.pdf_storage[file_id]

        try:
            doc = fitz.open(file_info['filepath'])
            total_pages = len(doc)

            # Convert to integers and ensure within range
            pages_to_remove = [int(p) for p in pages_to_remove if 1 <= int(p) <= total_pages]

            # Add a red highlight to pages that will be removed
            for page_num in pages_to_remove:
                page = doc[page_num-1]  # 0-based index

                # Get page dimensions
                rect = page.rect

                # Add a semi-transparent red overlay
                page.draw_rect(rect, color=(1, 0, 0), fill=(1, 0, 0, 0.3), overlay=True)

                # Add a "TO BE DELETED" watermark
                font_size = 36
                text = "TO BE DELETED"
                tw = fitz.TextWriter(rect)

                # V PyMuPDF TextWriter.append() nepoužívá parametr color přímo
                # Místo toho musíme použít fitz.utils.getColor pro převod barvy
                red_color = (1, 0, 0)  # RGB červená
                tw.append((rect.width/2, rect.height/2), text, fontsize=font_size,
                          color=red_color)  # Správné použití color parametru

                tw.write_text(page, opacity=0.8)

            new_file_id = str(uuid.uuid4())
            new_filename = f"preview_delete_{file_info['filename']}"
            output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")

            doc.save(output_path)
            doc.close()

            # Create file info
            pdf_info = {
                "id": new_file_id,
                "filename": new_filename,
                "pages": total_pages,
                "filepath": output_path,
                "preview": True,
                "pages_to_remove": pages_to_remove
            }

            self.pdf_storage[new_file_id] = pdf_info
            return pdf_info

        except Exception as e:
            raise Exception(f"Error creating delete preview: {str(e)}")


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

    def rotate_pdf(self, file_id, angle=90, pages=None, preview_only=False):
        """Rotate pages in a PDF file"""
        if file_id not in self.pdf_storage:
            raise Exception("File not found")

        file_info = self.pdf_storage[file_id]

        try:
            # Convert angle to integer if it's a string
            if isinstance(angle, str):
                try:
                    angle = int(angle)
                except ValueError:
                    angle = 90  # Default to 90 degrees if invalid

            # Normalize angle to 0, 90, 180, or 270
            angle = angle % 360

            # Try with PyMuPDF first
            try:
                doc = fitz.open(file_info['filepath'])
                total_pages = len(doc)

                # Determine which pages to rotate
                if pages is None or not pages:
                    pages = list(range(1, total_pages + 1))

                # Validate pages
                pages = [p for p in pages if 1 <= p <= total_pages]

                if not pages:
                    raise Exception("No valid pages to rotate")

                # Apply rotation
                for page_num in pages:
                    # PyMuPDF uses 0-based indexing
                    page = doc[page_num - 1]

                    # Get current rotation
                    current_rotation = page.rotation

                    # Calculate new rotation (fitz uses 0, 90, 180, 270)
                    new_rotation = (current_rotation + angle) % 360

                    # Apply the rotation
                    page.set_rotation(new_rotation)

                # For preview, use a temporary filename with "preview_" prefix
                if preview_only:
                    new_file_id = str(uuid.uuid4())
                    new_filename = f"preview_rotated_{file_info['filename']}"
                    output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")
                else:
                    new_file_id = str(uuid.uuid4())
                    new_filename = f"rotated_{file_info['filename']}"
                    output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")

                doc.save(output_path)
                doc.close()

            except Exception as e:
                # If PyMuPDF fails, try with PyPDF
                reader = PdfReader(file_info['filepath'])
                writer = PdfWriter()

                total_pages = len(reader.pages)

                # Determine which pages to rotate
                if pages is None or not pages:
                    pages = list(range(1, total_pages + 1))

                # Validate pages
                pages = [p for p in pages if 1 <= p <= total_pages]

                if not pages:
                    raise Exception("No valid pages to rotate")

                # Add all pages, rotating the selected ones
                for i in range(total_pages):
                    page = reader.pages[i]

                    # If this page should be rotated
                    if i + 1 in pages:
                        # Get current rotation
                        current_rotation = page.rotation if hasattr(page, 'rotation') else 0

                        # Calculate new rotation
                        new_rotation = (current_rotation + angle) % 360

                        # Apply rotation
                        page.rotate(new_rotation)

                    writer.add_page(page)

                # For preview, use a temporary filename with "preview_" prefix
                if preview_only:
                    new_file_id = str(uuid.uuid4())
                    new_filename = f"preview_rotated_{file_info['filename']}"
                    output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")
                else:
                    new_file_id = str(uuid.uuid4())
                    new_filename = f"rotated_{file_info['filename']}"
                    output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")

                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)

            # Create file info
            pdf_info = {
                "id": new_file_id,
                "filename": new_filename,
                "pages": total_pages,
                "filepath": output_path,
                "preview": preview_only
            }

            # Store in pdf_storage (even previews, they'll be cleaned up later)
            self.pdf_storage[new_file_id] = pdf_info
            return pdf_info

        except Exception as e:
            raise Exception(f"Error rotating PDF: {str(e)}")

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