from pypdf import PdfReader
import sys

pdf_file = r'C:\geonet_beregning\Dokumenter og data\VD\Dimensionering - befæstelser og forstærkningsbelægninger.pdf'
reader = PdfReader(pdf_file)

# Extract pages 7-13 (which are pages 8-14 in the document)
with open(r'C:\geonet_beregning\traffic_pages.txt', 'w', encoding='utf-8') as f:
    for page_num in range(7, min(14, len(reader.pages))):
        text = reader.pages[page_num].extract_text()
        f.write(f'\n\n========== PAGE {page_num + 1} ==========\n\n')
        f.write(text)
        f.write('\n')

print('Extracted pages 8-14 to traffic_pages.txt')
