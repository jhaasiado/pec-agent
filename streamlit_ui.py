import os
import json
import streamlit as st
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI

# === Load environment variables ===
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# === Streamlit page config ===
st.set_page_config(
    page_title="PEC RAG Agent",
    layout="wide"
)

st.title("🔌 PEC Chapter 2 Q&A Agent")
st.markdown("Ask questions about PEC Chapter 2 and get answers with cited sections.")

# === Cached loader for FAISS index ===
@st.cache_resource
def load_vectorstore(index_path: str):
    index_file = os.path.join(index_path, "index.faiss")
    embedding_model = OpenAIEmbeddings(api_key=openai_api_key)

    if os.path.exists(index_file):
        return FAISS.load_local(index_path, embedding_model, allow_dangerous_deserialization=True)
    else:
        # load pre‑chunked JSON
        with open("../data/pec_chunks_chapter2.json", "r", encoding="utf-8") as f:
            chunks = json.load(f)
        docs = [Document(page_content=item["text"], metadata=item["metadata"]) for item in chunks]
        vs = FAISS.from_documents(docs, embedding_model)
        vs.save_local(index_path)
        return vs

vectorstore = load_vectorstore("faiss_index")

# === RAG query function ===
def query_pec(query: str) -> dict:
    results = vectorstore.similarity_search(query, k=5)

    contexts = [
        {"metadata": doc.metadata, "content": doc.page_content}
        for doc in results
    ]

    prompt_context = "\n\n".join([c["content"] for c in contexts])
    prompt = f"""You are an expert in the Philippine Electrical Code (PEC).\nAnswer the following question using the official code content below:\n\n====\n{prompt_context}\n====\n\nQuestion: {query}\nAnswer:"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    return {"answer": response.choices[0].message.content, "contexts": contexts}

# === Streamlit UI ===
query = st.text_input("Enter your question about PEC Chapter 2:")
if st.button("Ask PEC Agent"):
    if not query:
        st.warning("Please type a question before submitting.")
    else:
        with st.spinner("Querying PEC..."):
            result = query_pec(query)

        st.subheader("📘 Answer")
        st.write(result["answer"])

        st.subheader("🔎 Cited Sections")
        for idx, ctx in enumerate(result["contexts"], start=1):
            meta = ctx["metadata"]
            section_id = meta.get("section", meta.get("id", None)) or f"#{idx}"
            title = meta.get("section_title", "")
            st.markdown(f"**Section {section_id} — {title}**")
            st.write(ctx["content"])