import os
import json
from tabulate import tabulate
import pdfplumber
from operator import itemgetter
from langchain_core.documents import Document

FILE_PATH = "DocStore"
with open("link_directory.json", "r") as f:
    LINK_DIRECTORY = json.load(f)

class pdf_loader:

    def __init__(self, directory_path) -> None:
        self.directory_path = directory_path
        self.pdfs = [directory_path + pdf for pdf in os.listdir(directory_path)]

    def save_docs(self, documents, file_path):
        with open(file_path, 'w') as jsonl_file:
            for document in documents:
                jsonl_file.write(document.json() + '\n')

    def load_docs(self, file_path):
        documents = []
        with open(file_path, 'r') as jsonl_file:
            for line in jsonl_file:
                data = json.loads(line)
                obj = Document(**data)
                documents.append(obj)
        return documents

    def check_bboxes(self, word, table_bbox):
        l = word['x0'], word['top'], word['x1'], word['bottom']
        r = table_bbox
        return l[0] > r[0] and l[1] > r[1] and l[2] < r[2] and l[3] < r[3]

    def format_table(self, table):
        label = table[0][0]
        for lb_ind in range(len(table[0])):
            if table[0][lb_ind]:
                label = table[0][lb_ind]
            else:
                table[0][lb_ind] = label
        return str(tabulate(table, tablefmt='html'))

    def clean_content(self, x):
        return ' '.join(x.split()[1 : -1]) + ' ####' if  x!= '' and 'IRC:' in x.split()[0] else ' '.join(x.split()[0 : -1]) + ' ####' # Adding Page Break

    def clean_documents(self, documents):
        final_docs = []
        doc = ''
        for document in documents:
            current_doc = document.metadata['source']
            if doc != current_doc:
                doc = current_doc
                first_page = documents.index(document)
            if document.metadata['page'] == 1:
                index = documents.index(document)
                start = index - first_page
                while index < len(documents) and isinstance(documents[index].metadata['page'], int):
                    documents[index].metadata['start'] = start
                    final_docs.append(documents[index])
                    index += 1
        return final_docs

    def load(self):
        print("> LOADING DOCUMENTS...")
        if os.path.isfile(FILE_PATH):
            documents = self.load_docs(FILE_PATH)
            print("> DOCUMENTS LOADED")
            return documents
        documents = []
        doc_count = 0
        for file in self.pdfs:
            pdf = pdfplumber.open(file)
            doc_name = str(file[len(self.directory_path): -4])
            doc_link = LINK_DIRECTORY[doc_name]
            for page in pdf.pages:
                doc_page = ''
                tables = page.find_tables()
                table_bboxes = [i.bbox for i in tables]
                tables = [{'table': i.extract(), 'top': i.bbox[1]} for i in tables]
                non_table_words = [word for word in page.extract_words() if not any([self.check_bboxes(word, table_bbox) for table_bbox in table_bboxes])]
                for cluster in pdfplumber.utils.cluster_objects(non_table_words + tables, itemgetter('top'), tolerance=5):
                    if 'text' in cluster[0]:
                        try: 
                            doc_page += ' ' + ' '.join([i['text'] for i in cluster])
                        except:
                            pass                                # SOME PAGES ARE HORIZONTAL, FIX LATER
                    elif 'table' in cluster[0]:
                        doc_page += ' ' + self.format_table(cluster[0]['table'])
                page_number = int(doc_page.split()[-1]) if doc_page != '' and doc_page.split()[-1].isdigit() else None
                documents.append(Document(metadata={'source' : doc_name, 'link' : doc_link, 'page' : page_number}, page_content=self.clean_content(doc_page)))
            doc_count += 1
            print(f'- ({doc_count}/{len(self.pdfs)}) {doc_name}')
            
        documents = self.clean_documents(documents)
        self.save_docs(documents, FILE_PATH)
        print("> DOCUMENTS LOADED")
        return documents