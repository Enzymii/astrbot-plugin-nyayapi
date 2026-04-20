from __future__ import annotations

from pathlib import Path

from peewee import CharField, Check, DateField, IntegerField, Model, SqliteDatabase

_db = SqliteDatabase(None)
_db_file: Path | None = None


class BaseModel(Model):
    class Meta:
        database = _db


class Jrrp(BaseModel):
    platform = CharField()
    source_id = CharField()
    group_id = CharField(default="")
    user_id = CharField()
    date = DateField()
    value = IntegerField(constraints=[Check("value >= 1 AND value <= 100")])

    class Meta(BaseModel.Meta):
        table_name = "jrrp"
        indexes = ((("platform", "source_id", "user_id", "date"), True),)


def init_db(data_path: Path) -> None:
    global _db_file

    data_path.mkdir(parents=True, exist_ok=True)
    db_file = data_path / "jrrp.db"

    if _db_file != db_file:
        if not _db.is_closed():
            _db.close()
        _db.init(str(db_file))
        _db_file = db_file

    if _db.is_closed():
        _db.connect(reuse_if_open=True)

    _db.create_tables([Jrrp], safe=True)
