import json
import os
import tempfile
import unittest
from unittest import mock

import council_free


class TestLoadApiKey(unittest.TestCase):
    def test_reads_from_environment_variable(self):
        with mock.patch.dict(os.environ, {"FAKE_KEY_ENV": "sk-from-env"}):
            self.assertEqual(council_free.load_api_key("FAKE_KEY_ENV"), "sk-from-env")

    def test_falls_back_to_home_dotenv(self):
        with tempfile.TemporaryDirectory() as home:
            dotenv_path = os.path.join(home, ".env")
            with open(dotenv_path, "w", encoding="utf-8") as f:
                f.write('FAKE_KEY_ENV="sk-from-dotenv"\n')
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("FAKE_KEY_ENV", None)
                with mock.patch("os.path.expanduser", return_value=dotenv_path):
                    self.assertEqual(
                        council_free.load_api_key("FAKE_KEY_ENV"), "sk-from-dotenv"
                    )

    def test_returns_none_when_missing_everywhere(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TOTALLY_ABSENT_KEY", None)
            with mock.patch("os.path.expanduser", return_value="/nonexistent/.env"):
                self.assertIsNone(council_free.load_api_key("TOTALLY_ABSENT_KEY"))


class TestCallModel(unittest.TestCase):
    def test_success_returns_content_and_no_error(self):
        def fake_post(url, headers, body):
            return {"choices": [{"message": {"content": "resposta ok"}}]}

        content, err = council_free.call_model(
            "https://example.test/chat", "sk-x", "model-x", "pergunta",
            http_post=fake_post,
        )
        self.assertEqual(content, "resposta ok")
        self.assertIsNone(err)

    def test_http_error_returns_error_and_no_content(self):
        def fake_post(url, headers, body):
            raise council_free.urllib.error.HTTPError(
                url, 429, "Too Many Requests", hdrs=None,
                fp=__import__("io").BytesIO(b"rate limited"),
            )

        content, err = council_free.call_model(
            "https://example.test/chat", "sk-x", "model-x", "pergunta",
            http_post=fake_post,
        )
        self.assertIsNone(content)
        self.assertIn("HTTP 429", err)

    def test_generic_exception_returns_error_and_no_content(self):
        def fake_post(url, headers, body):
            raise TimeoutError("boom")

        content, err = council_free.call_model(
            "https://example.test/chat", "sk-x", "model-x", "pergunta",
            http_post=fake_post,
        )
        self.assertIsNone(content)
        self.assertIn("TimeoutError", err)


class TestAvailableProviders(unittest.TestCase):
    def test_filters_to_providers_with_a_key(self):
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "sk-openrouter"}, clear=False):
            for env_var in ("GEMINI_API_KEY", "GROQ_API_KEY", "QWEN_API_KEY"):
                os.environ.pop(env_var, None)
            with mock.patch("os.path.expanduser", return_value="/nonexistent/.env"):
                result = council_free.available_providers()
        self.assertEqual([p["name"] for p in result], ["openrouter"])
        self.assertEqual(result[0]["api_key"], "sk-openrouter")


class TestRunRound1(unittest.TestCase):
    def _providers(self):
        return [
            {"name": "gemini", "base_url": "https://g.test", "model": "m-g", "api_key": "k-g"},
            {"name": "groq", "base_url": "https://q.test", "model": "m-q", "api_key": "k-q"},
        ]

    def test_collects_successful_answers_with_provider_labels(self):
        def fake_post(url, headers, body):
            payload = json.loads(body)
            answer = f"resposta de {payload['model']}"
            return {"choices": [{"message": {"content": answer}}]}

        members, failures = council_free.run_round1(
            "qual a capital da França?", self._providers(), http_post=fake_post
        )
        self.assertEqual(failures, [])
        self.assertEqual(
            sorted(m["provider"] for m in members), ["gemini", "groq"]
        )
        gemini_answer = next(m for m in members if m["provider"] == "gemini")
        self.assertEqual(gemini_answer["answer"], "resposta de m-g")

    def test_one_provider_failing_does_not_block_the_other(self):
        def fake_post(url, headers, body):
            if "g.test" in url:
                raise TimeoutError("gemini indisponível")
            return {"choices": [{"message": {"content": "ok groq"}}]}

        members, failures = council_free.run_round1(
            "pergunta", self._providers(), http_post=fake_post
        )
        self.assertEqual([m["provider"] for m in members], ["groq"])
        self.assertEqual(failures, [{"provider": "gemini", "error": "TimeoutError: gemini indisponível"}])


class TestBuildRound2Prompt(unittest.TestCase):
    def test_excludes_own_answer_and_labels_others(self):
        round1 = [
            {"provider": "gemini", "answer": "resposta do gemini"},
            {"provider": "groq", "answer": "resposta do groq"},
            {"provider": "qwen", "answer": "resposta do qwen"},
        ]
        prompt = council_free.build_round2_prompt("pergunta X", "groq", round1)
        self.assertNotIn("resposta do groq", prompt)
        self.assertIn("resposta do gemini", prompt)
        self.assertIn("resposta do qwen", prompt)
        self.assertIn("Resposta A", prompt)
        self.assertIn("Resposta B", prompt)
        self.assertNotIn("gemini", prompt.split("Pergunta original")[0])  # sem nomes reais no corpo


class TestRunRound2(unittest.TestCase):
    def test_each_provider_reacts_without_seeing_its_own_answer(self):
        round1_members = [
            {"provider": "gemini", "answer": "resposta do gemini"},
            {"provider": "groq", "answer": "resposta do groq"},
        ]
        providers = [
            {"name": "gemini", "base_url": "https://g.test", "model": "m-g", "api_key": "k-g"},
            {"name": "groq", "base_url": "https://q.test", "model": "m-q", "api_key": "k-q"},
        ]

        def fake_post(url, headers, body):
            payload = json.loads(body)
            sent_prompt = payload["messages"][0]["content"]
            if "g.test" in url:
                assert "resposta do gemini" not in sent_prompt
            if "q.test" in url:
                assert "resposta do groq" not in sent_prompt
            return {"choices": [{"message": {"content": f"reacao via {url}"}}]}

        members, failures = council_free.run_round2(
            "pergunta", providers, round1_members, http_post=fake_post
        )
        self.assertEqual(failures, [])
        self.assertEqual(
            sorted(m["provider"] for m in members), ["gemini", "groq"]
        )
        self.assertTrue(all("reaction" in m for m in members))


class TestDispatch(unittest.TestCase):
    def _fake_post_ok(self, url, headers, body):
        return {"choices": [{"message": {"content": "ok"}}]}

    def test_missing_args_returns_usage_error(self):
        result, code = council_free.dispatch([])
        self.assertEqual(code, 1)
        self.assertIn("Usage", result["error"])

    def test_no_providers_returns_error(self):
        result, code = council_free.dispatch(
            ["round1", "pergunta"], providers=[]
        )
        self.assertEqual(code, 1)
        self.assertIn("No provider API keys", result["error"])

    def test_round1_happy_path_returns_members(self):
        providers = [{"name": "groq", "base_url": "https://q.test", "model": "m", "api_key": "k"}]
        result, code = council_free.dispatch(
            ["round1", "pergunta"], providers=providers, http_post=self._fake_post_ok
        )
        self.assertEqual(code, 0)
        self.assertEqual(result["members"][0]["provider"], "groq")
        self.assertEqual(result["failures"], [])

    def test_round2_without_json_path_returns_usage_error(self):
        providers = [{"name": "groq", "base_url": "https://q.test", "model": "m", "api_key": "k"}]
        result, code = council_free.dispatch(
            ["round2", "pergunta"], providers=providers
        )
        self.assertEqual(code, 1)
        self.assertIn("round1_results.json", result["error"])

    def test_round2_reads_round1_file_and_returns_reactions(self):
        providers = [{"name": "groq", "base_url": "https://q.test", "model": "m", "api_key": "k"}]
        with tempfile.TemporaryDirectory() as tmp:
            round1_path = os.path.join(tmp, "round1.json")
            with open(round1_path, "w", encoding="utf-8") as f:
                json.dump({"members": [{"provider": "gemini", "answer": "resp"}]}, f)
            result, code = council_free.dispatch(
                ["round2", "pergunta", round1_path],
                providers=providers, http_post=self._fake_post_ok,
            )
        self.assertEqual(code, 0)
        self.assertEqual(result["members"][0]["provider"], "groq")
        self.assertIn("reaction", result["members"][0])

    def test_unknown_stage_returns_error(self):
        providers = [{"name": "groq", "base_url": "https://q.test", "model": "m", "api_key": "k"}]
        result, code = council_free.dispatch(
            ["round99", "pergunta"], providers=providers
        )
        self.assertEqual(code, 1)
        self.assertIn("Unknown stage", result["error"])

    def test_round2_with_nonexistent_file_returns_error(self):
        providers = [{"name": "groq", "base_url": "https://q.test", "model": "m", "api_key": "k"}]
        result, code = council_free.dispatch(
            ["round2", "pergunta", "/nonexistent/path/round1.json"],
            providers=providers,
        )
        self.assertEqual(code, 1)
        self.assertIn("not found", result["error"])


if __name__ == "__main__":
    unittest.main()
