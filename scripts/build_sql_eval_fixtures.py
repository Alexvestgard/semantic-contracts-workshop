"""Regenerate draft questions, independent answers, and prompts before freezing a run."""
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
data = root / 'data_contract_components/data_assets/db_migrations/raw_data/objects.json'
a = json.loads(data.read_text())

def filled(x):
    return x is not None and bool(str(x).strip())
q = []
gold = {}

def add(id, level, text, sql, expected, ordered=False):
    q.append(dict(id=id, difficulty=level, question=text, ordered=ordered))
    gold[id] = dict(sql=sql, expected=expected)
add('q01', 'basic', 'How many artworks are in the museum sample? Return one count.', 'SELECT COUNT(*) FROM object', [[len(a)]])
add('q02', 'basic', 'How many artworks have a populated artist name? NULL, empty, and whitespace-only names are missing. Return one count.', "SELECT COUNT(*) FROM object WHERE NULLIF(BTRIM(artist_display_name), '') IS NOT NULL", [[sum((filled(x.get('artistDisplayName')) for x in a))]])
add('q03', 'basic', 'How many artworks have a missing artist name? Include NULL, empty, and whitespace-only names. Return one count.', "SELECT COUNT(*) FROM object WHERE NULLIF(BTRIM(artist_display_name), '') IS NULL", [[sum((not filled(x.get('artistDisplayName')) for x in a))]])
add('q04', 'basic', 'How many artworks are explicitly marked as public domain? Return one count.', 'SELECT COUNT(*) FROM object_copyright WHERE is_public_domain IS TRUE', [[sum((x.get('isPublicDomain') is True for x in a))]])
add('q05', 'basic', 'How many artworks have a populated primary image URL? NULL, empty, and whitespace-only URLs are missing. Return one count.', "SELECT COUNT(*) FROM object_images WHERE NULLIF(BTRIM(primary_image), '') IS NOT NULL", [[sum((filled(x.get('primaryImage')) for x in a))]])
add('q06', 'basic', 'How many artworks have no populated primary image URL? Include NULL, empty, and whitespace-only URLs. Return one count.', "SELECT COUNT(*) FROM object_images WHERE NULLIF(BTRIM(primary_image), '') IS NULL", [[sum((not filled(x.get('primaryImage')) for x in a))]])
add('q07', 'basic', 'How many artworks belong to the Asian Art department? Return one count.', "SELECT COUNT(*) FROM object_gallery_info WHERE department = 'Asian Art'", [[sum((x.get('department') == 'Asian Art' for x in a))]])
add('q08', 'basic', 'How many artworks have a populated classification? NULL, empty, and whitespace-only classifications are missing. Return one count.', "SELECT COUNT(*) FROM object_physical_properties WHERE NULLIF(BTRIM(classification), '') IS NOT NULL", [[sum((filled(x.get('classification')) for x in a))]])
add('q09', 'basic', 'Return object ID and title for the five artworks with the smallest object IDs, in ascending ID order.', 'SELECT object_id, title FROM object ORDER BY object_id LIMIT 5', [[x['objectID'], x.get('title')] for x in sorted(a, key=lambda x: x['objectID'])[:5]], True)
add('q10', 'basic', 'How many artworks have a populated culture? NULL, empty, and whitespace-only culture values are missing. Return one count.', "SELECT COUNT(*) FROM object_history WHERE NULLIF(BTRIM(culture), '') IS NOT NULL", [[sum((filled(x.get('culture')) for x in a))]])
from collections import Counter

def groups(field, pred=lambda x: True):
    return [[k, v] for k, v in sorted(Counter((x.get(field) for x in a if pred(x))).items())]
add('q11', 'intermediate', 'Return every department and its artwork count, sorted by department name ascending.', 'SELECT department, COUNT(*) FROM object_gallery_info GROUP BY department ORDER BY department', groups('department'), True)
add('q12', 'intermediate', 'For each department with public-domain artworks, return department and public-domain artwork count, sorted by department ascending.', 'SELECT g.department, COUNT(*) FROM object_gallery_info g JOIN object_copyright c USING (object_id) WHERE c.is_public_domain IS TRUE GROUP BY g.department ORDER BY g.department', groups('department', lambda x: x.get('isPublicDomain') is True), True)
add('q13', 'intermediate', 'For each department with missing artist names, return department and that count, sorted by department ascending. NULL, empty, and whitespace-only artist names are missing.', "SELECT g.department, COUNT(*) FROM object_gallery_info g JOIN object o USING (object_id) WHERE NULLIF(BTRIM(o.artist_display_name), '') IS NULL GROUP BY g.department ORDER BY g.department", groups('department', lambda x: not filled(x.get('artistDisplayName'))), True)
add('q14', 'intermediate', 'For each department with populated primary image URLs, return department and that count, sorted by department ascending. NULL, empty, and whitespace-only URLs are missing.', "SELECT g.department, COUNT(*) FROM object_gallery_info g JOIN object_images i USING (object_id) WHERE NULLIF(BTRIM(i.primary_image), '') IS NOT NULL GROUP BY g.department ORDER BY g.department", groups('department', lambda x: filled(x.get('primaryImage'))), True)
add('q15', 'intermediate', 'How many public-domain artworks are classified exactly as Paintings? Return one count.', "SELECT COUNT(*) FROM object_copyright c JOIN object_physical_properties p USING (object_id) WHERE c.is_public_domain IS TRUE AND p.classification = 'Paintings'", [[sum((x.get('isPublicDomain') is True and x.get('classification') == 'Paintings' for x in a))]])
add('q16', 'intermediate', 'How many Asian Art artworks have a populated culture? NULL, empty, and whitespace-only cultures are missing. Return one count.', "SELECT COUNT(*) FROM object_gallery_info g JOIN object_history h USING (object_id) WHERE g.department = 'Asian Art' AND NULLIF(BTRIM(h.culture), '') IS NOT NULL", [[sum((x.get('department') == 'Asian Art' and filled(x.get('culture')) for x in a))]])
add('q17', 'intermediate', 'How many artworks with a populated primary image URL are not explicitly marked public domain? NULL, empty, and whitespace-only URLs are missing. Return one count.', "SELECT COUNT(*) FROM object_images i JOIN object_copyright c USING (object_id) WHERE NULLIF(BTRIM(i.primary_image), '') IS NOT NULL AND c.is_public_domain IS NOT TRUE", [[sum((filled(x.get('primaryImage')) and x.get('isPublicDomain') is not True for x in a))]])
add('q18', 'intermediate', 'Return the five departments with the most artworks as department and count, sorted by count descending, then department ascending for ties.', 'SELECT department, COUNT(*) AS n FROM object_gallery_info GROUP BY department ORDER BY n DESC, department ASC LIMIT 5', sorted(groups('department'), key=lambda x: (-x[1], x[0]))[:5], True)
add('q19', 'intermediate', 'Return object ID, title, and department for the five public-domain artworks with the smallest object IDs, sorted by ID ascending.', 'SELECT o.object_id, o.title, g.department FROM object o JOIN object_gallery_info g USING (object_id) JOIN object_copyright c USING (object_id) WHERE c.is_public_domain IS TRUE ORDER BY o.object_id LIMIT 5', [[x['objectID'], x.get('title'), x.get('department')] for x in sorted(a, key=lambda x: x['objectID']) if x.get('isPublicDomain') is True][:5], True)
add('q20', 'intermediate', 'For each department with populated classifications, return department and the number of distinct populated classifications, sorted by department ascending. NULL, empty, and whitespace-only classifications are missing.', "SELECT g.department, COUNT(DISTINCT p.classification) FROM object_gallery_info g JOIN object_physical_properties p USING (object_id) WHERE NULLIF(BTRIM(p.classification), '') IS NOT NULL GROUP BY g.department ORDER BY g.department", [[dep, len({x.get('classification') for x in a if x.get('department') == dep and filled(x.get('classification'))})] for dep in sorted({x['department'] for x in a}) if any((x['department'] == dep and filled(x.get('classification')) for x in a))], True)

def write(p, v):
    (root / p).write_text(json.dumps(v, indent=2, ensure_ascii=False) + '\n')
write('eval/questions.json', q)
write('eval/gold/answers.json', {'sentinel': 'GOLD_ONLY_8b45b406_reference_answers', 'answers': gold})
write('eval/pilots.json', [{'id': 'p01', 'question': 'Return the three largest object IDs in descending order.', 'ordered': True}, {'id': 'p02', 'question': 'How many artworks belong to the Musical Instruments department? Return one count.', 'ordered': False}, {'id': 'p03', 'question': 'Return object ID and title for the first three Asian Art artworks by ascending object ID.', 'ordered': True}])
base = {'instructions': 'Answer the question using the database tools. Submit the requested result values as rows.', 'semantics': {}}
improved = {'instructions': 'Inspect the relevant tables before writing SQL. Check column names and sample values. Test your query, fix errors, and submit the result values that answer the question exactly.', 'semantics': {'missing_text': 'null_or_blank', 'object_key': 'object_id', 'public_domain': 'explicit_true', 'ordering': 'question'}}
regressed = json.loads(json.dumps(improved))
regressed['semantics']['missing_text'] = 'null_only'
for name, v in [('baseline', base), ('improved', improved), ('regressed', regressed)]:
    write('eval/prompts/' + name + '.json', v)

write('eval/prompt-contract.json', {'version': 1, 'required_semantics': improved['semantics'], 'scope': 'Checks declared semantic settings and approved free-text instructions; does not prove model compliance.', 'approved_instructions': improved['instructions']})
write('eval/pilot-budget.json', {'status': 'pilot', 'max_tool_calls': 12, 'question_timeout_seconds': 180, 'request_timeout_seconds': 45, 'max_output_tokens': 384, 'tool_row_limit': 20, 'history_characters': 6500, 'observation_characters': 3000})
print('20 questions, 3 pilots, 3 prompt versions; reference answers calculated from source JSON')
