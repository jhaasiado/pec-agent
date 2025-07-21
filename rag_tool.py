import os
import json
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI

# === Load environment ===
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# === Set FAISS index path ===
index_path = "faiss_index"
index_file = os.path.join(index_path, "index.faiss")

# === Initialize embedding model ===
embedding_model = OpenAIEmbeddings(api_key=openai_api_key)

# === Load or Create FAISS Index ===
if os.path.exists(index_file):
    print("📂 Loading existing FAISS index...")
    vectorstore = FAISS.load_local(index_path, embedding_model, allow_dangerous_deserialization=True)
else:
    print("🧠 Embedding PEC chunks from JSON...")
    with open("../data/pec_chunks_chapter2.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)

    docs = [Document(page_content=item["text"], metadata=item["metadata"]) for item in chunks]
    vectorstore = FAISS.from_documents(docs, embedding_model)
    vectorstore.save_local(index_path)
    print("💾 FAISS index saved to disk!")

# === Tool function ===
def query_pec(query: str) -> dict:
    results = vectorstore.similarity_search(query, k=5)

    # Build a list of full context sections
    contexts = [
        {
            "metadata": doc.metadata,
            "content": doc.page_content
        }
        for doc in results
    ]

    # Flatten just the text for the prompt
    prompt_context = "\n\n".join([c["content"] for c in contexts])

    prompt = f"""You are an expert in the Philippine Electrical Code (PEC).
Answer the following question using the official code content below:

====
{prompt_context}
====

Question: {query}
Answer:"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "answer": response.choices[0].message.content,
        "contexts": contexts,           # full sections
        "citations": [c["metadata"] for c in contexts]  # just the metadata
    }


# === Optional CLI for testing ===
if __name__ == "__main__":
    while True:
        q = input("\nAsk the PEC agent (type 'exit' to quit): ")
        if q.lower() in ["exit", "quit"]:
            break

        result = query_pec(q)
        print("\n📘 Answer:\n" + result["answer"])

        print("\n🔎 Cited Sections:")
        for idx, ctx in enumerate(result["contexts"], 1):
            meta = ctx["metadata"]
            # adjust the keys below to whatever your metadata contains,
            # e.g. meta['section'], meta['title'], etc.
            section_id = meta.get("section", meta.get("id", f"#{idx}"))
            title      = meta.get("title", "")
            print(f"\nSection {section_id} — {title}\n{ctx['content']}\n")
