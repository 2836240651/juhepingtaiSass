import sqlite3
import unittest
from unittest.mock import MagicMock, patch

from app.competitor_ingest import init_competitor_schema, replace_competitor_snapshot
from app.crawler import competitor_crawler
from app.crawler.competitor_crawler import (
    crawl_competitor_products,
    extract_price,
    extract_products_from_url,
    extract_sales_signal,
    normalize_product,
)


class CompetitorCrawlerParsingTest(unittest.TestCase):
    def test_extracts_price_and_sales_signal_from_card_text(self):
        text = "Portable Camping Light\n$12.49\n1.2K sold\nFree shipping"

        self.assertEqual(extract_price(text), 12.49)
        self.assertEqual(extract_sales_signal(text), 1200)

    def test_extracts_south_africa_rand_price(self):
        text = "Quick look\nCamping Chair\nR281\nOpen in new tab."

        self.assertEqual(extract_price(text), 281.0)

    def test_normalizes_product_with_stable_hash_id_when_url_has_no_id(self):
        product = normalize_product(
            {
                "text": "Foldable Storage Box\nUS$8.99\n328 sold",
                "url": "https://www.temu.com/example-item.html",
            },
            fallback_index=3,
            crawl_date="2026-07-06",
        )

        self.assertTrue(product["product_id"])
        self.assertEqual(product["product_name"], "Foldable Storage Box")
        self.assertEqual(product["price"], 8.99)
        self.assertEqual(product["daily_sales"], 328)
        self.assertEqual(product["total_sales"], 328)
        self.assertEqual(product["listed_at"], "2026-07-06")

    def test_normalizes_product_name_when_card_text_is_single_line(self):
        product = normalize_product(
            {
                "text": "API Real Lantern $12.49 1.2K sold",
                "url": "https://www.temu.com/goods-test123456.html",
            },
            fallback_index=1,
            crawl_date="2026-07-06",
        )

        self.assertEqual(product["product_name"], "API Real Lantern")

    def test_reports_browser_profile_unavailable_when_context_cannot_open(self):
        with patch(
            "app.crawler.competitor_crawler.collect_with_playwright",
            side_effect=RuntimeError(
                "BrowserType.launch_persistent_context: Target page, context or browser has been closed"
            ),
        ), patch.object(competitor_crawler, "close_tenant_profile_browsers", return_value=1):
            with self.assertRaisesRegex(RuntimeError, "COMPETITOR_BROWSER_PROFILE_UNAVAILABLE"):
                crawl_competitor_products(
                    tenant_id=5,
                    competitor_url="https://www.temu.com/mall.html?mall_id=3678530852421",
                    crawl_date="2026-07-06",
                )

    def test_force_closes_profile_and_retries_context_open_once(self):
        with patch(
            "app.crawler.competitor_crawler.collect_with_playwright",
            side_effect=[
                RuntimeError("BrowserType.launch_persistent_context: Target page, context or browser has been closed"),
                {
                    "status": "OK",
                    "captured_at": "2026-07-08T00:00:00+00:00",
                    "target": {"mall_id": "3678530852421"},
                    "raw_products": [
                        {
                            "goods_id": "601",
                            "goods_id_num": 601,
                            "title": "Fishing Lure Set",
                            "title_clean": "Fishing Lure Set",
                            "href": "https://www.temu.com/jp/fishing-lure-g-601.html",
                            "text": "Fishing Lure Set 378円 1,134 販売",
                            "price_yen": 378,
                            "sold_num": 1134,
                            "sold_text": "1,134 販売",
                        }
                    ],
                    "collection": {"final_url": "https://www.temu.com/jp/mall.html?mall_id=3678530852421"},
                },
            ],
        ) as collect, patch.object(competitor_crawler, "close_tenant_profile_browsers", return_value=1) as close_profiles:
            result = crawl_competitor_products(
                tenant_id=5,
                competitor_url="https://www.temu.com/mall.html?mall_id=3678530852421",
                crawl_date="2026-07-06",
            )

        self.assertEqual(close_profiles.call_count, 2)
        self.assertEqual(collect.call_count, 2)
        self.assertEqual(result["products"][0]["product_name"], "Fishing Lure Set")

    def test_reports_frontend_verification_when_page_redirects_after_initial_load(self):
        page = MagicMock()
        page.url = "https://www.temu.com/za/mall.html?mall_id=3678530852421"
        page_contains_store_unavailable_side_effects = [False, False]

        def wait_for_load_state(state, timeout=None):
            if state == "networkidle":
                page.url = (
                    "https://www.temu.com/bgn_verification.html?verifyCode=abc"
                    "&from=https%3A%2F%2Fwww.temu.com%2Fmall.html"
                )

        page.wait_for_load_state.side_effect = wait_for_load_state
        page.mouse = MagicMock()

        with patch.object(competitor_crawler, "human_pause", return_value=None), \
                patch.object(
                    competitor_crawler,
                    "page_contains_store_unavailable",
                    side_effect=lambda _page: page_contains_store_unavailable_side_effects.pop(0),
                ):
            with self.assertRaisesRegex(RuntimeError, "COMPETITOR_FRONTEND_LOGIN_REQUIRED"):
                extract_products_from_url(
                    page,
                    "https://www.temu.com/za/mall.html?mall_id=3678530852421",
                    max_products=20,
                )


class CompetitorSnapshotIngestTest(unittest.TestCase):
    def test_replaces_snapshot_for_same_competitor_and_date(self):
        conn = sqlite3.connect(":memory:")
        try:
            init_competitor_schema(conn)
            first = [
                {
                    "product_id": "p1",
                    "product_name": "Old Item",
                    "category": "",
                    "price": 10.0,
                    "daily_sales": 4,
                    "total_sales": 4,
                    "listed_at": "2026-07-06",
                    "url": "https://www.temu.com/p1",
                }
            ]
            second = [
                {
                    "product_id": "p2",
                    "product_name": "New Item",
                    "category": "",
                    "price": 11.0,
                    "daily_sales": 9,
                    "total_sales": 9,
                    "listed_at": "2026-07-06",
                    "url": "https://www.temu.com/p2",
                }
            ]

            self.assertEqual(replace_competitor_snapshot(conn, 1, "comp_a", "2026-07-06", first), 1)
            self.assertEqual(replace_competitor_snapshot(conn, 1, "comp_a", "2026-07-06", second), 1)

            rows = conn.execute(
                """
                SELECT product_id, product_name, daily_sales
                FROM temu_competitor_snapshot
                WHERE tenant_id = 1 AND competitor_id = 'comp_a' AND snapshot_date = '2026-07-06'
                """
            ).fetchall()
            self.assertEqual(rows, [("p2", "New Item", 9)])
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
