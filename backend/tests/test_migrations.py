"""The migrations run cleanly in both directions, and they describe exactly what the models describe."""

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

import app.db.models  # noqa: F401  (registers every model)
from app.db.base import Base
from app.db.models.enums import ALL_ENUM_TYPES
from tests.migration_helpers import alembic_config, scratch_database

TABLES = {
    "users", "subjects", "questions", "answer_options", "test_attempts", "responses",
    "classifier_predictions", "results", "feedback", "subscriptions", "payments",
}


@pytest.fixture(scope="module")
def migrated_scratch(app):
    """An empty database that has gone upgrade head -> downgrade base -> upgrade head."""
    with scratch_database(app.config["SQLALCHEMY_DATABASE_URI"]) as url:
        config = alembic_config(url)
        command.upgrade(config, "head")
        command.downgrade(config, "base")

        engine = create_engine(url)
        with engine.connect() as connection:
            leftover_tables = set(inspect(connection).get_table_names()) - {"alembic_version"}
            leftover_types = connection.execute(
                text("SELECT typname FROM pg_type WHERE typtype = 'e'")
            ).scalars().all()
        assert leftover_tables == set(), "downgrade base left tables behind"
        assert leftover_types == [], "downgrade base left enum types behind"

        command.upgrade(config, "head")
        yield engine
        engine.dispose()


def test_upgrade_creates_the_eleven_tables(migrated_scratch):
    tables = set(inspect(migrated_scratch).get_table_names()) - {"alembic_version"}
    assert tables == TABLES


def test_models_match_migrations(migrated_scratch):
    with migrated_scratch.connect() as connection:
        context = MigrationContext.configure(
            connection, opts={"compare_type": True, "compare_server_default": True}
        )
        diff = compare_metadata(context, Base.metadata)
    assert diff == [], f"Models and migrations differ: {diff}"


def test_check_constraints_and_indexes_match_by_name(migrated_scratch):
    # Autogenerate does not compare CHECK constraints or partial-index predicates, so names are
    # compared here. The naming convention makes them deterministic.
    inspector = inspect(migrated_scratch)
    for table in Base.metadata.sorted_tables:
        model_checks = {
            c.name for c in table.constraints if c.__class__.__name__ == "CheckConstraint"
        }
        db_checks = {c["name"] for c in inspector.get_check_constraints(table.name)}
        assert model_checks == db_checks, table.name

        # (name, unique, partial). Postgres rewrites predicates, so only their presence is compared.
        model_indexes = {
            (i.name, i.unique, i.dialect_options["postgresql"]["where"] is not None)
            for i in table.indexes
        }
        db_indexes = {
            (i["name"], i["unique"], "postgresql_where" in i.get("dialect_options", {}))
            for i in inspector.get_indexes(table.name)
            if not i.get("duplicates_constraint")
        }
        assert model_indexes == db_indexes, table.name


def test_enum_values_match(migrated_scratch):
    with migrated_scratch.connect() as connection:
        for enum_type in ALL_ENUM_TYPES:
            db_values = connection.execute(
                text(
                    "SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid "
                    "WHERE t.typname = :name ORDER BY e.enumsortorder"
                ),
                {"name": enum_type.name},
            ).scalars().all()
            assert db_values == list(enum_type.enums), enum_type.name


def test_every_foreign_key_restricts_deletes(migrated_scratch):
    inspector = inspect(migrated_scratch)
    for table in TABLES:
        for foreign_key in inspector.get_foreign_keys(table):
            ondelete = (foreign_key.get("options") or {}).get("ondelete")
            assert ondelete == "RESTRICT", f"{table}.{foreign_key['name']}: {ondelete}"
