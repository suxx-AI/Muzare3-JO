"""Contract checks without network calls or Gemini usage."""

import json
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

import Agent
import api
from tools import optimize_farm_plan


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(api.app)

    def test_health_and_cors(self):
        self.assertEqual(self.client.get('/health').json(), {'status': 'ok'})
        response = self.client.options('/chat', headers={
            'Origin': 'http://localhost:5173',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['access-control-allow-origin'], 'http://localhost:5173')

    def test_contract_and_latest_optimizer(self):
        optimizer = optimize_farm_plan.invoke({
            'total_dunums': 20, 'budget_jod': 10000,
            'crops_to_consider': ['بندورة', 'خيار'],
        })
        output = {'messages': [
            ToolMessage(name='optimize_farm_plan', content='{"old": true}', tool_call_id='old'),
            ToolMessage(name='optimize_farm_plan', content=json.dumps(optimizer), tool_call_id='new'),
            ToolMessage(name='get_live_weather', content='{}', tool_call_id='weather'),
            AIMessage(content=[
                {'type': 'text', 'text': 'الخطة جاهزة', 'extras': {'signature': 'private'}},
                {'type': 'thinking', 'thinking': 'private reasoning'},
            ]),
        ]}
        with patch.object(api.agent_app, 'invoke', return_value=output) as invoke:
            response = self.client.post('/chat', json={'message': 'خطط لمزرعتي', 'session_id': 'demo-user'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'answer': 'الخطة جاهزة', 'dashboard': optimizer})
        args, kwargs = invoke.call_args
        self.assertIsInstance(args[0]['messages'][0], HumanMessage)
        self.assertEqual(args[0]['messages'][0].content, 'خطط لمزرعتي')
        self.assertEqual(kwargs['config'], {'configurable': {'thread_id': 'demo-user'}})
        self.assertNotIn('signature', response.text)

    def test_missing_and_malformed_data(self):
        outputs = [
            {},
            {'messages': [AIMessage(content='مرحبا')]},
            {'messages': [
                ToolMessage(name='optimize_farm_plan', content='{"old": true}', tool_call_id='old'),
                ToolMessage(name='optimize_farm_plan', content='bad JSON', tool_call_id='new'),
                AIMessage(content=[]),
            ]},
            {'messages': [ToolMessage(name='optimize_farm_plan', content='[]', tool_call_id='list')]},
        ]
        for output in outputs:
            with self.subTest(output=output), patch.object(api.agent_app, 'invoke', return_value=output):
                response = self.client.post('/chat', json={'message': 'مرحبا', 'session_id': 'test'})
                self.assertEqual(response.status_code, 200)
                self.assertIsNone(response.json()['dashboard'])
                self.assertIsInstance(response.json()['answer'], str)

    def test_validation_and_upstream_failure(self):
        for body in [{}, {'message': '', 'session_id': 'test'}, {'message': 'x', 'session_id': '  '}]:
            self.assertEqual(self.client.post('/chat', json=body).status_code, 422)
        with patch.object(api.agent_app, 'invoke', side_effect=RuntimeError('upstream secret')), patch.object(api.logger, 'exception'):
            response = self.client.post('/chat', json={'message': 'مرحبا', 'session_id': 'test'})
        self.assertEqual(response.status_code, 502)
        self.assertNotIn('upstream secret', response.text)

    def test_real_graph_memory_isolated_by_api_session(self):
        # Replace only Gemini during this test. Run the actual compiled graph.
        def model_reply(prompt):
            users = [message.content for message in prompt if isinstance(message, HumanMessage)]
            return AIMessage(content=' | '.join(users))

        first, second = str(uuid4()), str(uuid4())
        with patch.object(Agent, 'model_with_tools') as model:
            model.invoke.side_effect = model_reply
            self.assertEqual(self.client.post('/chat', json={'message': 'الأول', 'session_id': first}).json()['answer'], 'الأول')
            self.assertEqual(self.client.post('/chat', json={'message': 'الثاني', 'session_id': first}).json()['answer'], 'الأول | الثاني')
            self.assertEqual(self.client.post('/chat', json={'message': 'مستقل', 'session_id': second}).json()['answer'], 'مستقل')

    def test_real_toolnode_serialization(self):
        call = {'name': 'optimize_farm_plan', 'args': {
            'total_dunums': 20, 'budget_jod': 10000, 'crops_to_consider': ['بندورة', 'خيار'],
        }, 'id': 'optimizer-test', 'type': 'tool_call'}
        with patch.object(Agent, 'model_with_tools') as model:
            model.invoke.side_effect = [AIMessage(content='', tool_calls=[call]), AIMessage(content='الخطة جاهزة')]
            result = Agent.app.invoke(
                {'messages': [HumanMessage(content='خطة تجريبية')]},
                config={'configurable': {'thread_id': str(uuid4())}},
            )
        message = next(item for item in result['messages'] if isinstance(item, ToolMessage))
        self.assertIsInstance(message, ToolMessage)
        self.assertEqual(message.name, 'optimize_farm_plan')
        self.assertTrue(api.extract_dashboard(result['messages'])['success'])


if __name__ == '__main__':
    unittest.main()
