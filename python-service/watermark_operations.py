from pypdf import PdfReader, PdfWriter
import math
import os
import uuid
import io
from reportlab.pdfgen import canvas
from reportlab.lib.colors import Color
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Mapa farieb
COLOR_MAP = {
    'black': (0, 0, 0),
    'gray': (0.5, 0.5, 0.5),
    'red': (1, 0, 0),
    'blue': (0, 0, 1),
    'green': (0, 0.5, 0),
}

class WatermarkOperations:
    def __init__(self, upload_folder):
        """Initialize watermark operations with upload folder for storage"""
        self.upload_folder = upload_folder

    def add_watermark(self, pdf_file_path, output_path, text, opacity=0.3, size=36, color='gray', angle=45, pages=None):
        """
        Add text watermark to PDF

        Args:
            pdf_file_path: Path to the source PDF
            output_path: Path for the output PDF
            text: Watermark text
            opacity: Watermark opacity (0-1)
            size: Font size
            color: Text color (string: black, gray, red, blue, green)
            angle: Rotation angle in degrees
            pages: List of pages to watermark (1-indexed), None for all pages

        Returns:
            Path to the watermarked PDF
        """
        try:
            # Inicializácia čítača PDF
            reader = PdfReader(pdf_file_path)
            writer = PdfWriter()

            # Zistíme veľkosť stránok
            pages_to_mark = pages or list(range(1, len(reader.pages) + 1))

            # Pre každú stránku
            for i, page in enumerate(reader.pages):
                page_num = i + 1

                # Ak je stránka v zozname na označenie, aplikujeme vodoznak
                if page_num in pages_to_mark:
                    # Získame rozmery stránky
                    media_box = page.mediabox
                    width = float(media_box.width)
                    height = float(media_box.height)

                    # Vytvoríme vodoznak
                    watermark = self._create_watermark(text, width, height, opacity, size, color, angle)

                    # Aplikujeme vodoznak na stránku
                    page.merge_page(watermark)

                # Pridáme stránku do výstupu
                writer.add_page(page)

            # Uložíme výsledný PDF
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            return output_path

        except Exception as e:
            raise Exception(f"Error adding watermark: {str(e)}")

    def _create_watermark(self, text, width, height, opacity, size, color, angle):
        """
        Vytvorí vodoznak ako PDF stránku

        Args:
            text: Text vodoznaku
            width: Šírka stránky
            height: Výška stránky
            opacity: Priehľadnosť (0-1)
            size: Veľkosť písma
            color: Farba (string)
            angle: Uhol otočenia v stupňoch

        Returns:
            PDF stránka s vodoznakom
        """
        # Vytvoríme PDF canvas
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=(width, height))

        # Nastavíme farbu
        color_tuple = COLOR_MAP.get(color, (0.5, 0.5, 0.5))  # Default to gray
        color_obj = Color(*color_tuple, alpha=opacity)
        c.setFillColor(color_obj)

        # Nastavíme font a veľkosť
        c.setFont("Helvetica", size)

        # Ak je uhol 0, vytvárame horizontálny vodoznak
        if angle == 0:
            # Horizontálne opakovanie
            x_step = width / 2
            y_step = height / 4
            for y in range(4):
                for x in range(2):
                    c.drawString(x * x_step, y * y_step + size/2, text)

        # Ak je uhol 90, vytvárame vertikálny vodoznak
        elif angle == 90:
            # Vertikálne opakovanie
            c.rotate(90)
            x_step = height / 2
            y_step = width / 4
            for y in range(4):
                for x in range(2):
                    c.drawString(x * x_step, -y * y_step - size/2, text)

        # Inak vytvárame diagonálny vodoznak
        else:
            # Diagonálne opakovanie
            diagonal_length = math.sqrt(width**2 + height**2)
            steps = int(diagonal_length / (len(text) * size / 10))

            c.saveState()
            c.translate(width/2, height/2)
            c.rotate(angle)

            step_size = diagonal_length / steps
            for i in range(-steps//2, steps//2 + 1):
                y_pos = i * step_size
                c.drawCentredString(0, y_pos, text)

            c.restoreState()

        c.save()

        # Vytvoríme PDF stránku z canvas
        packet.seek(0)
        watermark = PdfReader(packet)

        return watermark.pages[0]