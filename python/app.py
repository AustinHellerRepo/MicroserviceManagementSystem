from __future__ import annotations
from typing import List, Tuple, Dict
from flask import Flask, request, jsonify
from sys import version
import tempfile
import uuid
import json
from austin_heller_repo.threading import Semaphore
from austin_heller_repo.git_manager import GitManager
from austin_heller_repo.component_manager import ComponentManagerApiInterface
from austin_heller_repo.version_controlled_containerized_python_manager import VersionControlledContainerizedPythonManager, VersionControlledContainerizedPythonInstance


app = Flask(__name__)


specification_semaphore = Semaphore()
is_specification_loaded = False
specification = None  # type: Dict
temp_directory_per_component_uuid = {}  # type: Dict[str, tempfile.TemporaryDirectory]
component_specification_per_component_uuid = {}  # type: Dict[str, Dict]
vccpi_per_component_uuid = {}  # type: Dict[str, VersionControlledContainerizedPythonInstance]


def get_component_output(component_uuid: str, json_data_array: List[Dict], component_manager_api_base_url: str) -> Dict:
    global specification

    component_manager_api_interface = ComponentManagerApiInterface(
        component_manager_api_base_url=component_manager_api_base_url
    )

    specification_semaphore.acquire()
    try:
        if not is_specification_loaded:
            specification = component_manager_api_interface.get_docker_api_specification()
            # TODO use this specification for permitting updates while actively running
        specification_semaphore.release()
    except Exception as ex:
        specification_semaphore.release()
        raise ex

    # pull the component specifications if they have never been pulled before
    if component_uuid not in component_specification_per_component_uuid.keys():
        component_specification = component_manager_api_interface.get_docker_component_specification_by_component_uuid(
            component_uuid=component_uuid
        )
        component_specification_per_component_uuid[component_uuid] = component_specification

    # create the temp directory for the dockerfile of this component if it does not exist
    if component_uuid not in temp_directory_per_component_uuid.keys():
        temp_directory = tempfile.TemporaryDirectory()
        temp_directory_per_component_uuid[component_uuid] = temp_directory

    temp_directory = temp_directory_per_component_uuid[component_uuid]

    component_specification = component_specification_per_component_uuid[component_uuid]

    git_manager = GitManager(
        git_directory_path=temp_directory.name
    )

    # run script in component
    vccpm = VersionControlledContainerizedPythonManager(
        git_manager=git_manager
    )

    script_arguments = []  # type: List[str]
    configuration_argument_json = {
        "component_manager_api_base_url": component_manager_api_base_url
    }
    script_arguments.append(f"\"{json.dumps(configuration_argument_json)}\"")
    for json_data_array_element in json_data_array:
        script_arguments.append(f"\"{json.dumps(json_data_array_element)}\"")

    with vccpm.run_python_script(
        git_repo_clone_url=component_specification["git_repo_clone_url"],
        script_file_path=component_specification["script_file_path"],
        script_arguments=script_arguments,
        timeout_seconds=component_specification["timeout_seconds"],
        is_docker_socket_needed=component_specification["is_docker_socket_needed"]
    ) as vccpi:

        vccpi.wait()
        output_bytes = vccpi.get_output()

    output_string = output_bytes.decode()
    output_json = json.loads(output_string)

    return output_json


@app.route("/v1/test/health", methods=["GET", "POST"])
def test_health():
    return {"is_healthy": True}


@app.route("/v1/test/json/form", methods=["POST"])
def test_json_form():
    input_json_string = request.form["json"]
    print(f"type(input_json_string): {type(input_json_string)}")
    print(f"input_json_string: {input_json_string}")
    input_json = json.loads(input_json_string)
    return input_json


@app.route("/v1/test/json/json", methods=["POST"])
def test_json_json():
    input_json = request.get_json()
    return input_json


@app.route("/v1/test/component_manager_api", methods=["POST"])
def test_component_manager_api():
    input_json = request.get_json()
    if "component_manager_api_base_url" not in input_json:
        raise Exception(f"Failed to find \"component_manager_api_base_url\" in \"{input_json}\".")
    else:
        component_manager_api_base_url = input_json["component_manager_api_base_url"]
        component_manager_api_interface = ComponentManagerApiInterface(
            component_manager_api_base_url=component_manager_api_base_url
        )
        health = component_manager_api_interface.get_health()
        return health


@app.route("/v1/api/docker", methods=["POST"])
def docker():

    output = None  # type: Dict
    try:

        input_json = request.get_json()
        if "component_uuid" not in input_json:
            raise Exception(f"Failed to find \"component_uuid\" in json \"{input_json}\".")
        elif "json_data_array" not in input_json:
            raise Exception(f"Failed to find \"json_data_array\" in json \"{input_json}\".")
        elif "component_manager_api_base_url" not in input_json:
            raise Exception(f"Failed to find \"component_manager_api_base_url\" in json \"{input_json}\".")

        component_uuid = input_json["component_uuid"]
        json_data_array = input_json["json_data_array"]
        component_manager_api_base_url = input_json["component_manager_api_base_url"]

        if not isinstance(json_data_array, list):
            raise Exception(f"json_data_array was not an array: \"{json_data_array}\".")
        else:

            output = get_component_output(
                component_uuid=component_uuid,
                json_data_array=json_data_array,
                component_manager_api_base_url=component_manager_api_base_url
            )

    except Exception as ex:
        output = {
            "data": None,
            "exception": str(ex)
        }

    return output
