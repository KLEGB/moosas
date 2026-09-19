"""Versioned file protocol for the SketchUp async airflow client."""
import argparse
import json
import math
import os
from pathlib import Path
import traceback

from ...model.io import load_model
from .runner import AirflowRunner, VentPaths


def atomic_json(filename, payload):
    filename = Path(filename)
    temporary = filename.with_suffix(filename.suffix + '.tmp')
    temporary.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    os.replace(temporary, filename)


def run_request(request, workspace):
    if request.get('schema_version') != 1 or not request.get('job_id'):
        raise ValueError('Unsupported airflow request schema or missing job_id')
    files = request['rdf_files']
    if not isinstance(files, list) or not files:
        raise ValueError('No RDF inputs')
    bc = request['boundary_conditions']
    for key in ('wind_speed_m_s', 'outdoor_temperature_c', 'indoor_temperature_c', 'alpha'):
        if not math.isfinite(float(bc[key])):
            raise ValueError(f'Non-finite boundary condition: {key}')
    if not isinstance(bc['thermal'], bool):
        raise ValueError('thermal must be boolean')
    vector = bc['wind_direction_vector']
    if len(vector) != 3 or not all(math.isfinite(float(v)) for v in vector) or sum(float(v)**2 for v in vector) == 0:
        raise ValueError('Invalid wind direction vector')
    result = dict(schema_version=1, job_id=request['job_id'], success=True, networks=[], warnings=[])
    for index, rdf in enumerate(files):
        model = load_model(rdf)
        paths = VentPaths.from_workspace(str(Path(workspace) / f'network-{index}'))
        run = AirflowRunner(model, paths=paths, wind_direction_vector=vector,
                            wind_speed=bc['wind_speed_m_s'], outdoor_temperature=bc['outdoor_temperature_c'],
                            indoor_temperature=bc['indoor_temperature_c'], thermal=bc['thermal'],
                            alpha=bc['alpha']).run()
        result['networks'].append(dict(
            rdf_file=str(Path(rdf).resolve()), paths=list(run.path_results),
            zones=[dict(uid=z.user_name, volume_m3=z.volume,
                        outdoor_inflow_m3_h=float(run.airflow_matrix[-1, i]),
                        temperature_c=z.temperatures[-1]) for i, z in enumerate(run.zones)],
            converged=run.converged, iterations=run.iteration_count, residual=run.residual))
        result['warnings'].extend(run.warnings)
    return result


def execute(request_path):
    request_path = Path(request_path).resolve()
    request = json.loads(request_path.read_text(encoding='utf-8-sig'))
    try:
        result = run_request(request, request_path.parent)
        atomic_json(request_path.parent / 'result.json', result)
        return result
    except Exception as exc:
        atomic_json(request_path.parent / 'result.json', dict(
            schema_version=1, job_id=request.get('job_id'), success=False,
            error=str(exc), traceback=traceback.format_exc()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', required=True)
    execute(parser.parse_args().request)
