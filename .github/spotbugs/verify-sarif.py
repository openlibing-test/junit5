import json
from pathlib import Path

report = Path('build/reports/spotbugs/spotbugs.sarif')
data = json.loads(report.read_text())
assert data['version'] == '2.1.0', 'Unexpected SARIF version'
assert data['runs'], 'Missing analysis runs'
results = [result for run in data['runs'] for result in run.get('results', [])]
locations = [location['physicalLocation'] for result in results for location in result.get('locations', [])]
summary = {
    'sarif_version': data['version'],
    'tools': [run['tool']['driver']['name'] for run in data['runs']],
    'results': len(results),
    'locations': len(locations),
    'rules': len({result['ruleId'] for result in results}),
    'class_directories': len(Path('build/spotbugs-inputs/classes.txt').read_text().splitlines()),
}
Path('build/reports/spotbugs/summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
