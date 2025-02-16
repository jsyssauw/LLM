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
    print(f"\n🔎 Found {len(results)} relevant document chunks for query: '{query}'")
    return results

# ==== 4) Call Anthropic Claude and get response ====
def ask_claude(prompt):
    """Calls Anthropic Claude with the given prompt and returns the response."""
    load_dotenv()  ##CHANGING$: Load environment variables from .env file
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
    
    client = anthropic.Client(api_key)
    response = client.completions.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=500,
        temperature=0.7,
        prompt=prompt
    )
    return response.choices[0].text.strip()

# ==== 5) Construct the full query and call Claude ====
def construct_and_query_claude(query, results):
    """Constructs a query for Claude using the context from retrieved documents."""
    context = "\n".join(result.page_content for result in results)
    prompt = f"Context: {context}\n\nQuestion: {query}\n"
    return ask_claude(prompt)

# ==== 6) Handle user queries through the Gradio UI ====
def chatbot_ui(user_input):
    """Handles user queries through the Gradio UI."""
    results = retrieve_context(user_input)
    response = construct_and_query_claude(user_input, results)
    return response

# ==== Main ====
if __name__ == "__main__":
    # Run document processing once before starting the chatbot
    process_documents()
    # Launch Gradio interface
    iface = gr.Interface(
        fn=chatbot_ui,
        inputs="text",
        outputs="text",
        title="RAG Chatbot with Claude 3.5"
    )
    iface.launch()