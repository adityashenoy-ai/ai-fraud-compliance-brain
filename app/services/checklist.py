from typing import Dict, List




def generate_checklist(metadata: Dict) -> List[Dict]:
"""Produce a basic checklist based on extracted metadata.
Each item contains: id, text, priority, due_by (optional)
"""
checklist = []
subject = metadata.get('subject') or metadata.get('headline') or ''
affected = metadata.get('affected_entities', [])


# High level items
checklist.append({'id': 'read_full', 'text': 'Read full circular and confirm exact applicability', 'priority': 'high'})
checklist.append({'id': 'legal_review', 'text': 'Schedule legal review of the circular', 'priority': 'high'})


if 'NBFC' in affected or 'PSP' in affected:
checklist.append({'id': 'ops_impact', 'text': 'Assess operational impact on transaction flows and settlements', 'priority': 'high'})
checklist.append({'id': 'tech_impact', 'text': 'Identify required changes in reconciliation / APIs', 'priority': 'medium'})


checklist.append({'id': 'update_policies', 'text': f'Update internal policy docs: {subject[:120]}', 'priority': 'medium'})
return checklist
