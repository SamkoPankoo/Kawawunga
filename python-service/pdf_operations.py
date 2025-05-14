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

    def add_watermark(self, file_id, text, opacity=0.3, color="gray", size=36, angle=45, pages=None, preview_only=False):
        """Add text watermark to PDF pages"""
        if file_id not in self.pdf_storage:
            raise Exception("File not found")

        file_info = self.pdf_storage[file_id]

        try:
            # Convert opacity to float in range 0-1
            if isinstance(opacity, int) and opacity > 1:
                opacity = opacity / 100.0
            opacity = min(max(float(opacity), 0), 1)  # Ensure in range 0-1

            # Try with PyMuPDF
            try:
                # Open the PDF with PyMuPDF
                doc = fitz.open(file_info['filepath'])
                total_pages = len(doc)

                # Determine which pages to watermark
                if pages is None or not pages:
                    pages = list(range(1, total_pages + 1))

                # Validate pages
                pages = [p for p in pages if 1 <= p <= total_pages]

                # Create font color
                if color == "gray":
                    text_color = (0.5, 0.5, 0.5)
                elif color == "red":
                    text_color = (1, 0, 0)
                elif color == "blue":
                    text_color = (0, 0, 1)
                elif color == "green":
                    text_color = (0, 0.5, 0)
                elif color == "black":
                    text_color = (0, 0, 0)
                else:
                    text_color = (0.5, 0.5, 0.5)  # Default to gray

                # Apply watermark to all selected pages
                for page_num in pages:
                    # Get the page (PyMuPDF uses 0-based indexing)
                    page = doc[page_num - 1]

                    # Get page dimensions
                    rect = page.rect
                    center_x = rect.width / 2
                    center_y = rect.height / 2

                    # Create text watermark
                    fontsize = size
                    text_writer = fitz.TextWriter(rect, opacity=opacity, color=text_color)
                    text_writer.append((center_x, center_y), text, fontsize=fontsize, rotate=angle)
                    text_writer.write_text(page)

                # For preview, use a temporary filename with "preview_" prefix
                if preview_only:
                    new_file_id = str(uuid.uuid4())
                    new_filename = f"preview_watermarked_{file_info['filename']}"
                    output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")
                else:
                    new_file_id = str(uuid.uuid4())
                    new_filename = f"watermarked_{file_info['filename']}"
                    output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")

                doc.save(output_path)
                doc.close()

            except Exception as e:
                # If PyMuPDF failed, try with PyPDF and reportlab
                from reportlab.pdfgen import canvas
                from reportlab.lib.pagesizes import letter
                from reportlab.lib.colors import red, blue, green, black, gray
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                from io import BytesIO

                # Get proper color
                if color == "red":
                    text_color = red
                elif color == "blue":
                    text_color = blue
                elif color == "green":
                    text_color = green
                elif color == "black":
                    text_color = black
                else:
                    text_color = gray

                # Open original PDF
                reader = PdfReader(file_info['filepath'])
                writer = PdfWriter()

                total_pages = len(reader.pages)

                # Determine which pages to watermark
                if pages is None or not pages:
                    pages = list(range(1, total_pages + 1))

                # Validate pages
                pages = [p for p in pages if 1 <= p <= total_pages]

                # Process each page
                for i in range(total_pages):
                    page = reader.pages[i]

                    if i + 1 in pages:  # If this page should be watermarked
                        # Create watermark
                        packet = BytesIO()
                        c = canvas.Canvas(packet, pagesize=(page.mediabox.width, page.mediabox.height))
                        c.setFont("Helvetica", size)
                        c.setFillColor(text_color)
                        c.setFillAlpha(opacity)

                        # Position watermark in the center
                        c.saveState()
                        c.translate(page.mediabox.width / 2, page.mediabox.height / 2)
                        c.rotate(angle)
                        c.drawCentredString(0, 0, text)
                        c.restoreState()

                        c.save()

                        # Get the watermark as a PDF page
                        packet.seek(0)
                        watermark = PdfReader(packet).pages[0]

                        # Merge watermark with page
                        page.merge_page(watermark)

                    writer.add_page(page)

                # For preview, use a temporary filename with "preview_" prefix
                if preview_only:
                    new_file_id = str(uuid.uuid4())
                    new_filename = f"preview_watermarked_{file_info['filename']}"
                    output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")
                else:
                    new_file_id = str(uuid.uuid4())
                    new_filename = f"watermarked_{file_info['filename']}"
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
            raise Exception(f"Error adding watermark to PDF: {str(e)}")

    def compress_pdf(self, file_id, compression_level='medium'):
        """
        Compress a PDF file to reduce its size - improved version
        """
        if file_id not in self.pdf_storage:
            raise Exception("File not found")

        file_info = self.pdf_storage[file_id]

        try:
            # Map compression level to actual compression settings
            compression_settings = {
                'low': {'image_quality': 80, 'dpi': 150, 'pdfsettings': '/prepress'},
                'medium': {'image_quality': 50, 'dpi': 120, 'pdfsettings': '/ebook'},
                'high': {'image_quality': 30, 'dpi': 72, 'pdfsettings': '/screen'}
            }

            # Default to medium if invalid level
            if compression_level not in compression_settings:
                compression_level = 'medium'

            settings = compression_settings[compression_level]

            # Create a new file ID and path
            new_file_id = str(uuid.uuid4())
            new_filename = f"compressed_{file_info['filename']}"
            output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")
            temp_output = os.path.join(tempfile.gettempdir(), f"temp_{new_file_id}.pdf")

            # APPROACH 1: Try using Ghostscript if available - most effective
            try:
                import subprocess
                gs_params = ['-dPDFSETTINGS=' + settings['pdfsettings']]

                # Execute ghostscript
                subprocess.run(
                    ['gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
                    gs_params[0], '-dNOPAUSE', '-dQUIET', '-dBATCH',
                    f'-sOutputFile={temp_output}', file_info['filepath']],
                    check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )

                if os.path.exists(temp_output):
                    shutil.copy(temp_output, output_path)
                    os.remove(temp_output)
            except Exception as gs_error:
                print(f"Ghostscript compression failed: {gs_error}")

                # APPROACH 2: Try PyMuPDF for image-based compression
                try:
                    doc = fitz.open(file_info['filepath'])

                    # Process each page for image compression
                    for page_num in range(len(doc)):
                        page = doc[page_num]
                        image_list = page.get_images(full=True)

                        for img_index, img in enumerate(image_list):
                            xref = img[0]  # Image reference number

                            try:
                                base_image = doc.extract_image(xref)
                                image_bytes = base_image["image"]

                                # Convert to PIL image for recompression
                                from PIL import Image
                                import io

                                # Load the image
                                image = Image.open(io.BytesIO(image_bytes))

                                # Resize image based on compression level
                                if compression_level == 'high':
                                    # Reduce by 50%
                                    orig_width, orig_height = image.size
                                    new_width = int(orig_width * 0.5)
                                    new_height = int(orig_height * 0.5)
                                    image = image.resize((new_width, new_height), Image.LANCZOS)
                                elif compression_level == 'medium':
                                    # Reduce by 25%
                                    orig_width, orig_height = image.size
                                    new_width = int(orig_width * 0.75)
                                    new_height = int(orig_height * 0.75)
                                    image = image.resize((new_width, new_height), Image.LANCZOS)
                            except Exception as e:
                                print(f"Error processing image: {e}")

                    # Save with aggressive compression settings
                    doc.save(output_path,
                            garbage=4,  # Clean up unused objects
                            clean=True,  # More cleanup
                            deflate=True,  # Compress streams
                            deflate_images=True,  # Compress images
                            deflate_fonts=True)  # Compress fonts
                    doc.close()
                except Exception as mupdf_error:
                    print(f"PyMuPDF compression failed: {mupdf_error}")

                    # APPROACH 3: PyPDF as last resort
                    reader = PdfReader(file_info['filepath'])
                    writer = PdfWriter()

                    for page in reader.pages:
                        writer.add_page(page)

                    writer.compress_content_streams = True

                    with open(output_path, 'wb') as output_file:
                        writer.write(output_file)

            # If the output file doesn't exist or is somehow larger than the original,
            # create a more aggressive compression using a different approach
            if not os.path.exists(output_path) or os.path.getsize(output_path) >= os.path.getsize(file_info['filepath']):
                # Try qpdf as a last resort if available
                try:
                    import subprocess
                    subprocess.run(
                        ['qpdf', '--linearize', '--compress-streams=y', '--decode-level=specialized',
                         file_info['filepath'], output_path],
                        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                except Exception:
                    # If all else fails, just use the original with JPG conversion trick
                    # This method is more aggressive but might reduce quality
                    try:
                        # Open with PyMuPDF
                        doc = fitz.open(file_info['filepath'])
                        pdf_writer = fitz.open()

                        # Convert each page to JPG then back to PDF
                        for page_num in range(len(doc)):
                            page = doc[page_num]
                            pix = page.get_pixmap(matrix=fitz.Matrix(1, 1))

                            # Higher compression for higher levels
                            quality = 30
                            if compression_level == 'low':
                                quality = 60
                            elif compression_level == 'medium':
                                quality = 40

                            img_data = pix.tobytes("jpeg", quality=quality)
                            img = Image.open(io.BytesIO(img_data))

                            # Create new PDF page
                            new_page = pdf_writer.new_page(width=page.rect.width, height=page.rect.height)
                            new_page.insert_image(page.rect, stream=img_data)

                        # Save the resultant PDF
                        pdf_writer.save(output_path)
                        pdf_writer.close()
                        doc.close()
                    except Exception as e:
                        print(f"Final compression method failed: {e}")
                        # Last resort - just copy the file if all methods fail
                        shutil.copy(file_info['filepath'], output_path)

            # Create file info
            pdf_info = {
                "id": new_file_id,
                "filename": new_filename,
                "pages": file_info['pages'],  # Same number of pages as original
                "filepath": output_path,
                "compression_level": compression_level,
                "original_size": os.path.getsize(file_info['filepath']),
                "compressed_size": os.path.getsize(output_path),
                "compression_ratio": 1 - (os.path.getsize(output_path) / os.path.getsize(file_info['filepath']))
            }

            # Store in pdf_storage
            self.pdf_storage[new_file_id] = pdf_info
            return pdf_info

        except Exception as e:
            raise Exception(f"Error compressing PDF: {str(e)}")

    def edit_metadata(self, file_id, metadata, preview_only=False):
        """
        Edit metadata of a PDF file

        Args:
            file_id: ID of the PDF to edit
            metadata: Dictionary with metadata fields (title, author, subject, keywords)
            preview_only: Whether this is just a preview

        Returns:
            Dictionary with updated PDF info
        """
        if file_id not in self.pdf_storage:
            raise Exception("File not found")

        file_info = self.pdf_storage[file_id]

        try:
            # Initialize PDF reader and writer
            reader = PdfReader(file_info['filepath'])
            writer = PdfWriter()

            # Add all pages from the original document
            for page in reader.pages:
                writer.add_page(page)

            # Prepare metadata
            meta = {}
            if metadata.get("title"):
                meta["/Title"] = metadata["title"]
            if metadata.get("author"):
                meta["/Author"] = metadata["author"]
            if metadata.get("subject"):
                meta["/Subject"] = metadata["subject"]
            if metadata.get("keywords"):
                meta["/Keywords"] = metadata["keywords"]

            # Apply metadata
            writer.add_metadata(meta)

            # Set output path
            if preview_only:
                new_file_id = str(uuid.uuid4())
                new_filename = f"preview_metadata_{file_info['filename']}"
                output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")
            else:
                new_file_id = str(uuid.uuid4())
                new_filename = f"metadata_{file_info['filename']}"
                output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")

            # Write the PDF with updated metadata
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            # Create file info
            pdf_info = {
                "id": new_file_id,
                "filename": new_filename,
                "pages": len(reader.pages),
                "filepath": output_path,
                "preview": preview_only,
                "metadata": metadata
            }

            # Store in pdf_storage
            self.pdf_storage[new_file_id] = pdf_info
            return pdf_info

        except Exception as e:
            raise Exception(f"Error editing metadata: {str(e)}")

    def get_metadata(self, file_id):
        """Get metadata from a PDF file"""
        if file_id not in self.pdf_storage:
            raise Exception("File not found")

        file_info = self.pdf_storage[file_id]

        try:
            # Try with PyPDF first
            try:
                reader = PdfReader(file_info['filepath'])
                if reader.metadata:
                    metadata = reader.metadata

                    # Extract metadata fields
                    result = {}
                    if metadata.title:
                        result["title"] = metadata.title
                    if metadata.author:
                        result["author"] = metadata.author
                    if metadata.subject:
                        result["subject"] = metadata.subject
                    if metadata.keywords:
                        result["keywords"] = metadata.keywords

                    return result
                else:
                    return {}

            except Exception as e:
                # If PyPDF fails, try with PyMuPDF
                doc = fitz.open(file_info['filepath'])
                metadata = doc.metadata

                # Extract metadata fields
                result = {}
                if "title" in metadata and metadata["title"]:
                    result["title"] = metadata["title"]
                if "author" in metadata and metadata["author"]:
                    result["author"] = metadata["author"]
                if "subject" in metadata and metadata["subject"]:
                    result["subject"] = metadata["subject"]
                if "keywords" in metadata and metadata["keywords"]:
                    result["keywords"] = metadata["keywords"]

                doc.close()
                return result

        except Exception as e:
            # Return empty metadata if extraction fails
            print(f"Error extracting metadata: {str(e)}")
            return {}

    def edit_metadata(self, file_id, metadata, preview_only=False):
        """Edit metadata of a PDF file"""
        if file_id not in self.pdf_storage:
            raise Exception("File not found")

        file_info = self.pdf_storage[file_id]

        try:
            # Try with PyPDF first
            try:
                reader = PdfReader(file_info['filepath'])
                writer = PdfWriter()

                # Add all pages from the original document
                for page in reader.pages:
                    writer.add_page(page)

                # Prepare metadata
                meta = {}
                if metadata.get("title"):
                    meta["/Title"] = metadata["title"]
                if metadata.get("author"):
                    meta["/Author"] = metadata["author"]
                if metadata.get("subject"):
                    meta["/Subject"] = metadata["subject"]
                if metadata.get("keywords"):
                    meta["/Keywords"] = metadata["keywords"]

                # Apply metadata
                writer.add_metadata(meta)

                # Set output path
                if preview_only:
                    new_file_id = str(uuid.uuid4())
                    new_filename = f"preview_metadata_{file_info['filename']}"
                    output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")
                else:
                    new_file_id = str(uuid.uuid4())
                    new_filename = f"metadata_{file_info['filename']}"
                    output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")

                # Write the PDF with updated metadata
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)

            except Exception as e:
                # If PyPDF fails, try with PyMuPDF
                doc = fitz.open(file_info['filepath'])

                # Add metadata
                meta = {}
                if metadata.get("title"):
                    meta["title"] = metadata["title"]
                if metadata.get("author"):
                    meta["author"] = metadata["author"]
                if metadata.get("subject"):
                    meta["subject"] = metadata["subject"]
                if metadata.get("keywords"):
                    meta["keywords"] = metadata["keywords"]

                # Update the document's metadata
                doc.set_metadata(meta)

                # Set output path
                if preview_only:
                    new_file_id = str(uuid.uuid4())
                    new_filename = f"preview_metadata_{file_info['filename']}"
                    output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")
                else:
                    new_file_id = str(uuid.uuid4())
                    new_filename = f"metadata_{file_info['filename']}"
                    output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")

                # Save the PDF with updated metadata
                doc.save(output_path)
                doc.close()

            # Create file info
            pdf_info = {
                "id": new_file_id,
                "filename": new_filename,
                "pages": file_info['pages'],
                "filepath": output_path,
                "preview": preview_only,
                "metadata": metadata
            }

            # Store in pdf_storage
            self.pdf_storage[new_file_id] = pdf_info
            return pdf_info

        except Exception as e:
            raise Exception(f"Error editing metadata: {str(e)}")

    def protect_pdf(self, file_id, user_password, owner_password=None,
                   allow_printing=True, allow_copying=True):
        """
        Add password protection to a PDF file

        Args:
            file_id: ID of the PDF to protect
            user_password: Password required to open the document
            owner_password: Password with full permissions (defaults to user_password if None)
            allow_printing: Whether to allow printing
            allow_copying: Whether to allow copying content

        Returns:
            Dictionary with protected PDF info
        """
        if file_id not in self.pdf_storage:
            raise Exception("File not found")

        file_info = self.pdf_storage[file_id]

        try:
            # Initialize PDF reader and writer
            reader = PdfReader(file_info['filepath'])
            writer = PdfWriter()

            # Add all pages from the original document
            for page in reader.pages:
                writer.add_page(page)

            # Set permissions - PyPDF permissions are bit flags
            permissions = 0
            if allow_printing:
                permissions |= 4  # Print document (bit 2)
            if allow_copying:
                permissions |= 16  # Extract content (bit 4)

            # Apply encryption
            if owner_password is None or owner_password == "":
                owner_password = user_password

            # Ensure we use the more secure 128-bit encryption
            writer.encrypt(
                user_password=user_password,
                owner_password=owner_password,
                use_128bit=True,
                permissions_flag=permissions
            )

            # Set output path
            new_file_id = str(uuid.uuid4())
            new_filename = f"protected_{file_info['filename']}"
            output_path = os.path.join(self.upload_folder, f"{new_file_id}_{new_filename}")

            # Write the protected PDF
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            # Verify the PDF is actually password-protected
            try:
                # Try to open the PDF without a password - should raise an exception
                verify_reader = PdfReader(output_path)

                # If we got here, the PDF isn't properly protected
                # Let's try a different method with PyMuPDF
                try:
                    doc = fitz.open(file_info['filepath'])

                    # Apply permissions and encryption
                    perm = 0
                    if allow_printing:
                        perm |= fitz.PDF_PERM_PRINT
                    if allow_copying:
                        perm |= fitz.PDF_PERM_COPY

                    # Save with encryption
                    doc.save(
                        output_path,
                        encryption=fitz.PDF_ENCRYPT_AES_128,  # Use AES 128-bit encryption
                        user_pw=user_password,
                        owner_pw=owner_password,
                        permissions=perm
                    )
                    doc.close()
                except Exception as mupdf_error:
                    print(f"PyMuPDF protection failed: {mupdf_error}")
                    # Just continue with original output
            except:
                # Exception raised means the PDF is properly password-protected
                pass

            # Create file info
            pdf_info = {
                "id": new_file_id,
                "filename": new_filename,
                "pages": len(reader.pages),
                "filepath": output_path,
                "protected": True
            }

            # Store in pdf_storage
            self.pdf_storage[new_file_id] = pdf_info
            return pdf_info

        except Exception as e:
            raise Exception(f"Error adding password protection: {str(e)}")

    def convert_images_to_pdf(self, image_files, page_size='A4', orientation='portrait'):
        """
        Convert images to a single PDF file

        Args:
            image_files: List of image file objects
            page_size: Page size (A4, Letter, etc.)
            orientation: Page orientation (portrait, landscape)

        Returns:
            PDF file info dictionary
        """
        try:
            # Define page dimensions based on size and orientation
            page_sizes = {
                'A4': (210, 297),  # Width, height in mm
                'A5': (148, 210),
                'Letter': (215.9, 279.4),
                'Legal': (215.9, 355.6)
            }

            # Get the selected page size
            width_mm, height_mm = page_sizes.get(page_size, page_sizes['A4'])

            # Swap dimensions if landscape
            if orientation.lower() == 'landscape':
                width_mm, height_mm = height_mm, width_mm

            # Convert mm to points (1 inch = 25.4 mm, 1 inch = 72 points)
            width_pt = width_mm * 72 / 25.4
            height_pt = height_mm * 72 / 25.4

            # Create a new PDF file with unique ID
            file_id = str(uuid.uuid4())
            filename = "converted_images.pdf"
            output_path = os.path.join(self.upload_folder, f"{file_id}_{filename}")

            # Save image files to temporary files
            temp_files = []
            for img_file in image_files:
                temp_path = os.path.join(tempfile.gettempdir(), secure_filename(img_file.filename))
                img_file.save(temp_path)
                temp_files.append(temp_path)

            # Initialize PDF writer
            writer = PdfWriter()

            # Process each image
            for img_path in temp_files:
                # Open image with PIL
                img = Image.open(img_path)

                # Convert to RGB if RGBA (for transparency handling)
                if img.mode == 'RGBA':
                    img = img.convert('RGB')

                # Resize image to fit the page with margins
                margin_pt = 10  # 10pt margin
                content_width = width_pt - 2 * margin_pt
                content_height = height_pt - 2 * margin_pt

                # Calculate scaling ratio to fit the image within the content area
                img_ratio = img.width / img.height
                content_ratio = content_width / content_height

                if img_ratio > content_ratio:
                    # Image is wider than the content area ratio
                    new_width = content_width
                    new_height = content_width / img_ratio
                else:
                    # Image is taller than the content area ratio
                    new_height = content_height
                    new_width = content_height * img_ratio

                img = img.resize((int(new_width), int(new_height)), Image.LANCZOS)

                # Create a PDF from the image
                pdf_bytes = BytesIO()
                img.save(pdf_bytes, format='PDF')
                pdf_bytes.seek(0)

                # Add to the writer
                reader = PdfReader(pdf_bytes)
                writer.add_page(reader.pages[0])

            # Write the combined PDF
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            # Cleanup temporary files
            for temp_path in temp_files:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            # Create file info
            pdf_info = {
                "id": file_id,
                "filename": filename,
                "pages": len(temp_files),
                "filepath": output_path
            }

            self.pdf_storage[file_id] = pdf_info
            return pdf_info

        except Exception as e:
            # Clean up any temporary files
            for temp_path in temp_files if 'temp_files' in locals() else []:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            raise Exception(f"Error converting images to PDF: {str(e)}")

    def convert_pdf_to_images(self, file_id, format='png', dpi=300, pages=None, create_zip=True):
        """
        Convert PDF pages to images

        Args:
            file_id: ID of the PDF to convert
            format: Output image format (png, jpg)
            dpi: Image resolution (dots per inch)
            pages: List of pages to convert (1-indexed), None for all pages
            create_zip: Whether to create a ZIP archive for multiple images

        Returns:
            List of dictionaries with image file info
        """
        if file_id not in self.pdf_storage:
            raise Exception("File not found")

        file_info = self.pdf_storage[file_id]
        pdf_file_path = file_info['filepath']

        try:
            # Calculate zoom factor from DPI (default PDF resolution is 72 DPI)
            zoom = dpi / 72

            # Create output folder for images
            output_folder = os.path.join(self.upload_folder, f"images_{file_id}")
            os.makedirs(output_folder, exist_ok=True)

            # Open the PDF file with PyMuPDF
            pdf_document = fitz.open(pdf_file_path)
            total_pages = len(pdf_document)
            result_files = []

            # Normalize format
            format = format.lower()
            if format not in ['png', 'jpg', 'jpeg']:
                format = 'png'  # Default to PNG if invalid format

            # Set proper MIME type
            mime_type = f"image/{format}"
            if format == 'jpg':
                mime_type = "image/jpeg"

            # Determine which pages to convert
            if pages is None:
                # Convert all pages
                pages_to_convert = range(total_pages)
            else:
                # Convert only specified pages (convert from 1-indexed to 0-indexed)
                pages_to_convert = [p-1 for p in pages if 1 <= p <= total_pages]

            # Process each page
            for i in pages_to_convert:
                # Get the page
                page = pdf_document[i]

                # Set the matrix for rendering (controls resolution)
                matrix = fitz.Matrix(zoom, zoom)

                # Render the page as a pixmap
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)

                # Define the output filename
                image_id = str(uuid.uuid4())
                image_filename = f"page_{i+1}.{format}"
                image_filepath = os.path.join(output_folder, image_filename)

                # Save the pixmap as an image file
                pixmap.save(image_filepath)

                # Store metadata
                image_info = {
                    "id": image_id,
                    "filename": image_filename,
                    "filepath": image_filepath,
                    "type": mime_type
                }

                self.pdf_storage[image_id] = image_info
                result_files.append(image_info)

            pdf_document.close()

            # Create ZIP if needed and there are multiple files
            if create_zip and len(result_files) > 1:
                zip_id = str(uuid.uuid4())
                zip_filename = f"images_{file_id}.zip"
                zip_path = os.path.join(self.upload_folder, zip_filename)

                with zipfile.ZipFile(zip_path, 'w') as zip_file:
                    for file_info in result_files:
                        zip_file.write(file_info['filepath'], file_info['filename'])

                # Add zip info
                zip_info = {
                    "id": zip_id,
                    "filename": zip_filename,
                    "filepath": zip_path,
                    "type": "application/zip"
                }
                self.pdf_storage[zip_id] = zip_info

                # Add zip info to result files
                for file_info in result_files:
                    file_info['zip_id'] = zip_id

            return result_files

        except Exception as e:
            raise Exception(f"Error converting PDF to images: {str(e)}")
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