from app.services.news_service import fetch_technology_news


def test_fetch_technology_news_filters_and_orders(monkeypatch):
    techcrunch_xml = """
    <rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
      <channel>
        <link>https://techcrunch.com/</link>
        <item>
          <title>AI hiring surges at major labs</title>
          <link>https://example.com/ai-hiring</link>
          <description><![CDATA[<p>Open roles and aggressive recruiting.</p>]]></description>
          <pubDate>Sun, 05 Apr 2026 10:00:00 GMT</pubDate>
          <media:content url="https://example.com/image-1.jpg" />
        </item>
        <item>
          <title>Mass layoffs shake device startup</title>
          <link>https://example.com/layoffs</link>
          <description><![CDATA[<p>Another workforce reduction.</p>]]></description>
          <pubDate>Sun, 04 Apr 2026 10:00:00 GMT</pubDate>
          <media:content url="https://example.com/image-2.jpg" />
        </item>
      </channel>
    </rss>
    """

    class FakeResponse:
      def __init__(self, text: str):
        self.content = text.encode("utf-8")
        self.text = text

      def raise_for_status(self):
        return None

    def fake_get(url, timeout=0, headers=None):
      return FakeResponse(techcrunch_xml)

    monkeypatch.setattr("app.services.news_service.requests.get", fake_get)

    payload = fetch_technology_news(category="hiring", limit=10)

    assert payload["success"] is True
    assert payload["items"]
    assert payload["items"][0]["category"] == "hiring"
    assert payload["items"][0]["image_url"] == "https://example.com/image-1.jpg"
