'''
Description: 
Author: colin gao
Date: 2023-05-05 13:32:05
LastEditTime: 2023-05-09 16:14:10
'''
import os, json
os.environ["OPENAI_API_KEY"] = "sk-***"

from colorama import init, Fore, Style

from langchain.document_loaders import TextLoader, DirectoryLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI

from configs.config import *
from templates import CONDENSE_PROMPT, QA_PROMPT

init()

loader = DirectoryLoader(DOCS_ROOT_PATH, glob="**/*.txt", loader_cls=TextLoader)
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP
)
documents = text_splitter.split_documents(documents)

embeddings = OpenAIEmbeddings(model='text-embedding-ada-002')

# 将数据存入向量存储 TODO pinecone
if INGEST:
    vector_store = Chroma.from_documents(
        documents, 
        embeddings, 
        collection_name="my_collection", 
        persist_directory=VS_ROOT_PATH
    )
else:
    vector_store = Chroma(
        persist_directory=VS_ROOT_PATH,
        embedding_function=embeddings,
        collection_name="my_collection"
    )

llm_model = ChatOpenAI(
    model_name='gpt-3.5-turbo', 
    temperature=TEMPERTURE,
    streaming=STREAMING)

retriever = vector_store.as_retriever(
    search_kwargs={"k": VECTOR_SEARCH_TOP_K},
    qa_template=QA_PROMPT,
    question_generator_template=CONDENSE_PROMPT
)

qa = ConversationalRetrievalChain.from_llm(
    llm=llm_model, retriever=retriever, return_source_documents=True)

chat_history = []

while True:
    question = input("Please enter your question (or type 'exit' to end): ")
    if question.lower() == 'exit':
        break

    # 开始发送问题 chat_history 为必须参数，用于存储对话历史
    result = qa({'question': question, 'chat_history': chat_history})
    chat_history.append((question, result['answer']))

    print(f'{Fore.BLUE}{Style.BRIGHT}AI:{Fore.RESET}{Style.NORMAL} {result["answer"]}')

    # Write chat history to a JSON file
    with open('chat_history.json', 'w') as json_file:
        json.dump(chat_history, json_file, ensure_ascii=False, indent=4)

