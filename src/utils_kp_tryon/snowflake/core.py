from dataclasses import dataclass

import snowflake.connector
import polars as pl


class SnowflakeClient:
    def __init__(self):
        self._connection: snowflake.connector.SnowflakeConnection | None = None

    @property
    def connection(self) -> snowflake.connector.SnowflakeConnection:
        if self._connection is None or self._connection.is_closed():
            self._connection = snowflake.connector.connect(connection_name="default")
        return self._connection

    def run_query(self, sql: str, params: dict | tuple | None = None) -> pl.DataFrame:
        with self.connection.cursor() as cur:
            cur.execute(sql, params)
            try:
                result = cur.fetch_arrow_all()
                return pl.from_arrow(result) if result is not None else pl.DataFrame()
            except snowflake.connector.errors.NotSupportedError:
                rows = cur.fetchall()
                if not rows:
                    return pl.DataFrame()
                columns = [c[0] for c in cur.description]
                return pl.DataFrame(rows, schema=columns, orient="row")

    def close(self):
        if self._connection is not None and not self._connection.is_closed():
            self._connection.close()
        self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


@dataclass(frozen=True)
class TablePath:
    database: str
    schema: str
    table: str

    @classmethod
    def parse(cls, path: str) -> "TablePath":
        parts = path.split(".")
        if len(parts) != 3:
            raise ValueError(f"Expected <database>.<schema>.<table>. Got {path!r}.")
        database, schema, table = (p.strip() for p in parts)
        return cls(
            database=database.upper(), schema=schema.upper(), table=table.upper()
        )


@dataclass(frozen=True)
class SchemaPath:
    database: str
    schema: str

    @classmethod
    def parse(cls, path: str) -> "SchemaPath":
        parts = path.split(".")
        if len(parts) != 2:
            raise ValueError(f"Expected <database>.<schema>. Got {path!r}.")
        database, schema = (p.strip() for p in parts)
        return cls(database=database.upper(), schema=schema.upper())


class SnowflakeExplorer:
    def __init__(self, client: SnowflakeClient):
        self._client = client

    def query(self, sql: str):
        return self._client.run_query(sql)

    def list_schemas(self, database: str) -> pl.DataFrame:
        sql = f"""
            select schema_name, created, last_altered
            from {database}.information_schema.schemata
            order by schema_name
        """
        return self._client.run_query(sql)

    def list_tables(self, schema_path: str) -> pl.DataFrame:
        p = SchemaPath.parse(schema_path)
        sql = f"""
            select table_name, table_type, created, last_altered, row_count
            from {p.database}.information_schema.tables
            where table_catalog = %(database)s and table_schema = %(schema)s
            order by table_type, table_name
        """
        params = {"database": p.database, "schema": p.schema}
        return self._client.run_query(sql, params)

    def list_columns(self, table_path: str) -> pl.DataFrame:
        p = TablePath.parse(table_path)
        sql = f"""
            select ordinal_position, column_name, data_type, comment
            from {p.database}.information_schema.columns
            where
                table_catalog = %(database)s
                and table_schema = %(schema)s
                and table_name = %(table)s
            order by ordinal_position
        """
        params = {"database": p.database, "schema": p.schema, "table": p.table}
        return self._client.run_query(sql, params)
