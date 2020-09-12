from enum import unique, Enum

from sqlalchemy import (
    MetaData, Column, Table, Integer,
    String, Date, Enum as PgEnum, ForeignKey, ForeignKeyConstraint
)

convention = {
    'all_column_names': lambda constraint, table: '_'.join([
        column.name for column in constraint.columns.values()
    ]),

    # Именование индексов
    'ix': 'ix__%(table_name)s__%(all_column_names)s',

    # Именование уникальных индексов
    'uq': 'uq__%(table_name)s__%(all_column_names)s',

    # Именование CHECK-constraint-ов
    'ck': 'ck__%(table_name)s__%(constraint_name)s',

    # Именование внешних ключей
    'fk': 'fk__%(table_name)s__%(all_column_names)s__%(referred_table_name)s',

    # Именование первичных ключей
    'pk': 'pk__%(table_name)s'
}

metadata = MetaData(naming_convention=convention)


@unique
class Gender(Enum):
    male = 'male'
    female = 'female'


imports_table = Table(
    'imports',
    metadata,
    Column('import_id', Integer, primary_key=True)
)

citizens_table = Table(
    'citizens',
    metadata,
    Column('import_id', Integer, ForeignKey('imports.import_id'), primary_key=True),
    Column('citizen_id', Integer, primary_key=True),
    Column('name', String, nullable=False),
    Column('birth_date', Date, nullable=False),
    Column('town', String, nullable=False, index=True),
    Column('street', String, nullable=False),
    Column('building', String, nullable=False),
    Column('apartment', Integer, nullable=False),
    Column('gender', PgEnum(Gender, name='gender'), nullable=False)
)

relations_table = Table(
    'relations',
    metadata,
    Column('import_id', Integer, primary_key=True),
    Column('citizen_id', Integer, primary_key=True),
    Column('relative_id', Integer, primary_key=True),
    ForeignKeyConstraint(
        ('import_id', 'citizen_id'),
        ('citizens.import_id', 'citizens.citizen_id')
    ),
    ForeignKeyConstraint(
        ('import_id', 'relative_id'),
        ('citizens.import_id', 'citizens.citizen_id')
    )
)
