import http.client
import json
import tempfile
import threading
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from app.platforms.temu_collector_service import create_server


class TemuCollectorServiceTest(unittest.TestCase):
    def test_health_and_capabilities(self):
        with run_test_server() as server:
            health = request_json(server, "GET", "/health")
            capabilities = request_json(server, "GET", "/capabilities")

        self.assertEqual(health["status"], "ok")
        self.assertIn("temu", capabilities["platforms"])
        self.assertIn("raw_payload", capabilities["supported_evidence"])
        self.assertIn("har", capabilities["supported_evidence"])
        self.assertIn("authorized_browser", capabilities["supported_evidence"])

    def test_fetch_writes_raw_products_from_inline_payload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with run_test_server() as server:
                response = request_json(
                    server,
                    "POST",
                    "/collector/temu/fetch",
                    {
                        "target_id": "mt_http_payload",
                        "store_url": "https://www.temu.com/mall.html?mall_id=synthetic_http",
                        "evidence_root": tmpdir,
                        "raw_payload": {
                            "items": [
                                {
                                    "goodsId": "920000000000001",
                                    "goodsName": "HTTP Collector Payload Jig",
                                    "priceInfo": {"price": 1080},
                                    "soldQuantity": "321",
                                    "linkUrl": "https://www.temu.com/http-collector-payload-jig-g-920000000000001.html",
                                }
                            ]
                        },
                    },
                )
            raw_file = Path(tmpdir) / "mt_http_payload" / "raw_products.json"
            loaded = json.loads(raw_file.read_text(encoding="utf-8"))

        self.assertEqual(response["status"], "OK")
        self.assertEqual(response["product_count"], 1)
        self.assertEqual(loaded[0]["goods_id"], "920000000000001")

    def test_fetch_requires_payload_or_har_for_url_only_request(self):
        with run_test_server() as server:
            response = request_json(
                server,
                "POST",
                "/collector/temu/fetch",
                {
                    "target_id": "mt_http_url_only",
                    "store_url": "https://www.temu.com/mall.html?mall_id=synthetic_http",
                },
            )

        self.assertEqual(response["status"], "SOURCE_UNAVAILABLE")
        self.assertEqual(response["error"]["code"], "SOURCE_UNAVAILABLE")

    def test_fetch_captures_products_from_authorized_browser_session(self):
        product_payload = {
            "api": "synthetic.temu.mall.goods",
            "result": {
                "goodsList": [
                    {
                        "goodsId": "930000000000001",
                        "goodsName": "Authorized Browser Capture Jig",
                        "priceInfo": {"price": 1580},
                        "soldQuantity": "456",
                        "linkUrl": "https://www.temu.com/browser-capture-jig-g-930000000000001.html",
                    }
                ]
            },
        }
        fake_page = FakePage([FakeResponse(product_payload)])
        fake_context = FakeContext(fake_page)

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch(
                "app.platforms.temu_collector_service.open_temu_context",
                fake_open_temu_context(fake_context),
                create=True,
            ):
                with run_test_server() as server:
                    response = request_json(
                        server,
                        "POST",
                        "/collector/temu/fetch",
                        {
                            "target_id": "mt_http_browser",
                            "tenant_id": 1,
                            "capture_mode": "browser",
                            "store_url": "https://www.temu.com/mall.html?mall_id=synthetic_browser",
                            "evidence_root": tmpdir,
                        },
                    )
            raw_file = Path(tmpdir) / "mt_http_browser" / "raw_products.json"
            raw_payload_file = Path(tmpdir) / "mt_http_browser" / "raw_payload.json"
            self.assertTrue(raw_payload_file.exists())
            loaded = json.loads(raw_file.read_text(encoding="utf-8"))

        self.assertEqual(response["status"], "OK")
        self.assertEqual(response["product_count"], 1)
        self.assertEqual(response["source_type"], "AUTHORIZED_BROWSER_SESSION")
        self.assertEqual(loaded[0]["goods_id"], "930000000000001")


class run_test_server:
    def __enter__(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.server = create_server(("127.0.0.1", 0), default_evidence_root=Path(self.tmpdir.name))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self.server

    def __exit__(self, exc_type, exc, tb):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.tmpdir.cleanup()


def request_json(server, method: str, path: str, body=None):
    conn = http.client.HTTPConnection(server.server_address[0], server.server_address[1], timeout=5)
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    conn.request(method, path, body=payload, headers=headers)
    response = conn.getresponse()
    data = response.read().decode("utf-8")
    conn.close()
    return json.loads(data)


class FakeResponse:
    def __init__(self, payload):
        self.url = "https://www.temu.com/api/synthetic/mall/goods"
        self.headers = {"content-type": "application/json; charset=utf-8"}
        self._payload = payload

    def json(self):
        return self._payload

    def text(self):
        return json.dumps(self._payload)


class FakePage:
    def __init__(self, responses):
        self.url = "about:blank"
        self.responses = responses
        self.handlers = {}

    def on(self, event_name, callback):
        self.handlers[event_name] = callback

    def goto(self, url, wait_until=None, timeout=None):
        self.url = url
        for response in self.responses:
            self.handlers["response"](response)

    def wait_for_load_state(self, state=None, timeout=None):
        return None

    def wait_for_timeout(self, timeout):
        return None


class FakeContext:
    def __init__(self, page):
        self.page = page

    def new_page(self):
        return self.page


def fake_open_temu_context(context):
    @contextmanager
    def _open_temu_context(tenant_id, *, headless=None):
        yield object(), context

    return _open_temu_context


if __name__ == "__main__":
    unittest.main()
