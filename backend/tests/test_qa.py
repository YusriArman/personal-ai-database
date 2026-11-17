from app.answer.qa import REFUSAL_TEXT, answer_question, build_prompt, check_citations
from app.providers.fake import FakeProvider
from app.retrieve.search import hybrid_search


def test_check_citations_splits_valid_and_invalid():
    assert check_citations("a [1] b [3] c [1] d [9] [0]", 3) == ([1, 3], [9, 0])
    assert check_citations("no citations", 3) == ([], [])


def test_prompt_numbers_sources(indexed, provider):
    sources = hybrid_search(indexed, provider, "rockets", 2)
    prompt = build_prompt("What do rockets burn?", sources)
    assert "[1] " in prompt and "[2] " in prompt and prompt.endswith("Answer:")


def test_answer_with_valid_citation(indexed):
    provider = FakeProvider(script=["Rockets burn kerosene and oxygen [1]."])
    answer = answer_question(indexed, provider, "What do rockets burn?", abstain_threshold=0.1)
    assert not answer.abstained and answer.grounded and answer.cited == [1]
    assert answer.sources[0].title == "Alpha"


def test_invalid_citation_is_stripped_and_answer_flagged_ungrounded(indexed):
    provider = FakeProvider(script=["Rockets burn hydrogen [7]."])
    answer = answer_question(indexed, provider, "What do rockets burn?", abstain_threshold=0.1)
    assert answer.invalid_citations == [7] and "[7]" not in answer.text
    assert not answer.grounded and not answer.abstained


def test_low_similarity_abstains_without_calling_the_model(indexed):
    provider = FakeProvider(script=[])  # any generate() call would fail the test
    answer = answer_question(indexed, provider, "zebra xylophone quartz", abstain_threshold=0.5)
    assert answer.abstained and answer.reason == "low_similarity"
    assert answer.text == REFUSAL_TEXT and provider.prompts == []


def test_model_refusal_is_respected(indexed):
    provider = FakeProvider(script=["NOT_IN_NOTES"])
    answer = answer_question(indexed, provider, "rockets kerosene", abstain_threshold=0.1)
    assert answer.abstained and answer.reason == "model_declined"


def test_empty_index_abstains(conn, provider):
    answer = answer_question(conn, provider, "anything")
    assert answer.abstained and answer.reason == "no_sources"


def test_bare_citation_is_not_shown_as_an_answer(indexed):
    provider = FakeProvider(script=["[1]"])
    answer = answer_question(indexed, provider, "rockets kerosene", abstain_threshold=0.1)
    assert answer.abstained and answer.reason == "empty_answer" and answer.sources
