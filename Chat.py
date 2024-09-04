import os
import warnings
warnings.filterwarnings("ignore")
from dotenv import load_dotenv
from distutils.util import strtobool
import vertexai
from DocumentLoader import pdf_loader
from DocumentRetriever import Retriever
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_google_vertexai import VertexAI
from Interface import chat_ui

load_dotenv()
DIRECTORY_PATH = os.getenv("path_to_pdf_directory")
TRAIN_EMBEDDINGS = strtobool(os.getenv("train_embeddings"))
PROJECT_ID = os.getenv("project_id")
LOCATION = os.getenv("location")

# Initialize Vertex AI SDK
vertexai.init(project=PROJECT_ID, location=LOCATION)

#Loading Documents 
documents = pdf_loader(DIRECTORY_PATH).load()

# Creating VectorStore and Generating Retreiver 
retreiver = Retriever(documents, TRAIN_EMBEDDINGS)

template = """
You are a Chatbot and you have to reply to Question by Users.
You are given information about Public Safety Standards of the Republic of India in the context below, The context also includes tables in html format.
<context>
{context}
</context>
Chat History:
<chat_history>
{chat_history}
</chat_history>
Answer from the context and Chat History only, if you don't know the answer, just reply "I am sorry, I dont have answer to your query. Please try rephrasing your question."
Question By User: {input}
"""

prompt = PromptTemplate(template=template, input_variables=['context', 'chat_history', 'input'])

llm = VertexAI(
    model_name="text-bison",
    max_output_tokens=1000,
    temperature=0,
    top_p=0.8,
    top_k=40,
    verbose=True,
)

stuff_documents_chain = create_stuff_documents_chain(llm, prompt)
chain = create_retrieval_chain(retreiver, stuff_documents_chain)

print("> LOADING INTERFACE")
chat_ui(chain)