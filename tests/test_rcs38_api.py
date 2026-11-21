"""Tests d'intégration de l'API RCS-38 : aucune donnée réelle."""
import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from tools.rcs38_demo_server import build_server, DemoStore, load_fixture

ROOT = Path(__file__).resolve().parents[1]


class TestRCS38LocalAPI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "state.sqlite3"
        self.server = build_server(port=0, db_path=self.db)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = "http://127.0.0.1:" + str(self.server.server_address[1])
        self.addCleanup(self.thread.join, 3)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, path, payload=None, *, origin=None, content_type="application/json", host=None):
        data = json.dumps(payload).encode() if payload is not None else None
        headers = {"Content-Type": content_type} if data is not None else {}
        if origin:
            headers["Origin"] = origin
        if host:
            headers["Host"] = host
        req = Request(self.base + path, data=data, headers=headers)
        try:
            with urlopen(req, timeout=4) as response:
                raw = response.read()
                mime = response.headers.get("Content-Type", "")
                return response.status, json.loads(raw) if "application/json" in mime else raw.decode()
        except HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def test_api_returns_entirely_fictional_overview(self):
        status, data = self.request("/api/v1/demo/overview")
        self.assertEqual(status, 200)
        self.assertEqual(data["data_mode"], "fictional_demo_only")
        self.assertEqual(data["server_mode"], "local_demo")
        self.assertEqual(len(data["actions"]), 2)
        self.assertEqual(data["events"], [])
        for run in data["runs"]:
            self.assertIsNone(run["energy_kwh"])
            self.assertIsNone(run["co2e_kg"])

    def test_health_and_static_site(self):
        self.assertEqual(self.request("/api/v1/demo/health")[0], 200)
        status, content = self.request("/index.html")
        self.assertEqual(status, 200)
        self.assertIn("RoboCare Sentinel", content)
        self.assertEqual(self.request("/api/v1/other")[0], 404)

    def test_approval_requires_simulation_confirmation(self):
        action = "ACT-DEMO-01"
        invalid = {"decision": "approved", "reason_code": "controle_confirme",
                   "acknowledge_simulation": False}
        self.assertEqual(self.request(f"/api/v1/demo/actions/{action}/decision", invalid)[0], 400)
        invalid["acknowledge_simulation"] = True
        status, result = self.request(f"/api/v1/demo/actions/{action}/decision", invalid)
        self.assertEqual(status, 200)
        self.assertEqual(result["state"], "Approuvée")
        self.assertEqual(result["actor_role"], "technicien-demo")
        self.assertTrue(result["trace_id"])
        status, overview = self.request("/api/v1/demo/overview")
        self.assertEqual(len(overview["events"]), 1)
        self.assertEqual(overview["events"][0]["before_state"], "En attente")
        self.assertEqual(overview["events"][0]["after_state"], "Approuvée")
        self.assertEqual(self.request(f"/api/v1/demo/actions/{action}/decision", invalid)[0], 409)

    def test_rejection_with_bounded_reason_enum(self):
        a = "ACT-DEMO-02"
        payload = {"decision": "rejected", "reason_code": "signal_non_confirme",
                   "acknowledge_simulation": True}
        status, result = self.request(f"/api/v1/demo/actions/{a}/decision", payload)
        self.assertEqual(status, 200)
        self.assertEqual(result["state"], "Rejetée")
        self.assertEqual(self.request(f"/api/v1/demo/actions/{a}/decision", payload)[0], 409)

    def test_invalid_decisions_and_extra_fields_rejected(self):
        path = "/api/v1/demo/actions/ACT-DEMO-01/decision"
        p = {"decision": "approved", "reason_code": "signal_non_confirme",
             "acknowledge_simulation": True}
        self.assertEqual(self.request(path, p)[0], 400)
        p["patient_name"] = "DONNEE INTERDITE"
        self.assertEqual(self.request(path, p)[0], 400)

    def test_nonexistent_action_is_404(self):
        p = {"decision": "approved", "reason_code": "controle_confirme",
             "acknowledge_simulation": True}
        self.assertEqual(self.request("/api/v1/demo/actions/ACT-DEMO-99/decision", p)[0], 404)

    def test_origin_and_content_type_checked(self):
        p = {"decision": "approved", "reason_code": "controle_confirme",
             "acknowledge_simulation": True}
        path = "/api/v1/demo/actions/ACT-DEMO-01/decision"
        self.assertEqual(self.request(path, p, origin="https://external.example")[0], 403)
        self.assertEqual(self.request(path, p, content_type="text/plain")[0], 415)

    def test_state_persists_in_sqlite_restart(self):
        path = "/api/v1/demo/actions/ACT-DEMO-01/decision"
        p = {"decision": "approved", "reason_code": "controle_confirme",
             "acknowledge_simulation": True}
        self.assertEqual(self.request(path, p)[0], 200)
        next_store = DemoStore(self.db, load_fixture())
        self.assertEqual(next_store.actions()[0]["state"], "Approuvée")
        self.assertEqual(len(next_store.events()), 1)

    def test_no_public_network_bind(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")

    def test_foreign_host_rejected_for_read_write_and_head(self):
        # A loopback bind alone does not prevent a foreign DNS name resolving to it.
        for path in ("/index.html", "/api/v1/demo/overview"):
            self.assertEqual(self.request(path, host="external.example")[0], 403)
        payload = {"decision": "approved", "reason_code": "controle_confirme",
                   "acknowledge_simulation": True}
        self.assertEqual(self.request("/api/v1/demo/actions/ACT-DEMO-01/decision",
                                      payload, host="external.example")[0], 403)
        request = Request(self.base + "/index.html", method="HEAD",
                          headers={"Host": "external.example"})
        with self.assertRaises(HTTPError) as error:
            urlopen(request, timeout=4)
        self.assertEqual(error.exception.code, 403)
        port = self.server.server_address[1]
        self.assertEqual(self.request("/api/v1/demo/overview", host=f"localhost:{port}")[0], 200)
        self.assertEqual(self.request("/api/v1/demo/overview")[1]["events"], [])

    def test_fixture_contract_enforced_by_server_loader(self):
        fixture = json.loads((ROOT / "frontend/monitoring/demo.json").read_text(encoding="utf-8"))
        path = Path(self.temp.name) / "invalid.json"
        for field, value in (("site", "unapproved-site"), ("patient_id", "FORBIDDEN_TEST_MARKER")):
            changed = json.loads(json.dumps(fixture))
            changed["devices"][0][field] = value
            path.write_text(json.dumps(changed), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_fixture(path)

    def test_simultaneous_decisions_commit_one_event(self):
        from concurrent.futures import ThreadPoolExecutor
        payload = {"decision": "approved", "reason_code": "controle_confirme",
                   "acknowledge_simulation": True}
        path = "/api/v1/demo/actions/ACT-DEMO-01/decision"
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _: self.request(path, payload)[0], range(2)))
        self.assertEqual(sorted(responses), [200, 409])
        self.assertEqual(len(self.request("/api/v1/demo/overview")[1]["events"]), 1)


if __name__ == "__main__":
    unittest.main()
