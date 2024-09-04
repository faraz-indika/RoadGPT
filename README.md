# RoadGPT
1. Download PDFs using DownloadPDFs.py file, You have to option to select the year from which you want the PDFs
2. Add a .env file with the following variables
    ```
    path_to_pdf_directory = "./PDFs/"
    train_embeddings = 'false'
    project_id = "id_of_project_on_vertex_ai"
    location = "location_of_project_on_vertex_ai"
    ```
3. Put train_embeddings = 'true' if Vectorstore and Docstore are not present or are to be trained again for new  PDFs
4. Create a conda environment with Python 3.12.4 and Install the necessary libraries
5. Authenticate yourself with Vertex AI Platform