from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import Chroma
from langchain_classic.chains import RetrievalQA
from langchain_classic.prompts import PromptTemplate

HROMA_PATH = './chroma_db'
EMBED_MODEL = 'nomic-embed-text'
LLM_MODEL   = 'qwen2.5-coder:3b'
CHROMA_PATH = './chroma_db'

PROMPT = PromptTemplate(
    template="""Eres un asistente de programacion. Usa el siguiente contexto
extraido de los documentos del usuario para responder su pregunta.
Si no encuentras la respuesta en el contexto, dilo claramente.
Responde en espanol salvo que el codigo lo requiera en ingles.

Contexto:
{context}

Pregunta: {question}

Respuesta:""",
    input_variables=['context', 'question']
)

def cargar_rag():
    embeddings = OllamaEmbeddings(model=EMBED_MODEL)
    vectorstore = Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=embeddings
    )
    llm = OllamaLLM(model=LLM_MODEL, temperature=0.1)
    retriever = vectorstore.as_retriever(search_kwargs={'k': 5})
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type='stuff',
        retriever=retriever,
        chain_type_kwargs={'prompt': PROMPT},
        return_source_documents=True
    )
    return chain

def main():
    print('Cargando RAG...')
    rag = cargar_rag()
    print('Listo. Escribe tu pregunta (o "salir" para terminar)\n')

    while True:
        pregunta = input('Tu: ').strip()
        if pregunta.lower() in ['salir', 'exit', 'quit']:
            break
        if not pregunta:
            continue

        resultado = rag.invoke({'query': pregunta})
        print(f'\nAsistente: {resultado["result"]}')

        # Mostrar fuentes usadas
        fuentes = set(d.metadata.get('source','?')
                      for d in resultado['source_documents'])
        print(f'[Fuentes: {', '.join(fuentes)}]\n')

if __name__ == '__main__':
    main()