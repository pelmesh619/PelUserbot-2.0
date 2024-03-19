import psycopg2
from psycopg2 import errors

import asyncpg

import sqlalchemy
from sqlalchemy import URL, create_engine, text


class Database:

    def __init__(self, app, config):
        self.app = app
        self.config = config

    @staticmethod
    def escape(value):
        return str(value).translate({i: chr(i) * 2 for i in b'\''})


class PostgreSQLDatabase(Database):
    def __init__(self, app, config):
        super().__init__(app, config)

        try:
            self.conn = psycopg2.connect(
                database=self.config['dbname'],
                user=self.config['user'],
                password=self.config['password'],
                host=self.config['host'],
                port=self.config['port']
            )
        except Exception as e:
            # TODO logs
            self.conn = None

        else:
            self.conn.autocommit = True

    def exec(self, command, to_log=True):
        if not self.conn:
            return []
        cursor = self.conn.cursor()

        cursor.execute(command)

        if to_log:
            # TODO logs
            pass

        return True

    def exec_and_fetch(self, command, to_log=True):
        if not self.conn:
            return []
        cursor = self.conn.cursor()

        cursor.execute(command)

        if to_log:
            # TODO logs
            pass

        try:
            return cursor.fetchall()
        except errors.ProgrammingError:
            return True
        except Exception as e:
            pass

            # TODO logs

    execute = exec
    execute_and_fetch = exec_and_fetch


class AsyncPostgreSQLDatabase(Database):
    def __init__(self, app, config):
        super().__init__(app, config)
        self.conn = None

    async def connect(self):
        self.conn = await asyncpg.connect(
            database=self.config['dbname'],
            user=self.config['user'],
            password=self.config['password'],
            host=self.config['host'],
            port=self.config['port']
        )

    async def exec(self, command, to_log=True):
        if self.conn is None:
            await self.connect()
        async with self.conn.transaction():

            await self.conn.execute(command)
            if to_log:
                # TODO logs
                pass

            return True

    async def exec_and_fetch(self, command, to_log=True):
        if self.conn is None:
            await self.connect()
        async with self.conn.transaction():

            result = await self.conn.fetch(command)
            if to_log:
                # TODO logs
                pass
            return result

    execute = exec
    execute_and_fetch = exec_and_fetch


class SQLAlchemyDatabase(Database):
    def __init__(self, app, config):
        super().__init__(app, config)
        dialect = 'postgresql'
        driver = 'psycopg2'

        url_object = URL.create(
            f"{dialect}+{driver}",
            database=self.config['dbname'],
            username=self.config['user'],
            password=self.config['password'],
            host=self.config['host'],
            port=self.config['port']
        )
        try:
            self.engine = create_engine(url_object)
        except Exception as e:
            pass

            # TODO logs

    async def exec(self, command, to_log=True):
        with self.engine.connect() as conn:
            result = conn.execute(text(command))
            if to_log:
                # TODO logs
                pass

            return True

    async def exec_and_fetch(self, command, to_log=True):
        with self.engine.connect() as conn:
            result = conn.execute(text(command))
            if to_log:
                # TODO logs
                pass

            return result

    execute = exec
    execute_and_fetch = exec_and_fetch


DATABASE_TYPES = {
    'postgresql': PostgreSQLDatabase,
    'psycopg2': PostgreSQLDatabase,
    'asyncpostgresql': AsyncPostgreSQLDatabase,
    'asyncpg': AsyncPostgreSQLDatabase,
    'sqlalchemy': SQLAlchemyDatabase
}
