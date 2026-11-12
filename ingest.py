import argparse
import hashlib
from pathlib import Path
import fitz
from app.knowledge import ensure_index, embed


def chunks(text, size=800, overlap=100):
    text = ' '.join(text.split())
    step = size-overlap
    return [text[i:i+size] for i in range(0,len(text),step) if len(text[i:i+size]) > 80]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', default=None)
    args = parser.parse_args()
    
    if args.pdf:
        pdf = Path(args.pdf)
    else:
        # Fallback for Medical_book.pdf / medical_book.pdf across OS
        pdf = Path('data/Medical_book.pdf') if Path('data/Medical_book.pdf').exists() else Path('data/medical_book.pdf')

    if not pdf.exists():
        raise SystemExit(f'PDF not found: {pdf}')
    index = ensure_index()
    with fitz.open(pdf) as doc:
        batch = []
        for page_number, page in enumerate(doc, start=1):
            for part, content in enumerate(chunks(page.get_text()), start=1):
                key = hashlib.sha256(f'{pdf.name}:{page_number}:{part}:{content}'.encode()).hexdigest()
                batch.append((key,content,{'page':page_number,'text':content,'file':pdf.name}))
                if len(batch) >= 50:
                    vectors = embed([b[1] for b in batch])
                    index.upsert(vectors=[{'id':b[0],'values':v,'metadata':b[2]} for b,v in zip(batch,vectors)])
                    batch=[]
            if page_number % 50 == 0:
                print(f'Indexed pages: {page_number}/{len(doc)}',flush=True)
        if batch:
            vectors=embed([b[1] for b in batch])
            index.upsert(vectors=[{'id':b[0],'values':v,'metadata':b[2]} for b,v in zip(batch,vectors)])
    print('Ingestion complete')
if __name__ == '__main__': main()