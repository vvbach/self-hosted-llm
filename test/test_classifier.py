import unittest

from app.classifier import ClassifierService


class JsonParsingTests(unittest.TestCase):
    def test_plain_json(self):
        parsed = ClassifierService._extract_json(
            '{"category":"type_error","severity":"medium",'
            '"summary":"Wrong type","suggested_action":"Validate the input"}'
        )
        self.assertEqual(parsed["category"], "type_error")

    def test_markdown_fence(self):
        parsed = ClassifierService._extract_json(
            '```json\n{"category":"unknown","severity":"low",'
            '"summary":"Unknown","suggested_action":"Inspect logs"}\n```'
        )
        self.assertEqual(parsed["category"], "unknown")

    def test_text_wrapped_json(self):
        parsed = ClassifierService._extract_json(
            'Result: {"category":"network_error","severity":"high",'
            '"summary":"Connection refused","suggested_action":"Check the server"}'
        )
        self.assertEqual(parsed["severity"], "high")

    def test_invalid_json(self):
        with self.assertRaises(ValueError):
            ClassifierService._extract_json("not json")
