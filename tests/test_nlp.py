from services.nlp_service import extract_skills_from_text


def test_extract_skills_simple():
    vocab = ['Python', 'Pandas', 'NumPy']
    text = 'I used Python and pandas for analysis.'
    extracted = extract_skills_from_text(text, vocab)
    names = [s for s, c in extracted]
    assert 'Python' in names
    assert 'Pandas' in names


def test_fuzzy_matching():
    vocab = ['TensorFlow', 'PyTorch', 'Scikit-learn']
    text = 'I have experience with pytorchh and scikit learn.'
    extracted = extract_skills_from_text(text, vocab, fuzzy_threshold=0.6)
    names = [s for s, c in extracted]
    assert 'PyTorch' in names
    assert 'Scikit-learn' in names
