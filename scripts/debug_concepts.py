from finmentor.domain.concepts.loader import load_raw_conceptcards
from finmentor.domain.concepts.validator import validate_all_conceptcards

raw = load_raw_conceptcards()
cards = validate_all_conceptcards(raw)

for card in cards:
    print(card)
