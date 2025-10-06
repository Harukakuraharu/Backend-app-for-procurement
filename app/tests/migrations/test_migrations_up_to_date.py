# """
# Test can find cases, when you've changed something in migration and forgot
# about models for some reason (or vice versa).
# """

# from alembic.autogenerate import compare_metadata
# from alembic.command import upgrade
# from alembic.config import Config
# from alembic.runtime.migration import MigrationContext
# from sqlalchemy.engine.base import Engine

# from models import Base


# def test_migrations_up_to_date(
#     alembic_config: Config, postgres_engine: Engine
# ):
#     """
#     Тест для проверки, что миграции были созданы: compare_metadata сравнивает миграцию локально и ту, которая была создана в тесте
#     передали сформированный конфиг алембика для тестов от make_alembic_config и движок от фикстуры postgres_engine_fixture
#     """
#     upgrade(alembic_config, "head")

#     migration_ctx = MigrationContext.configure(postgres_engine.connect())
#     diff = compare_metadata(migration_ctx, Base.metadata)
#     assert not diff











