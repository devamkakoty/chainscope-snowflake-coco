import hashlib
import json
import unittest
from html.parser import HTMLParser

from chainscope.model import ROOT
from chainscope.metrics import CATALOG


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "script":
            self.assets.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.assets.append(attrs["href"])


class StaticPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ROOT / "docs"
        cls.html = (cls.root / "index.html").read_text(encoding="utf-8")
        cls.fixture_path = cls.root / "static" / "demo-data.js"
        text = cls.fixture_path.read_text(encoding="utf-8")
        cls.fixture = json.loads(text.removeprefix("window.CHAINSCOPE_DATA=").strip().removesuffix(";"))

    def test_static_html_has_relative_existing_assets(self):
        parser = AssetParser()
        parser.feed(self.html)
        self.assertGreaterEqual(len(parser.assets), 4)
        for asset in parser.assets:
            self.assertTrue(asset.startswith("./static/"))
            self.assertTrue((self.root / asset).is_file())
        self.assertTrue((self.root / ".nojekyll").exists())

    def test_replay_is_explicitly_public_and_non_authorizing(self):
        self.assertIn("Public synthetic fixture", self.html)
        self.assertIn("not access control", self.html)

    def test_all_seven_answers_and_source_records_available(self):
        self.assertEqual(set(self.fixture["answers"]), {m["id"] for m in CATALOG})
        for role in ["operations", "commercial"]:
            self.assertEqual(len(self.fixture["records"][role]), 163)
        for result in self.fixture["answers"].values():
            for source in result["citations"]:
                self.assertIn(source["href"], self.fixture["records"]["commercial"])

    def test_manifest_matches_generated_fixture(self):
        manifest = json.loads((self.root / "static-manifest.json").read_text())
        fixture_bytes = self.fixture_path.read_bytes()
        self.assertNotIn(b"\r\n", fixture_bytes)
        self.assertEqual(manifest["fixture_bytes"], len(fixture_bytes))
        self.assertEqual(manifest["fixture_sha256"], hashlib.sha256(fixture_bytes).hexdigest())

    def test_operation_record_projection_has_no_prices(self):
        record = self.fixture["records"]["operations"]["/api/records/order_lines/LIN-025"]
        self.assertNotIn("unit_price_cents", record["record"])
        self.assertIn("unit_price_cents", self.fixture["records"]["commercial"]["/api/records/order_lines/LIN-025"]["record"])

    def test_static_styles_and_runtime_match_source(self):
        self.assertEqual((self.root / "static" / "style.css").read_bytes(), (ROOT / "static" / "style.css").read_bytes())
        source = (ROOT / "static" / "app.js").read_text(encoding="utf-8").replace("/static/", "./static/")
        self.assertEqual(source, (self.root / "static" / "app.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
