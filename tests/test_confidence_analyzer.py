from app.services.confidence_analyzer import ConfidenceAnalyzer


def test_analyze_heatmap_segments_multi_sentence_answer():
    analyzer = ConfidenceAnalyzer()
    qa_pairs = [
        {
            "question": "Tell me about a challenging project.",
            "answer": (
                "I led the migration of our payment service to a new architecture. "
                "Um, I think it was maybe a bit risky. "
                "We successfully cut latency by 40% and the outcome was excellent."
            ),
            "category": "T",
            "question_number": 1,
        }
    ]

    results = analyzer.analyze_heatmap(qa_pairs)

    assert len(results) == 1
    question_result = results[0]
    assert question_result["skipped"] is False
    segments = question_result["segments"]
    assert len(segments) == 3

    # start/end pct monotonic and covering the whole answer
    for i in range(len(segments) - 1):
        assert segments[i]["end_pct"] == segments[i + 1]["start_pct"]
    assert segments[0]["start_pct"] == 0.0
    assert segments[-1]["end_pct"] == 1.0

    # weakest segment should be the hedging/filler-heavy middle sentence
    weakest_index = question_result["weakest_segment_index"]
    assert weakest_index == 1
    assert "hedge" in segments[1]["flags"]


def test_analyze_heatmap_skipped_answer():
    analyzer = ConfidenceAnalyzer()
    qa_pairs = [
        {"question": "Q1", "answer": "[SKIPPED]", "category": "T", "question_number": 1},
    ]

    results = analyzer.analyze_heatmap(qa_pairs)

    assert results[0]["skipped"] is True
    assert results[0]["segments"] == []
    assert results[0]["weakest_segment_index"] is None


def test_analyze_heatmap_empty_qa_pairs():
    analyzer = ConfidenceAnalyzer()
    assert analyzer.analyze_heatmap([]) == []
