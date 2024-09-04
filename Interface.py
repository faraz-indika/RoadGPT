import time
import gradio as gr
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes
from typing import Iterable

class Seafoam(Base):
    def __init__(
        self,
        *,
        primary_hue: colors.Color | str = colors.emerald,
        secondary_hue: colors.Color | str = colors.blue,
        neutral_hue: colors.Color | str = colors.blue,
        spacing_size: sizes.Size | str = sizes.spacing_md,
        radius_size: sizes.Size | str = sizes.radius_md,
        text_size: sizes.Size | str = sizes.text_lg,
        font: fonts.Font
        | str
        | Iterable[fonts.Font | str] = (
            fonts.GoogleFont("Quicksand"),
            "ui-sans-serif",
            "sans-serif",
        ),
        font_mono: fonts.Font
        | str
        | Iterable[fonts.Font | str] = (
            fonts.GoogleFont("IBM Plex Mono"),
            "ui-monospace",
            "monospace",
        ),
    ):
        super().__init__(
            primary_hue=primary_hue,
            secondary_hue=secondary_hue,
            neutral_hue=neutral_hue,
            spacing_size=spacing_size,
            radius_size=radius_size,
            text_size=text_size,
            font=font,
            font_mono=font_mono,
        )
        super().set(
            body_background_fill="repeating-linear-gradient(240deg, #dff0ff, #ffffff)",
            body_background_fill_dark="repeating-linear-gradient(240deg, #dff0ff, #ffffff)",
            block_background_fill="linear-gradient(40deg, #dff0ff, #ffffff)",
            block_background_fill_dark="linear-gradient(40deg, #dff0ff, #ffffff)",
            button_primary_background_fill="linear-gradient(90deg, *primary_300, *secondary_400)",
            button_primary_background_fill_hover="linear-gradient(90deg, *primary_200, *secondary_300)",
            button_primary_text_color="white",
            button_primary_background_fill_dark="linear-gradient(90deg, *primary_600, *secondary_800)",
            slider_color="*secondary_300",
            slider_color_dark="*secondary_600",
            block_title_text_weight="600",
            block_border_width="3px",
            block_shadow="*shadow_drop_lg",
            button_shadow="*shadow_drop_lg",
            button_large_padding="32px",
        )

seafoam = Seafoam()

css = """
body {
    margin: 0;
    padding: 0;
}

#header {
    display: flex;
    justify-content: space-between;
    padding: 0 2rem;
    align-items: center;
    height: 4rem;
    box-shadow: 0 4px 2px -2px gray;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    background-color: white;
    z-index: 40;
}

#header img {
    width: 11rem;
}

#right_profile {
    display: flex;
    gap: 3rem;
    align-items: center;
}

#main-content {
    padding-top: 4rem;
}
#chatbot {
    height: 600px !important;
    border: none;
    border-radius: 8px;
    padding: 1rem;
}
#chatbot .gr-header {
    display: none !important;
}
#chat_input textarea {
    background: unset !important;
    color: black !important;
    padding: 10px !important;
}

#chat_input textarea::placeholder {
    color: #aaa !important;
}
footer {
    display: none !important;
}
"""

def chat_ui(chain):

    def add_links(response, context):
        sry = '''
        I am sorry, I dont have answer to your query. Please try rephrasing your question.
        '''
        if sry in response:
            return response
        links = [f'    <a href="{document.metadata['link']}#page={document.metadata['page'] + document.metadata['start']}" style="text-decoration:none;">{document.metadata['source']} : {document.metadata['page']}</a>' for document in context]
        links = ('').join(link for link in links)
        start = '''
        <html>
        <head>
        <title>Add Links</title>
        <style>
        a {
            text-decoration: none;
            padding: 5px 10px;
            border: 1px solid #ccc;
            border-radius: 20px;
            background-color: #b3cce6;
            color: #FFFFFF
        }
        </style>
        </head>
        <body>
        <p>Read more from:</p>
        <ul>'''
        end  = '''
        </ul>
        </body>
        </html>
        '''
        return response + start + links + end

    def print_like_dislike(x: gr.LikeData):
        print(x.index, x.value, x.liked)

    def add_message(history, message):
        history.append((message["text"], None))
        return history, gr.MultimodalTextbox(value=None, interactive=False)

    def chat_with_pdf(history):
        current_history = ''
        if len(history) > 1: current_history =f"Question By User: {history[-2][0]} /n Reply From Chatbot: {history[-2][1]}"
        last_message = history[-1][0]
        #Logging
        print(f'\nQUESTION: \n{last_message}')
        llm_response = chain.invoke({'input' : last_message, 'chat_history' : current_history})
        #Logging
        print('CONTEXT:')
        for doc in llm_response['context']:
            print(f'<--------------------<{doc.metadata['source']} - {doc.metadata['page']}>-------------------->')
            print(doc.page_content)
        response = llm_response["answer"]
        print(f'RESPONSE: \n{response}')
        history[-1][1] = ""
        for character in add_links(response, llm_response['context']):
            history[-1][1] += character
            # time.sleep(0.02)
            yield history

    with gr.Blocks(theme=seafoam, css=css) as demo:
        gr.HTML("""
        <div id="header">
            <div class="logo">
                <img src="https://assets-global.website-files.com/644be23bb1119de3135bc518/65e1ba2f16483846b3212fc9_RV%20font%20only%20HD%20FILE-p-500.png" alt="logo">
            </div>
            <div id="right_profile">
                <div class="notification">
                    <!-- Add your notification component here -->
                </div>
                <div class="profile_menu">
                    <!-- Add your profile menu component here -->
                </div>
            </div>
        </div>
        <div id="main-content">
        """)
        chatbot = gr.Chatbot(
            [],
            elem_id="chatbot",
            bubble_full_width=False
        )

        chat_input = gr.MultimodalTextbox(interactive=True, file_types=["image"], placeholder="Enter message...", show_label=False, elem_id="chat_input")

        chat_msg = chat_input.submit(add_message, [chatbot, chat_input], [chatbot, chat_input])
        bot_msg = chat_msg.then(chat_with_pdf, chatbot, chatbot, api_name="bot_response")
        bot_msg.then(lambda: gr.MultimodalTextbox(interactive=True), None, [chat_input])
        chatbot.like(print_like_dislike, None, None)
        gr.HTML("</div>")
    demo.queue()
    demo.launch(debug=True, show_api=False)