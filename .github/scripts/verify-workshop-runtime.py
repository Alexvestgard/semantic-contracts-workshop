"""Exercise the unmodified development environment and participant notebook."""

import json
import subprocess
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from psycopg import connect, sql


def main():
    source = json.loads(Path(
        'data_contract_components/data_assets/db_migrations/raw_data/objects.json'
    ).read_text())
    expected = {row['objectID'] for row in source}
    if len(expected) != 3025:
        raise AssertionError(f'Expected 3025 source objects; found {len(expected)}')

    with connect('postgresql://postgres:postgres@postgres:5432/postgres') as conn:
        for table in (
            'object', 'object_history', 'object_physical_properties',
            'object_gallery_info', 'object_tags', 'object_images',
            'object_copyright', 'object_api_metadata',
        ):
            rows = conn.execute(sql.SQL('SELECT object_id FROM {}').format(
                sql.Identifier(table)
            )).fetchall()
            if len(rows) != len(expected) or {row[0] for row in rows} != expected:
                raise AssertionError(f'{table}: seeded IDs differ from source')
            print(f'{table}: all {len(rows)} source object IDs present', flush=True)

    notebook = nbformat.read('run_sql_queries_here.ipynb', as_version=4)
    placeholder = 'YOUR QUERY HERE;'
    query_cells = [cell for cell in notebook.cells
                   if cell.cell_type == 'code' and placeholder in cell.source]
    if len(query_cells) != 1:
        raise AssertionError('Expected exactly one participant query placeholder')
    query_cells[0].source = query_cells[0].source.replace(
        placeholder, 'SELECT COUNT(*) AS object_count FROM object;'
    )
    NotebookClient(notebook, timeout=60, kernel_name='python3',
                   resources={'metadata': {'path': '/workspace'}}).execute()
    output = str(query_cells[0].outputs)
    print(f'Executed notebook query output: {output}', flush=True)
    if '3025' not in output:
        raise AssertionError('Notebook query did not return the seeded object count')
    Path('.evidence').mkdir(exist_ok=True)
    nbformat.write(notebook, '.evidence/executed-notebook.ipynb')
    subprocess.run([
        'python', '-m', 'unittest',
        'data_contract_components/prevention/test_data_contract_violations.py', '-v'
    ], check=True)


if __name__ == '__main__':
    main()
