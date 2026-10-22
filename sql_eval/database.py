"""Read-only SQL with a restricted syntax tree and database role."""

import hashlib
import json

import psycopg
from pglast import parser

from .common import dumps

TABLES = (
    "object", "object_history", "object_physical_properties", "object_gallery_info",
    "object_tags", "object_images", "object_copyright", "object_api_metadata",
)
FUNCTIONS = {
    "count", "sum", "avg", "min", "max", "lower", "upper", "btrim", "ltrim",
    "rtrim", "length", "char_length", "round", "abs", "cardinality", "array_length",
    "unnest", "date_part", "date_trunc", "row_number", "rank", "dense_rank",
}


def validate_sql(sql):
    if not isinstance(sql, str) or not sql.strip() or len(sql) > 12000:
        raise ValueError("Submit a nonempty SQL query of at most 12,000 characters.")
    tree = json.loads(parser.parse_sql_json(sql))
    stmts = tree.get("stmts", [])
    if len(stmts) != 1 or set(stmts[0]["stmt"]) != {"SelectStmt"}:
        raise ValueError("Only one SELECT statement is allowed.")
    ctes = set()

    def collect(node):
        if isinstance(node, dict):
            if "CommonTableExpr" in node:
                ctes.add(node["CommonTableExpr"]["ctename"])
            for value in node.values():
                collect(value)
        elif isinstance(node, list):
            for value in node:
                collect(value)
    collect(tree)

    def check(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key.endswith("Stmt") and key != "SelectStmt":
                    raise ValueError("SQL may only read data, including inside CTEs.")
                if key in {"intoClause", "lockingClause"} and value:
                    raise ValueError("SELECT INTO and row locks are not allowed.")
                if key == "RangeVar":
                    if value.get("schemaname", "public") != "public" or value.get("catalogname"):
                        raise ValueError("Only the museum tables are available.")
                    if value["relname"] not in set(TABLES) | ctes:
                        raise ValueError("Only the museum tables are available; use the schema tool.")
                if key == "FuncCall":
                    names = [part["String"]["sval"] for part in value["funcname"]]
                    if len(names) != 1 or names[0].lower() not in FUNCTIONS:
                        raise ValueError("This function is outside the SQL tool's allowlist.")
                if key in {"TypeName", "typeName"}:
                    names = [part["String"]["sval"] for part in value.get("names", [])]
                    types = {"int2", "int4", "int8", "integer", "bigint", "numeric", "float4", "float8",
                             "text", "varchar", "bpchar", "bool", "boolean", "date", "timestamp",
                             "timestamptz", "interval", "json", "jsonb"}
                    if not names or names[-1] not in types or (len(names) > 1 and names[:-1] != ["pg_catalog"]):
                        raise ValueError("Only ordinary built-in data casts are available.")
                check(value)
        elif isinstance(node, list):
            for value in node:
                check(value)
    check(tree)


class Database:
    def __init__(self, dsn, timeout_ms=2000):
        self.dsn = dsn
        self.timeout_ms = timeout_ms

    def connection(self):
        conn = psycopg.connect(self.dsn, connect_timeout=5)
        conn.read_only = True
        return conn

    def query(self, sql, limit=30):
        validate_sql(sql)
        with self.connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT set_config('statement_timeout', %s, true)", (str(self.timeout_ms),))
            cur.execute("SET LOCAL search_path = pg_catalog, public")
            cur.execute(sql, prepare=True)
            rows = cur.fetchmany(limit + 1)
            return {"columns": [col.name for col in cur.description],
                    "rows": rows[:limit], "truncated": len(rows) > limit}

    def schema(self, table=None):
        if table is None or table not in TABLES:
            with self.connection() as conn:
                rows = conn.execute("""
                    SELECT table_name, column_name FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = ANY(%s)
                    ORDER BY table_name, ordinal_position
                """, (list(TABLES),)).fetchall()
            overview = {name: [] for name in TABLES}
            for name, column in rows:
                overview[name].append(column)
            result = {"tables": overview}
            if table is not None:
                result["error"] = "Unknown table. Choose a table from this schema."
            return result
        with self.connection() as conn:
            rows = conn.execute("""
                SELECT a.attname, format_type(a.atttypid, a.atttypmod),
                       col_description(a.attrelid, a.attnum)
                FROM pg_attribute a
                WHERE a.attrelid = %s::regclass AND a.attnum > 0 AND NOT a.attisdropped
                ORDER BY a.attnum
            """, ("public." + table,)).fetchall()
        return {"table": table, "columns": rows}

    def fingerprint(self):
        # Loader timestamps vary by startup and are not used by this question set.
        h = hashlib.sha256()
        with self.connection() as conn:
            for table in TABLES:
                h.update(dumps(self.schema(table)).encode())
                rows = conn.execute(
                    f"SELECT to_jsonb(t) - 'created_at' FROM public.{table} t ORDER BY object_id"
                ).fetchall()
                h.update(dumps(rows).encode())
        return h.hexdigest()
