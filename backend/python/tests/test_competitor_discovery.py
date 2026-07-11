import unittest

from app.crawler.competitor_discovery import build_search_url, build_discovery_candidates


class CompetitorDiscoveryTest(unittest.TestCase):
    def test_builds_za_search_url_with_encoded_keyword(self):
        self.assertEqual(
            build_search_url("fishing tackle", "za"),
            "https://www.temu.com/za/search_result.html?search_key=fishing%20tackle",
        )

    def test_groups_products_by_mall_id_in_search_order(self):
        search_url = build_search_url("fishing tackle", "za")
        items = [
            {
                "url": "https://www.temu.com/za/fishing-lure-g-601.html?mall_id=111&goods_id=601",
                "text": "Fishing Lure Set\n$5.99\n1.2K sold",
            },
            {
                "url": "https://www.temu.com/za/hooks-g-602.html?mall_id=111&goods_id=602",
                "text": "Fishing Hooks Kit\n$3.49\n500 sold",
            },
            {
                "url": "https://www.temu.com/za/fishing-line-g-603.html?mall_id=222&goods_id=603",
                "text": "Braided Fishing Line\n$7.25\n900 sold",
            },
        ]

        candidates = build_discovery_candidates(items, search_url=search_url, keyword="fishing tackle", limit=10)

        self.assertEqual(len(candidates), 2)
        self.assertEqual(candidates[0]["rank"], 1)
        self.assertEqual(candidates[0]["label"], "Fishing Lure Set")
        self.assertEqual(candidates[0]["url"], "https://www.temu.com/mall.html?mall_id=111")
        self.assertEqual(candidates[0]["sampleProductCount"], 2)
        self.assertTrue(candidates[0]["crawlable"])
        self.assertEqual(candidates[1]["rank"], 2)
        self.assertEqual(candidates[1]["url"], "https://www.temu.com/mall.html?mall_id=222")

    def test_falls_back_to_search_source_when_no_mall_id_is_available(self):
        search_url = build_search_url("fishing tackle", "za")
        items = [
            {
                "url": "https://www.temu.com/za/fishing-lure-g-601.html?goods_id=601",
                "text": "Fishing Lure Set\n$5.99\n1.2K sold",
            },
            {
                "url": "https://www.temu.com/za/fishing-hooks-g-602.html?goods_id=602",
                "text": "Fishing Hooks Kit\n$3.49\n500 sold",
            },
        ]

        candidates = build_discovery_candidates(items, search_url=search_url, keyword="fishing tackle", limit=10)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]["label"], "fishing tackle 搜索结果候选源")
        self.assertEqual(candidates[0]["url"], search_url)
        self.assertEqual(candidates[0]["sampleProductCount"], 2)
        self.assertEqual(candidates[0]["sourceType"], "search")


if __name__ == "__main__":
    unittest.main()
