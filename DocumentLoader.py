import os
from tabulate import tabulate
import pdfplumber
from operator import itemgetter
from langchain_core.documents import Document

class pdf_loader:

    def __init__(self, directory_path) -> None:
        self.directory_path = directory_path
        self.pdfs = [directory_path + pdf for pdf in os.listdir(directory_path)]

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
        for document in documents:
            if document.metadata['page'] == 1:
                index = documents.index(document)
                while index < len(documents) and isinstance(documents[index].metadata['page'], int):
                    final_docs.append(documents[index])
                    index += 1
        return final_docs

    def load(self):
        documents = []
        for file in self.pdfs:
            pdf = pdfplumber.open(file)
            doc_name = str(file[len(self.directory_path): -4])
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
                documents.append(Document(metadata={'source' : doc_name, 'page' : page_number}, page_content=self.clean_content(doc_page)))
            
        documents = self.clean_documents(documents)
        return documents