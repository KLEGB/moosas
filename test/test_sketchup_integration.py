import json
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from MoosasPy.simulation.airflow.sketchup_job import run_request
from MoosasPy.transform.idf_export import export_idf_batch


def test_sketchup_airflow_request_maps_inputs_and_results(tmp_path):
    request = {
        "schema_version": 1,
        "job_id": "job-1",
        "rdf_files": [str(tmp_path / "model.ttl")],
        "boundary_conditions": {
            "wind_speed_m_s": 3.0,
            "outdoor_temperature_c": 30.0,
            "indoor_temperature_c": 24.0,
            "alpha": 0.22,
            "thermal": False,
            "wind_direction_vector": [1.0, 0.0, 0.0],
        },
    }
    airflow_result = SimpleNamespace(
        airflow_matrix=np.array([[0.0, 1.0], [2.0, 0.0]]),
        zones=(SimpleNamespace(user_name="room", volume=30.0, temperatures=(24.0,)),),
        path_results=({"uid": "window"},),
        converged=True,
        iteration_count=1,
        residual=0.0,
        warnings=(),
    )

    with patch(
        "MoosasPy.simulation.airflow.sketchup_job.load_model",
        return_value="model",
    ), patch(
        "MoosasPy.simulation.airflow.sketchup_job.AirflowRunner"
    ) as runner:
        runner.return_value.run.return_value = airflow_result
        result = run_request(request, tmp_path)

    assert result["schema_version"] == 1
    assert result["job_id"] == "job-1"
    assert result["networks"][0]["paths"] == [{"uid": "window"}]
    assert result["networks"][0]["zones"] == [{
        "uid": "room",
        "volume_m3": 30.0,
        "outdoor_inflow_m3_h": 2.0,
        "temperature_c": 24.0,
    }]
    assert runner.call_args.kwargs["thermal"] is False
    assert runner.call_args.kwargs["wind_direction_vector"] == [1.0, 0.0, 0.0]


def test_idf_batch_export_writes_manifest(tmp_path):
    source = tmp_path / "model.ttl"
    source.write_text("model", encoding="utf-8")
    output_dir = tmp_path / "idf"

    with patch("MoosasPy.transform.idf_export.load_model", return_value="model"), patch(
        "MoosasPy.transform.idf_export.exportIDF"
    ) as export_idf:
        manifest_path = export_idf_batch([str(source)], str(output_dir))

    manifest = json.loads((output_dir / "idf_export_manifest.json").read_text(encoding="utf-8"))
    assert manifest_path == str(output_dir / "idf_export_manifest.json")
    assert manifest == {
        "sources": [str(source.resolve())],
        "idf_files": [str(output_dir / "model.idf")],
    }
    export_idf.assert_called_once_with("model", str(output_dir / "model.idf"), idfTemplatePath=None)