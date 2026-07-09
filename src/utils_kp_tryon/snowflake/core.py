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

    def run_query(self, sql: str) -> pl.DataFrame:
        with self.connection.cursor() as cur:
            cur.execute(sql)
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
