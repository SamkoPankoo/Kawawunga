from pypdf import PdfReader, PdfWriter
import os
import uuid

class DeletePagesOperations:
    def __init__(self, upload_folder):
        """Initialize delete pages operations with upload folder for storage"""
        self.upload_folder = upload_folder

    def delete_pages(self, pdf_file_path, output_path, pages_to_delete):
        """
        Delete specific pages from a PDF file

        Args:
            pdf_file_path: Path to the source PDF
            output_path: Path for the output PDF
            pages_to_delete: List of page numbers to delete (1-indexed)

        Returns:
            Path to the modified PDF
        """
        try:
            # Initialize PDF reader and writer
            reader = PdfReader(pdf_file_path)
            writer = PdfWriter()

            # Process each page
            for i, page in enumerate(reader.pages):
                page_num = i + 1

                # If the page should not be deleted, add it to the writer
                if page_num not in pages_to_delete:
                    writer.add_page(page)

            # Write output file
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            return output_path

        except Exception as e:
            raise Exception(f"Error deleting pages: {str(e)}")

    def delete_page_ranges(self, pdf_file_path, output_path, page_ranges):
        """
        Delete pages within specified ranges

        Args:
            pdf_file_path: Path to the source PDF
            output_path: Path for the output PDF
            page_ranges: List of ranges as dictionaries with 'start' and 'end' keys

        Returns:
            Path to the modified PDF
        """
        try:
            # Initialize PDF reader
            reader = PdfReader(pdf_file_path)

            # Calculate pages to delete
            pages_to_delete = []

            for page_range in page_ranges:
                start = int(page_range.get('start', 1))
                end = int(page_range.get('end', len(reader.pages)))

                # Validate range
                if start < 1:
                    start = 1
                if end > len(reader.pages):
                    end = len(reader.pages)

                # Add pages in range
                pages_to_delete.extend(range(start, end + 1))

            # Remove duplicates
            pages_to_delete = list(set(pages_to_delete))

            # Delete pages
            return self.delete_pages(pdf_file_path, output_path, pages_to_delete)

        except Exception as e:
            raise Exception(f"Error deleting page ranges: {str(e)}")

    def keep_only_pages(self, pdf_file_path, output_path, pages_to_keep):
        """
        Keep only specified pages and delete all others

        Args:
            pdf_file_path: Path to the source PDF
            output_path: Path for the output PDF
            pages_to_keep: List of page numbers to keep (1-indexed)

        Returns:
            Path to the modified PDF
        """
        try:
            # Initialize PDF reader
            reader = PdfReader(pdf_file_path)

            # Calculate pages to delete
            total_pages = len(reader.pages)
            all_pages = list(range(1, total_pages + 1))
            pages_to_delete = [p for p in all_pages if p not in pages_to_keep]

            # Delete pages
            return self.delete_pages(pdf_file_path, output_path, pages_to_delete)

        except Exception as e:
            raise Exception(f"Error keeping only specified pages: {str(e)}")