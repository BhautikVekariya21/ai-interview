from app.services.faq_service import fetch_faq_for_technology, list_supported_technologies


def test_supported_technologies_contains_python():
    items = list_supported_technologies()
    assert any(item["id"] == "python" for item in items)


def test_fetch_faq_for_technology_maps_answer(monkeypatch):
    def fake_fetch_json(path, params):
        if path == "/tags/python/faq":
            return {
                "items": [
                    {
                        "question_id": 101,
                        "accepted_answer_id": 9001,
                        "title": "How do I loop in Python?",
                        "link": "https://stackoverflow.com/questions/101/example",
                        "score": 42,
                        "answer_count": 3,
                        "tags": ["python", "loops"],
                    }
                ]
            }
        if path == "/questions/101/answers":
            return {
                "items": [
                    {
                        "answer_id": 9001,
                        "question_id": 101,
                        "score": 120,
                        "is_accepted": True,
                        "body": "<p>Use a <code>for</code> loop.</p><p>It is idiomatic.</p>",
                    }
                ]
            }
        raise AssertionError(f"Unexpected path {path}")

    monkeypatch.setattr("app.services.faq_service._fetch_json", fake_fetch_json)

    payload = fetch_faq_for_technology("python")

    assert payload["technology"]["id"] == "python"
    assert len(payload["items"]) == 1
    assert payload["items"][0]["question"] == "How do I loop in Python?"
    assert payload["items"][0]["answer"]["is_accepted"] is True
    assert "Use a for loop." in payload["items"][0]["answer"]["body_text"]


def test_fetch_faq_for_technology_sorts_high_score_first(monkeypatch):
    def fake_fetch_json(path, params):
        if path == "/tags/python/faq":
            return {
                "items": [
                    {
                        "question_id": 101,
                        "accepted_answer_id": 9001,
                        "title": "Lower score question",
                        "link": "https://stackoverflow.com/questions/101/example",
                        "score": 10,
                        "answer_count": 2,
                        "tags": ["python"],
                    },
                    {
                        "question_id": 102,
                        "accepted_answer_id": 9002,
                        "title": "Higher score question",
                        "link": "https://stackoverflow.com/questions/102/example",
                        "score": 80,
                        "answer_count": 4,
                        "tags": ["python"],
                    },
                ]
            }
        if path == "/questions/101;102/answers":
            return {
                "items": [
                    {
                        "answer_id": 9001,
                        "question_id": 101,
                        "score": 20,
                        "is_accepted": True,
                        "body": "<p>Answer one</p>",
                    },
                    {
                        "answer_id": 9002,
                        "question_id": 102,
                        "score": 50,
                        "is_accepted": True,
                        "body": "<p>Answer two</p>",
                    },
                ]
            }
        raise AssertionError(f"Unexpected path {path}")

    monkeypatch.setattr("app.services.faq_service._fetch_json", fake_fetch_json)

    payload = fetch_faq_for_technology("python")

    assert [item["question_id"] for item in payload["items"]] == [102, 101]
