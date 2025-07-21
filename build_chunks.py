import json
from pathlib import Path

def chunk_pec_json(input_path: str, output_path: str):
    """
    Reads a PEC JSON file of articles → sections and writes out
    a flat list of chunks suitable for RAG embedding.

    Each chunk has:
      - id: the section identifier (e.g. "2.0.1.1")
      - text: cleaned text (newlines collapsed)
      - metadata:
          - chapter: first segment of id
          - article: first two segments of id joined by '.'
          - section_title: section["title"]
    """
    # load original nested structure
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))

    chunks = []
    for article in data:
        for section in article.get("sections", []):
            sec_id = section.get("section", "").strip()
            # collapse newlines into spaces and trim
            text = " ".join(section.get("text", "").splitlines()).strip()
            title = section.get("title", "").strip()

            parts = sec_id.split(".")
            chapter = parts[0] if parts else ""
            article_meta = ".".join(parts[:2]) if len(parts) >= 2 else ""

            chunks.append({
                "id": sec_id,
                "text": text,
                "metadata": {
                    "chapter": chapter,
                    "article": article_meta,
                    "section_title": title
                }
            })

    # write flat list out
    Path(output_path).write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    # example usage
    chunk_pec_json(
        input_path="../data_structured/chapter2_structured.json",
        output_path="../data/pec_chunks_chapter2.json"
    )
    print("✅ pec_chunks_chapter2.json generated!")
