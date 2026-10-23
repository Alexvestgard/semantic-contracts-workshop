"""Read-only SQL with a restricted syntax tree and database role."""

import psycopg
import sqlglot
from sqlglot import exp

TABLES = (
    "object", "object_history", "object_physical_properties", "object_gallery_info",
    "object_tags", "object_images", "object_copyright", "object_api_metadata",
)
FUNCTIONS = {
    "count", "sum", "avg", "min", "max", "lower", "upper", "trim", "ltrim",
    "rtrim", "length", "round", "abs", "array_size", "unnest", "extract",
    "date_trunc", "timestamp_trunc", "row_number", "rank", "dense_rank",
    "nullif", "coalesce", "case", "if", "and", "or", "cast", "array",
}
TYPES = {"SMALLINT", "INT", "BIGINT", "DECIMAL", "FLOAT", "DOUBLE", "TEXT",
         "VARCHAR", "CHAR", "BOOLEAN", "DATE", "TIMESTAMP", "TIMESTAMPTZ",
         "INTERVAL", "JSON", "JSONB"}


def validate_sql(sql):
    if not isinstance(sql, str) or not sql.strip() or len(sql) > 12000:
        raise ValueError("Submit a nonempty SQL query of at most 12,000 characters.")
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except sqlglot.errors.SqlglotError as error:
        raise ValueError("Could not parse the PostgreSQL query.") from error
    if len(statements) != 1 or not isinstance(statements[0], (exp.Select, exp.SetOperation)):
        raise ValueError("Only one SELECT statement is allowed.")
    tree = statements[0]
    ctes = {cte.alias for cte in tree.find_all(exp.CTE)}
    for node in tree.walk():
        if isinstance(node, (exp.DML, exp.DDL, exp.Command, exp.Into, exp.Lock)):
            raise ValueError("SQL may only read data, including inside CTEs; row locks are not allowed.")
        if isinstance(node, exp.Table):
            if node.db not in ("", "public") or node.catalog or node.name not in set(TABLES) | ctes:
                raise ValueError("Only the museum tables are available; use the schema tool.")
        if isinstance(node, exp.Dot):
            raise ValueError("Qualified functions and custom types are not allowed.")
        if isinstance(node, exp.Func):
            name = node.name if isinstance(node, exp.Anonymous) else node.sql_name()
            if name.lower() not in FUNCTIONS:
                raise ValueError("This function is outside the SQL tool's allowlist.")
        if isinstance(node, exp.DataType) and getattr(node.this, "value", None) not in TYPES:
            raise ValueError("Only ordinary built-in data casts are available.")
        if isinstance(node, exp.ObjectIdentifier):
            raise ValueError("Catalog identifier casts are not allowed.")


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
