import unittest

from fastapi.testclient import TestClient

from app.main import app, get_classifier
from app.schema import ClassificationResponse


class FakeClassifier:
    async def classify(self, error):
        return ClassificationResponse(
            category="runtime_error",
            severity="medium",
            summary="A runtime value is undefined",
            suggested_action="Initialize the value before using it",
        )


class ApiTests(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[get_classifier] = lambda: FakeClassifier()
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_classify(self):
        response = self.client.post(
            "/api/v1/classify",
            json={"error": "TypeError: products is undefined"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["category"], "runtime_error")
        self.assertEqual(body["severity"], "medium")

    def test_empty_error_is_rejected(self):
        response = self.client.post("/api/v1/classify", json={"error": ""})
        self.assertEqual(response.status_code, 422)
