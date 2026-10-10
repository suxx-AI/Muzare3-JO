import json
from unittest.mock import patch, Mock
from django.test import Client, TestCase
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from . import agent_service
import Agent


FARM = {"location": "الغور", "land": 20, "water": 10000, "budget": 10000}
SETUP = {"goal": "balanced", "crops": ["بندورة", "خيار"]}


class IntegrationTests(TestCase):
    def start(self, client=None):
        client = client or self.client
        result = client.post("/ar/start", {"farm": FARM, "setup": SETUP}, content_type="application/json")
        self.assertEqual(result.status_code, 200)
        return client

    def test_page_routes_assets_health_and_session(self):
        self.assertRedirects(self.client.get("/ar/"), "/ar/index")
        for route in ["/ar/index", "/ar/crops", "/ar/ready"]:
            self.assertContains(self.client.get(route), "مزارع جو")
        self.start()
        response = self.client.get("/ar/")
        self.assertContains(response, "لوحة القرار المباشر")
        self.assertNotContains(response, '"ميزان"')
        self.assertNotContains(response, "Mizaan")
        self.assertEqual(self.client.get("/health/").json()["status"], "ok")
        self.assertEqual(self.client.get("/static/js/main.js")["Content-Type"], "application/javascript")

    def test_real_graph_real_optimizer_clean_text_and_memory_isolation(self):
        first = self.start()
        second = self.start(Client())
        model = Mock()
        model.invoke.side_effect = [
            AIMessage(content="", tool_calls=[{"name": "optimize_farm_plan", "args": {"total_dunums": 20, "budget_jod": 10000, "crops_to_consider": ["بندورة", "خيار"]}, "id": "optimizer-integration-test"}]),
            AIMessage(content=[{"type": "text", "text": "**خطة فعلية**", "extras": {"signature": "not-for-ui"}}]),
        ]
        with patch.object(Agent, "model_with_tools", model):
            response = first.post("/ar/api/farm/chat/", {"message": "remember-first-824"}, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["answer"], "**خطة فعلية**")
        self.assertTrue(result["dashboard"]["success"])
        self.assertIn("balanced_plan", result["dashboard"])
        self.assertNotIn("signature", json.dumps(result))
        human = next(m for m in model.invoke.call_args_list[0].args[0] if isinstance(m, HumanMessage))
        self.assertIn("المساحة بالدونم", human.content)
        self.assertIn("10000", human.content)
        def remembers(messages):
            return AIMessage(content="remembered" if any(isinstance(m, HumanMessage) and "remember-first-824" in m.content for m in messages) else "isolated")
        model.invoke.side_effect = remembers
        with patch.object(Agent, "model_with_tools", model):
            followup = first.post("/ar/api/farm/chat/", {"message": "followup"}, content_type="application/json")
            separate = second.post("/ar/api/farm/chat/", {"message": "new visitor"}, content_type="application/json")
        self.assertEqual(followup.json()["answer"], "remembered")
        self.assertEqual(separate.json()["answer"], "isolated")
        self.assertNotEqual(first.session["mazarejo_thread_id"], second.session["mazarejo_thread_id"])

    def test_missing_invalid_optimizer_and_weather_messages(self):
        self.assertIsNone(agent_service.latest_optimizer([]))
        self.assertIsNone(agent_service.latest_optimizer([ToolMessage(content="not json", name="optimize_farm_plan", tool_call_id="1")]))
        self.assertEqual(agent_service.weather_results([ToolMessage(content='{"error":"offline","details":"private"}', name="get_live_weather", tool_call_id="2")]), [])
        self.assertEqual(agent_service.extract_text([AIMessage(content=[{"type": "text", "text": "answer", "extras": {"signature": "private"}}, {"type": "thinking", "text": "private"}])]), "answer")

    def test_optional_water_context_and_real_calculated_requirement(self):
        for water in ["omitted", None, 0, 1234.5]:
            with self.subTest(water=water):
                client = Client()
                farm = {key: value for key, value in FARM.items() if key != "water"}
                if water != "omitted":
                    farm["water"] = water
                response = client.post("/ar/start", {"farm": farm, "setup": SETUP}, content_type="application/json")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(client.session["mazarejo_farm"]["water"], None if water == "omitted" else water)
                model = Mock()
                model.invoke.side_effect = [
                    AIMessage(content="", tool_calls=[{"name": "optimize_farm_plan", "args": {"total_dunums": 20, "budget_jod": 10000, "crops_to_consider": SETUP["crops"]}, "id": "optional-water-test"}]),
                    AIMessage(content="احتياج المياه محسوب من الخطة"),
                ]
                with patch.object(Agent, "model_with_tools", model):
                    result = client.post("/ar/api/farm/chat/", {"message": "اعرض احتياج الخطة للمياه"}, content_type="application/json")
                self.assertEqual(result.status_code, 200)
                self.assertGreater(result.json()["dashboard"]["balanced_plan"]["total_water_m3"], 0)
                human = next(message for message in model.invoke.call_args_list[0].args[0] if isinstance(message, HumanMessage))
                context = json.loads(human.content.split("\n", 1)[1].split("\n\nرسالة المستخدم:", 1)[0])
                if water == "omitted" or water is None:
                    self.assertNotIn("المياه المتاحة بالمتر المكعب", context)
                else:
                    self.assertEqual(context["المياه المتاحة بالمتر المكعب"], water)
        for invalid in [-1, "", "123", True]:
            with self.subTest(invalid=invalid):
                response = self.client.post("/ar/start", {"farm": {**FARM, "water": invalid}, "setup": SETUP}, content_type="application/json")
                self.assertEqual(response.status_code, 400)

    def test_validation_error_no_fake_success_and_safe_csrf(self):
        self.assertEqual(self.client.post("/ar/start", {"farm": {**FARM, "land": 21}, "setup": SETUP}, content_type="application/json").status_code, 400)
        self.start()
        for body in ["[1]", "invalid", '{"message":null}', '{"message":"  "}']:
            self.assertEqual(self.client.post("/ar/api/farm/chat/", body, content_type="application/json").status_code, 400)
        with patch.object(agent_service, "invoke_agent", side_effect=RuntimeError("private-key traceback")):
            with self.assertLogs("dashboard.views", level="ERROR"):
                response = self.client.post("/ar/api/farm/chat/", {"message": "question"}, content_type="application/json")
        self.assertEqual(response.status_code, 502)
        self.assertEqual(list(response.json()), ["error"])
        self.assertNotContains(response, "private-key", status_code=502)
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post("/ar/api/farm/chat/", {"message": "question"}, content_type="application/json")
        self.assertEqual(response.status_code, 403)
        self.assertIn("error", response.json())

    def test_chat_reset_keeps_farm_but_process_restart_clears_everything(self):
        self.start()
        old = self.client.session["mazarejo_thread_id"]
        self.client.post("/ar/api/farm/reset/", {}, content_type="application/json")
        self.assertNotEqual(old, self.client.session["mazarejo_thread_id"])
        self.assertEqual(self.client.session["mazarejo_farm"], FARM)
        session = self.client.session
        session["mazarejo_messages"] = [{"role": "user", "text": "stale"}]
        session["mazarejo_dashboard"] = {"success": True}
        session["mazarejo_weather"] = [{"location": "الغور"}]
        session.save()
        with patch("dashboard.views.BOOT_ID", "next-process"):
            self.assertRedirects(self.client.get("/ar/"), "/ar/index")
        self.assertEqual(self.client.session["mazarejo_messages"], [])
        self.assertIsNone(self.client.session["mazarejo_dashboard"])
        self.assertEqual(self.client.session["mazarejo_weather"], [])
        self.assertNotIn("mazarejo_farm", self.client.session)
        self.assertNotIn("mazarejo_setup", self.client.session)

    def test_restart_onboarding_ignores_old_setup_and_stale_chat_cannot_invoke(self):
        self.start()
        with patch("dashboard.views.BOOT_ID", "new-onboarding-process"):
            response = self.client.get("/ar/index")
            self.assertEqual(response.context["saved_setup"], {"farm": {}, "setup": {}, "boot_id": "new-onboarding-process"})
        self.start()
        with patch("dashboard.views.BOOT_ID", "new-chat-process"), patch.object(agent_service, "invoke_agent") as invoke:
            response = self.client.post("/ar/api/farm/chat/", {"message": "old tab question"}, content_type="application/json")
            self.assertEqual(response.status_code, 400)
            invoke.assert_not_called()
