import json
import argparse
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

parser = argparse.ArgumentParser()
parser.add_argument('--report', type=Path, default=Path('build/reports/spotbugs/spotbugs.sarif'))
parser.add_argument('--after-upload', action='store_true')
args = parser.parse_args()
report = args.report
data = json.loads(report.read_text())
assert data['version'] == '2.1.0', 'Unexpected SARIF version'
assert data['runs'], 'Missing analysis runs'
sources = {}
for main in Path('.').glob('junit-*/src/main'):
    for language in ('java', 'kotlin'):
        source_root = main / language
        for source in source_root.rglob('*'):
            if source.is_file():
                sources.setdefault(source.relative_to(source_root).as_posix(), []).append(source)

def resolve(uri):
    uri = unquote(uri)
    direct = Path(uri)
    if not direct.is_absolute() and direct.is_file():
        return direct
    matches = sources.get(uri.removeprefix('./'), [])
    assert len(matches) <= 1, f'Ambiguous source URI: {uri}'
    return matches[0] if matches else None

def normalize(value):
    if isinstance(value, dict):
        if 'uri' in value:
            source = resolve(value['uri'])
            if source:
                value['uri'] = source.as_posix()
                value.pop('uriBaseId', None)
        for child in value.values():
            normalize(child)
    elif isinstance(value, list):
        for child in value:
            normalize(child)

if not args.after_upload:
    normalize(data)
    report.write_text(json.dumps(data, indent=2) + '\n')

results = [result for run in data['runs'] for result in run.get('results', [])]
locations = [location['physicalLocation'] for result in results for location in result.get('locations', [])]
coverage = Counter()
errors = []
for location in locations:
    uri = location['artifactLocation']['uri']
    source = resolve(uri)
    if source is None:
        coverage['unresolved_source'] += 1
        continue
    region = location.get('region', {})
    start = region.get('startLine')
    if not start:
        coverage['missing_line'] += 1
        continue
    lines = source.read_text(encoding='utf-8').splitlines()
    if start > len(lines):
        coverage['line_out_of_range'] += 1
        continue
    coverage['valid_source_line'] += 1
    if args.after_upload:
        expected = '\n'.join(lines[start - 1:region.get('endLine', start)])
        actual = region.get('snippet', {}).get('text')
        if actual != expected:
            errors.append(f'{uri}:{start}')
        else:
            coverage['correct_snippet'] += 1
summary = {
    'sarif_version': data['version'],
    'tools': [run['tool']['driver']['name'] for run in data['runs']],
    'results': len(results),
    'locations': len(locations),
    'rules': len({result['ruleId'] for result in results}),
    'source_coverage': dict(coverage),
    'snippet_mismatches': errors,
}
inputs = Path('build/spotbugs-inputs/classes.txt')
if inputs.exists():
    summary['class_directories'] = len(inputs.read_text().splitlines())
summary_path = report.with_name('summary-after-upload.json' if args.after_upload else 'summary.json')
summary_path.write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
assert not coverage['unresolved_source'], 'Unresolved production source paths'
assert not errors, 'Uploader produced missing or incorrect snippets at valid source lines'
