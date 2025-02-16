import os
import gradio as gr
import anthropic
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings  # pip install langchain-openai
from langchain_chroma import Chroma           # pip install langchain-chroma
from langchain_community.llms import Anthropic
from datetime import datetime

DEBUG_MODE=True

##Run this script in the directory containing the dictionaries
# ==== Configuration ====
current_directory = os.getcwd()
TXT_FILES_DIR = os.path.join(current_directory, "SyvilleDesigns").lower()
CHROMA_DB_DIR = os.path.join(TXT_FILES_DIR, "chroma_db")

CHUNK_SIZE = 400
                # For general RAG applications, 300-600 words is a good balance.
                # For technical/legal documents, use larger chunks (600+).
                # For FAQs or structured text, smaller chunks (200-400) work better.
CHUNK_OVERLAP = 50   # 10 to 20% of chunk size 
TOP_K = 5         # Number of chunks to retrieve
COLLECTION_NAME = "my_syvilledesigns_collection"  # Arbitrary name for the Chroma collection

# ==== 0) Check latest time that the Chroma database was updated ====
def get_last_vdb_update():
    file_path = os.path.join(CHROMA_DB_DIR,"chroma.sqlie3")
    # Check if the file exists
    if os.path.exists(file_path):
        # Get the last modified time in seconds since epoch
        last_modified_time = os.path.getmtime(file_path)
    else:
        last_modified_time = 0
    # Convert to a readable format
    last_modified_date = datetime.fromtimestamp(last_modified_time)
    if DEBUG_MODE:
        print("Last Modified Date:", last_modified_date)

    # return last_modified_time
    # always return 0 till we have updated the updating of the vectordabase to be incremental AND remove old records
    return 0

# ==== 1) Load TXT documents from directory & subdirectories ====
def load_txt_files(directory, last_vdb_update = 0):
    """Reads all .txt files from the directory and its subdirectories."""
    documents = []
    step_counter = 0
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".txt"):
                step_counter +=1
                if step_counter < 15:
                    print(filename)
                filepath = os.path.join(root, filename)
                file_modified_time = os.path.getmtime(filepath)
                if file_modified_time > last_vdb_update:
                    with open(filepath, "r", encoding="utf-8") as file:
                        documents.append(file.read())
    if DEBUG_MODE:
        print(f"Number of documents added:{len(documents)}")
    return documents

# ==== 2) Process and encode documents into ChromaDB ====
def process_documents():
    """Loads, splits, and stores documents into ChromaDB."""
    print("🔍 Loading documents...")
    ## keep in mind that at this point it's incremental read.
    raw_docs = load_txt_files(TXT_FILES_DIR)

    # Split text into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    doc_chunks = []
    for doc in raw_docs:
        doc_chunks.extend(splitter.split_text(doc))

    print(f"📄 {len(doc_chunks)} document chunks processed.")

    # (A) Use from_texts to create or add to a collection in Chroma
    print("⚙️ Initializing ChromaDB with from_texts()...")
    vectorstore = Chroma.from_texts(
        texts=doc_chunks, 
        embedding=OpenAIEmbeddings(),
        persist_directory=CHROMA_DB_DIR,
        collection_name=COLLECTION_NAME
    )

    # (B) If needed, we can force persist the underlying DB:
    # vectorstore._client.persist()  # (internal method, optional)

    print(f"✅ {len(doc_chunks)} records loaded into ChromaDB collection '{COLLECTION_NAME}'.")


# ==== 3) Query ChromaDB for retrieval ====
def retrieve_context(query):
    """Retrieves relevant document chunks from ChromaDB."""
    # (A) Re-initialize Chroma using the same collection name & directory
    vectorstore = Chroma(
        embedding_function=OpenAIEmbeddings(),
        persist_directory=CHROMA_DB_DIR,
        collection_name=COLLECTION_NAME
    )

    # (B) similarity_search to retrieve top_k
    results = vectorstore.similarity_search(query, k=TOP_K)

    # Print debug info
    print(f"\n🔎 Found {len(results)} relevant segment(s) for query: '{query}'")
    for r in results:
        print(f"   Segment: {r.metadata}, length={len(r.page_content)}")

    # Combine them into a single string for the prompt
    ## context = "\n\n".join([res.page_content for res in results])
    return results


# ==== 4) Query Anthropic Claude ====
def ask_llm(prompt):
   # Call Anthropic Claude
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,
        temperature=0.7,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text

# ==== 5) Construct the full query and call Claude ====
def construct_and_query(query, results):
    """Constructs a query for Claude using the context from retrieved documents."""
    context = "\n".join(result.page_content for result in results)
     # Prompt for Claude
    prompt = f"""
        You are an AI assistant using a Retrieval-Augmented Generation (RAG) system.
        Only answer the question if you know the answer, don't make it up. If you don't have the answer, say it.
        Use the following context to answer the user's question:

        CONTEXT:
        {context}

        QUESTION:
        {query}

        ANSWER:
        """
    print(f"\n🤖 Sending prompt to Claude with {len(results)} segment(s).")
    return ask_llm(prompt)

# ==== 6) Build Gradio UI ====
def chatbot_ui(user_input):
    """Handles user queries through the Gradio UI."""
    vdb_results = retrieve_context(user_input)
    response = construct_and_query(user_input, vdb_results)
    return response


# ==== Main ====
load_dotenv()
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    raise ValueError("❌ ERROR: Missing Anthropic API Key. Add it to your .env file.")
    sys.exit(0)
os.environ['ANTHROPIC_API_KEY'] = ANTHROPIC_API_KEY
client = anthropic.Anthropic()

if __name__ == "__main__":
    # context, results = retrieve_context(user_input)
    # Run document processing once before starting the chatbot
    process_documents()

    # Launch Gradio interface
    iface = gr.Interface(
        fn=chatbot_ui,
        inputs="text",
        outputs="text",
        title="Syville Designs PA"
    )
    iface.launch()
