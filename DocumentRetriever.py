from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community import vectorstores
from langchain.storage import InMemoryStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers import ParentDocumentRetriever
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever

def Retriever(documents, train_embeddings):
    embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={'device':'cpu'})

    if train_embeddings:
        print('> DEPLOYING VECTORSTORE FOR RETRIEVER...')
        vectorstore = vectorstores.FAISS.from_documents(documents=documents, embedding=embedding_model)
        vectorstore.save_local("VectorStore")
    else:
        print('> ACCESSING VECTORSTORE FOR RETRIEVER...')
        vectorstore = vectorstores.FAISS.load_local("VectorStore", embedding_model, allow_dangerous_deserialization=True)

    child_splitter = RecursiveCharacterTextSplitter(separators=['\n'], chunk_size=50, chunk_overlap=0, length_function=len)   
    parent_splitter = RecursiveCharacterTextSplitter(separators=['####'], chunk_size=2000, chunk_overlap=100, length_function=len)   

    parent_retriever = ParentDocumentRetriever(
        vectorstore=vectorstore,
        docstore=InMemoryStore(),
        child_splitter=child_splitter,
        parent_splitter=parent_splitter
    )

    if train_embeddings:
        parent_retriever.add_documents(documents=documents)

    chunks = parent_splitter.split_documents(documents)
    keyword_retriever = BM25Retriever.from_documents(chunks)
    keyword_retriever.k = 2

    print("> RETRIEVER LOADED")
    return EnsembleRetriever(retrievers=[parent_retriever,keyword_retriever], weights=[0.5, 0.5])