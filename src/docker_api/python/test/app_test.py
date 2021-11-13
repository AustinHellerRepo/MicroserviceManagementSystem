import unittest
from flask import request
import app as flask_app
import json


class AppTest2(unittest.TestCase):

	def test_initialize(self):

		client = flask_app.app.test_client()

		self.assertIsNotNone(client)

	def test_health(self):

		client = flask_app.app.test_client()

		response = client.get("/v1/test/health")

		self.assertEqual(b"{\"is_healthy\":true}\n", response.data)

	def test_json_using_data(self):

		client = flask_app.app.test_client()

		input_json_bytes = b'{"hello":"world"}\n'
		input_json_string = input_json_bytes.decode()

		response = client.post("/v1/test/json/form",
			data={
				"json": input_json_string
			}
		)

		self.assertEqual(input_json_bytes, response.data)

	def test_json_using_json(self):

		client = flask_app.app.test_client()

		input_json = {"hello": "world"}

		response = client.post("/v1/test/json/json",
			json=input_json
		)

		print(f"response: {response}")

		response_json = response.json
		print(f"response_json: {response_json}")

		self.assertEqual(input_json, response_json)

	def test_json_using_json_deep(self):

		client = flask_app.app.test_client()

		input_json = {"hello": "world", "deeper": {"here": True}}

		response = client.post("/v1/test/json/json",
			json=input_json
		)

		print(f"response: {response}")

		response_json = response.json
		print(f"response_json: {response_json}")

		self.assertEqual(input_json, response_json)

	def test_docker_missing_component_uuid_failed(self):

		client = flask_app.app.test_client()

		response = client.post("/v1/api/docker",
			json={
				"json_data_array": [],
				"component_manager_api_base_url": "0.0.0.0"
			}
		)

		print(f"response: {response.json}")

		expected_response_json = {
			"data": None,
			"exception": "Failed to find \"component_uuid\" in json \"{'component_manager_api_base_url': '0.0.0.0', 'json_data_array': []}\"."
		}

		self.assertEqual(expected_response_json, response.json)

	def test_docker_missing_json_data_array_failed(self):

		client = flask_app.app.test_client()

		response = client.post("/v1/api/docker",
			json={
				"component_uuid": "98e77fd4-7d54-40be-9cc9-b0883bfe123e",
				#"json_data_array": [],
				"component_manager_api_base_url": "0.0.0.0"
			}
		)

		print(f"response: {response.json}")

		expected_response_json = {
			"data": None,
			"exception": 'Failed to find "json_data_array" in json "{\'component_manager_api_base_url\': \'0.0.0.0\', \'component_uuid\': \'98e77fd4-7d54-40be-9cc9-b0883bfe123e\'}".'
		}

		self.assertEqual(expected_response_json, response.json)

	def test_docker_missing_component_manager_api_base_url_failed(self):

		client = flask_app.app.test_client()

		response = client.post("/v1/api/docker",
			json={
				"component_uuid": "9cab32fc-3188-4e74-a59c-6efc6981af6e",
				"json_data_array": [],
				#"component_manager_api_base_url": "0.0.0.0"
			}
		)

		print(f"response: {response.json}")

		expected_response_json = {
			"data": None,
			"exception": 'Failed to find "component_manager_api_base_url" in json "{\'component_uuid\': \'9cab32fc-3188-4e74-a59c-6efc6981af6e\', \'json_data_array\': []}".'
		}

		self.assertEqual(expected_response_json, response.json)

	def test_docker_json_data_array_is_not_a_list_failed(self):

		client = flask_app.app.test_client()

		response = client.post("/v1/api/docker",
			json={
				"component_uuid": "a38c223d-aa1c-4ae4-bad8-dd40c7f7f2b5",
				"json_data_array": {"is_dict": True},
				"component_manager_api_base_url": "0.0.0.0"
			}
		)

		print(f"response: {response.json}")

		expected_response_json = {
			"data": None,
			"exception": 'json_data_array was not an array: "{\'is_dict\': True}".'
		}

		self.assertEqual(expected_response_json, response.json)

	def test_component_manager_healthy(self):

		client = flask_app.app.test_client()

		response = client.get("/v1/test/component_manager_api")

		print(f"response: {response}")

		self.assertEqual(b"{\"is_healthy\":true}\n", response.data)
