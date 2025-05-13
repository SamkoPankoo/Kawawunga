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

    def rotate_pdf(self, file_id, angle=90, pages=None):
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

                # Save rotated PDF
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

                # Save rotated PDF
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
                "filepath": output_path
            }

            self.pdf_storage[new_file_id] = pdf_info
            return pdf_info

        except Exception as e:
            raise Exception(f"Error rotating PDF: {str(e)}")

    def add_watermark(self, file_id, text, opacity=0.3, color="gray", size=36, angle=45, pages=None):
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

                # Save watermarked PDF
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

                # Save watermarked PDF
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
                "filepath": output_path
            }

            self.pdf_storage[new_file_id] = pdf_info
            return pdf_info

        except Exception as e:
            raise Exception(f"Error adding watermark to PDF: {str(e)}")

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

    def get_page_count(self, file_path):
        """Get the number of pages in a PDF file"""
        try:
            # Try with PyPDF first
            try:
                reader = PdfReader(file_path)
                return len(reader.pages)
            except:
                # If PyPDF fails, try with PyMuPDF
                doc = fitz.open(file_path)
                page_count = len(doc)
                doc.close()
                return page_count
        except Exception as e:
            print(f"Error getting page count: {str(e)}")
            return 0

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
        import time

        now = time.time()
        max_age_seconds = max_age_hours * 3600

        for root, dirs, files in os.walk(self.upload_folder):
            for filename in files:
                filepath = os.path.join(root, filename)
                if os.path.isfile(filepath):
                    file_age = now - os.path.getmtime(filepath)
                    if file_age > max_age_seconds:
                        try:
                            os.remove(filepath)
                            print(f"Removed old file: {filepath}")

                            # Remove from storage if present
                            for file_id, file_info in list(self.pdf_storage.items()):
                                if file_info.get('filepath') == filepath:
                                    del self.pdf_storage[file_id]
                                    break

                        except Exception as e:
                            print(f"Error removing file {filepath}: {str(e)}")