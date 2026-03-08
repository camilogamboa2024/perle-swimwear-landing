#!/usr/bin/env python
import argparse
import json
import re
import sys
from pathlib import Path


def _init_counts():
    return {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}


def _normalize_severity(value, default='medium'):
    severity = (value or '').strip().lower()
    mapping = {
        'critical': 'critical',
        'high': 'high',
        'error': 'high',
        'warning': 'medium',
        'medium': 'medium',
        'low': 'low',
        'info': 'low',
    }
    return mapping.get(severity, default)


def _update_counts(counts, severity):
    if severity in counts:
        counts[severity] += 1


def _load_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError:
        return None


def _parse_score(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r'([0-9]+(?:\.[0-9]+)?)', value)
        if match:
            return float(match.group(1))
    return None


def _severity_from_score(score):
    if score is None:
        return None
    if score >= 9.0:
        return 'critical'
    if score >= 7.0:
        return 'high'
    if score >= 4.0:
        return 'medium'
    return 'low'


def _parse_pip_vuln_severity(vuln):
    severities = vuln.get('severity') or vuln.get('severities')
    if isinstance(severities, list):
        scores = []
        for entry in severities:
            score = _parse_score(entry.get('score') if isinstance(entry, dict) else entry)
            if score is not None:
                scores.append(score)
        if scores:
            return _severity_from_score(max(scores))
    if isinstance(severities, dict):
        score = _parse_score(severities.get('score'))
        return _severity_from_score(score)
    if isinstance(severities, str):
        score = _parse_score(severities)
        severity = _severity_from_score(score)
        if severity:
            return severity
    return 'high'


def _parse_zap_risk(alert):
    riskcode = alert.get('riskcode')
    if riskcode is None:
        return 'medium'
    if isinstance(riskcode, str):
        match = re.search(r'([0-9])', riskcode)
        if match:
            riskcode = int(match.group(1))
    if riskcode == 4:
        return 'critical'
    if riskcode == 3:
        return 'high'
    if riskcode == 2:
        return 'medium'
    return 'low'


def _collect_findings(input_dir):
    findings = []
    per_source = {}
    totals = _init_counts()

    def add_finding(source, severity, message, finding_id=''):
        normalized_severity = _normalize_severity(severity)
        findings.append(
            {
                'source': source,
                'id': finding_id,
                'severity': normalized_severity,
                'message': message,
            }
        )
        if source not in per_source:
            per_source[source] = _init_counts()
        _update_counts(per_source[source], normalized_severity)
        _update_counts(totals, normalized_severity)

    bandit_report = _load_json(input_dir / 'bandit.json')
    if bandit_report is None:
        add_finding('bandit', 'high', 'No se encontro o no se pudo parsear bandit.json', 'bandit_report_missing')
    else:
        for result in bandit_report.get('results', []):
            severity = _normalize_severity(result.get('issue_severity'))
            add_finding(
                'bandit',
                severity,
                result.get('issue_text', 'Bandit finding'),
                result.get('test_id', ''),
            )

    pip_report = _load_json(input_dir / 'pip-audit.json')
    if pip_report is None:
        add_finding('pip-audit', 'high', 'No se encontro o no se pudo parsear pip-audit.json', 'pip_audit_report_missing')
    else:
        if isinstance(pip_report, dict):
            dependencies = pip_report.get('dependencies', [])
        elif isinstance(pip_report, list):
            dependencies = pip_report
        else:
            dependencies = []

        if not isinstance(dependencies, list):
            add_finding('pip-audit', 'high', 'Formato inesperado en pip-audit.json', 'pip_audit_invalid_format')
            dependencies = []

        for dependency in dependencies:
            if not isinstance(dependency, dict):
                continue
            package_name = dependency.get('name', 'unknown-package')
            for vuln in dependency.get('vulns', []):
                severity = _parse_pip_vuln_severity(vuln)
                add_finding(
                    'pip-audit',
                    severity,
                    f"{package_name} vulnerable ({vuln.get('id', 'unknown-id')})",
                    vuln.get('id', ''),
                )

    semgrep_report = _load_json(input_dir / 'semgrep.json')
    if semgrep_report is None:
        add_finding('semgrep', 'high', 'No se encontro o no se pudo parsear semgrep.json', 'semgrep_report_missing')
    else:
        for result in semgrep_report.get('results', []):
            extra = result.get('extra', {})
            severity = _normalize_severity(extra.get('severity'), default='medium')
            add_finding(
                'semgrep',
                severity,
                extra.get('message', 'Semgrep finding'),
                result.get('check_id', ''),
            )

    for custom_report in ['dast_auth_csrf.json', 'security_headers.json']:
        report_data = _load_json(input_dir / custom_report)
        source_name = custom_report.replace('.json', '')
        if report_data is None:
            add_finding(source_name, 'high', f'No se encontro o no se pudo parsear {custom_report}', f'{source_name}_missing')
            continue
        for finding in report_data.get('findings', []):
            add_finding(
                source_name,
                finding.get('severity', 'medium'),
                finding.get('message', f'Finding en {source_name}'),
                finding.get('id', ''),
            )

    zap_report = _load_json(input_dir / 'zap_report.json')
    if zap_report is None:
        add_finding('zap', 'high', 'No se encontro o no se pudo parsear zap_report.json', 'zap_report_missing')
    else:
        for site in zap_report.get('site', []):
            for alert in site.get('alerts', []):
                severity = _parse_zap_risk(alert)
                add_finding(
                    'zap',
                    severity,
                    alert.get('alert', 'ZAP alert'),
                    alert.get('pluginid', ''),
                )

    return findings, per_source, totals


def _write_markdown(path, summary):
    lines = [
        '# Security Gate Summary',
        '',
        f"- Verdict: **{summary['verdict']}**",
        f"- Critical: {summary['totals']['critical']}",
        f"- High: {summary['totals']['high']}",
        f"- Medium: {summary['totals']['medium']}",
        f"- Low: {summary['totals']['low']}",
        '',
        '## By Source',
        '',
        '| Source | Critical | High | Medium | Low |',
        '| --- | ---: | ---: | ---: | ---: |',
    ]
    for source, counts in sorted(summary['per_source'].items()):
        lines.append(
            f"| {source} | {counts['critical']} | {counts['high']} | {counts['medium']} | {counts['low']} |"
        )
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='Unified security gate (Critical/High blocker).')
    parser.add_argument('--input-dir', required=True, help='Directory with JSON reports')
    parser.add_argument('--out', required=True, help='Output summary JSON path')
    parser.add_argument('--markdown', help='Optional output markdown path')
    parser.add_argument('--strict-critical-high', action='store_true')
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    findings, per_source, totals = _collect_findings(input_dir)

    verdict = 'PASS'
    if args.strict_critical_high and (totals['critical'] > 0 or totals['high'] > 0):
        verdict = 'FAIL'

    summary = {
        'input_dir': str(input_dir),
        'verdict': verdict,
        'totals': totals,
        'per_source': per_source,
        'findings': findings,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')

    if args.markdown:
        markdown_path = Path(args.markdown)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        _write_markdown(markdown_path, summary)

    print(
        f"Security gate -> verdict={verdict} critical={totals['critical']} high={totals['high']} "
        f"medium={totals['medium']} low={totals['low']}"
    )

    if verdict == 'FAIL':
        sys.exit(1)


if __name__ == '__main__':
    main()
