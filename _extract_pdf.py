import sys
try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        print("No pypdf installed")
        sys.exit(1)
path = r"C:\Users\dst\OneDrive - Byggros Holding A S\BG Byggros (BDK) - General\Personlige mapper\BDK\Dan Strand\Beregningsværktøj\rapportskabeloner\EKSEMPEL - Arkil - Dimensionering MSL - genbrugsstabil 060520.pdf"
r = PdfReader(path)
print("Num pages:", len(r.pages))
for i, p in enumerate(r.pages, 1):
    print(f"=== Page {i} ===")
    print(p.extract_text())
    print()
