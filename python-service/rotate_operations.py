from pypdf import PdfReader, PdfWriter
import os

class RotateOperations:
    def __init__(self, upload_folder):
        """Initialize rotate operations with upload folder for storage"""
        self.upload_folder = upload_folder

    def rotate_pages(self, pdf_file_path, output_path, pages_to_rotate, angle=90):
        """
        Rotate specific pages in a PDF file

        Args:
            pdf_file_path: Path to the source PDF
            output_path: Path for the output PDF
            pages_to_rotate: List of page numbers to rotate (1-indexed)
            angle: Rotation angle in degrees (90, 180, or 270)

        Returns:
            Path to the rotated PDF
        """
        try:
            # Validate angle
            if angle not in [90, 180, 270]:
                raise ValueError("Angle must be 90, 180, or 270 degrees")

            # Initialize PDF reader and writer
            reader = PdfReader(pdf_file_path)
            writer = PdfWriter()

            # Process each page
            for i, page in enumerate(reader.pages):
                page_num = i + 1

                # If the page should be rotated
                if page_num in pages_to_rotate:
                    # Get current rotation
                    current_rotation = page.get('/Rotate', 0)
                    # Calculate new rotation
                    new_rotation = (current_rotation + angle) % 360
                    # Set new rotation
                    page.rotate(angle)

                # Add page to writer
                writer.add_page(page)

            # Write output file
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            return output_path

        except Exception as e:
            raise Exception(f"Error rotating pages: {str(e)}")

    def rotate_all_pages(self, pdf_file_path, output_path, angle=90):
        """
        Rotate all pages in a PDF file

        Args:
            pdf_file_path: Path to the source PDF
            output_path: Path for the output PDF
            angle: Rotation angle in degrees (90, 180, or 270)

        Returns:
            Path to the rotated PDF
        """
        try:
            # Initialize PDF reader
            reader = PdfReader(pdf_file_path)

            # Get all page numbers
            all_pages = list(range(1, len(reader.pages) + 1))

            # Rotate all pages
            return self.rotate_pages(pdf_file_path, output_path, all_pages, angle)

        except Exception as e:
            raise Exception(f"Error rotating all pages: {str(e)}")

    def rotate_page_ranges(self, pdf_file_path, output_path, page_ranges, angle=90):
        """
        Rotate pages within specified ranges

        Args:
            pdf_file_path: Path to the source PDF
            output_path: Path for the output PDF
            page_ranges: List of ranges as dictionaries with 'start' and 'end' keys
            angle: Rotation angle in degrees (90, 180, or 270)

        Returns:
            Path to the rotated PDF
        """
        try:
            # Initialize PDF reader
            reader = PdfReader(pdf_file_path)

            # Calculate pages to rotate
            pages_to_rotate = []

            for page_range in page_ranges:
                start = int(page_range.get('start', 1))
                end = int(page_range.get('end', len(reader.pages)))

                # Validate range
                if start < 1:
                    start = 1
                if end > len(reader.pages):
                    end = len(reader.pages)

                # Add pages in range
                pages_to_rotate.extend(range(start, end + 1))

            # Remove duplicates
            pages_to_rotate = list(set(pages_to_rotate))

            # Rotate pages
            return self.rotate_pages(pdf_file_path, output_path, pages_to_rotate, angle)

        except Exception as e:
            raise Exception(f"Error rotating page ranges: {str(e)}")