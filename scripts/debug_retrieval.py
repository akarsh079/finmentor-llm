from finmentor.domain.concepts.loader import load_raw_conceptcards
from finmentor.domain.concepts.validator import validate_all_conceptcards
from finmentor.retrieval.retriever import retrieve

def main():
    raw = load_raw_conceptcards()
    cards = validate_all_conceptcards(raw)

    query = input("Query: ").strip()

    results, debug = retrieve(query, cards, top_k=5, debug=True)

    print("\n---RESULTS---\n")
    for i, card in enumerate(results):
        print(f"[{i}] {card.title}")
        meta = debug.get(i)
        if meta:
            print(f"    matched_terms: {meta.matched_terms}")
            print(f"    matched_fields: {meta.matched_fields}")
        print()

if __name__ == "__main__":
    main()
