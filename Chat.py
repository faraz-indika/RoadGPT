import os
import warnings
warnings.filterwarnings("ignore")
from dotenv import load_dotenv
import vertexai
from DocumentLoader import pdf_loader
from DocumentRetriever import Retriever
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_google_vertexai import VertexAI
import gradio as gr, time

load_dotenv()
DIRECTORY_PATH = os.getenv("path_to_pdf_directory")
PROJECT_ID = os.getenv("project_id")
LOCATION = os.getenv("location")

# Initialize Vertex AI SDK
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Loading Documents
print("> LOADING DOCUMENTS...")
loader = pdf_loader(DIRECTORY_PATH)
documents = loader.load()
print("> DOCUMENTS LOADED")

print('> ACCESSING VECTORSTORE FOR RETRIEVER...')
retreiver = Retriever(documents)
print("> RETRIEVER LOADED")

template = """
You are a Chatbot and you have to reply to Question by Users.
You are given information about Public Safety Standards of the Republic of India in the context below, The context also includes tables in html format.
<context>
{context}
</context>
Answer from the context only, if you don't know the answer, just reply "I am sorry, I dont have answer to your query. Please try rephrasing your question."
Just reply to the answer Once Only, dont put up any follow up questions
Question By User: {input}
"""

prompt = PromptTemplate(template=template, input_variables=['context', 'input'])

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
CSS ="""
.contain { display: flex; flex-direction: column; }
.gradio-container { height: 100vh !important; }
#component-0 { height: 100%; }
#chatbot { flex-grow: 1; overflow: auto;}
"""

with gr.Blocks(css = CSS) as demo:
    gr.Markdown("# RoadGPT 🛣️")

    chatbot = gr.Chatbot(label="Chat history", elem_id="chatbot")
    message = gr.Textbox(label="Ask me a question!")
    clear = gr.Button("Clear")

    def user(user_message, chat_history):
        return gr.update(value="", interactive=False), chat_history + [[user_message, None]]

    def bot(chat_history):
        user_message = chat_history[-1][0]
        #Logging
        print(f'QUESTION: \n{user_message}')
        llm_response = chain.invoke({"input" : user_message, "chat_history" : []})
        #Logging
        print('CONTEXT:')
        for doc in llm_response['context']:
            print(f'<--------------------<{doc.metadata['source']} - {doc.metadata['page']}>-------------------->')
            print(doc.page_content)
        print(f'RESPONSE: \n{llm_response["answer"]}')
        bot_message = llm_response["answer"]
        chat_history[-1][1] = ""
        for character in bot_message:
            chat_history[-1][1] += character
            time.sleep(0.005)
            yield chat_history

    response = message.submit(user, [message, chatbot], [message, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    response.then(lambda: gr.update(interactive=True), None, [message], queue=False)

demo.queue()
demo.launch()
