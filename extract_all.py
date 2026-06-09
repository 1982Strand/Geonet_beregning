from pypdf import PdfReader

pdf_file = r'C:\geonet_beregning\Dokumenter og data\VD\Dimensionering - befæstelser og forstærkningsbelægninger.pdf'
reader = PdfReader(pdf_file)

# Extract all pages to search for Eo and bæreevne info
with open(r'C:\geonet_beregning\all_pages.txt', 'w', encoding='utf-8') as f:
    for page_num in range(len(reader.pages)):
        text = reader.pages[page_num].extract_text()
        f.write(f'\n\n========== PAGE {page_num + 1} ==========\n\n')
        f.write(text)
        f.write('\n')

print(f'Extracted all {len(reader.pages)} pages')
