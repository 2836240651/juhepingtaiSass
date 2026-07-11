import unittest
from unittest.mock import MagicMock, patch

from app.crawler import temu_crawler


class LiveCrawlLoginWaitTests(unittest.TestCase):
    def test_live_crawl_waits_for_login_before_calling_api_client(self):
        context_manager = MagicMock()
        browser_context = MagicMock()
        page = MagicMock()
        context_manager.__enter__.return_value = (MagicMock(), browser_context)
        context_manager.__exit__.return_value = None

        client = MagicMock()
        client.get_shop_info.return_value = ("Shop A", "mall-123")
        client.fetch_all_sales.return_value = []

        with patch.object(temu_crawler, "open_temu_context", return_value=context_manager), \
                patch.object(temu_crawler, "get_or_open_seller_page", return_value=page), \
                patch.object(temu_crawler, "wait_for_login_and_mall", return_value="mall-123") as wait, \
                patch.object(temu_crawler, "TemuApiClient", return_value=client):
            result = temu_crawler.crawl_temu_sales_live("2026-07-06", tenant_id=5)

        wait.assert_called_once_with(page, tenant_id=5)
        self.assertEqual(result["shops"][0]["shop_id"], "mall-123")


if __name__ == "__main__":
    unittest.main()
