"""Initial

Revision ID: fc0f7c9159d3
Revises: 
Create Date: 2020-09-13 00:29:09.678438

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "fc0f7c9159d3"
down_revision = None
branch_labels = None
depends_on = None

GenderType = sa.Enum("male", "female", name="gender")


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "imports",
        sa.Column("import_id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("import_id", name=op.f("pk__imports")),
    )
    op.create_table(
        "citizens",
        sa.Column("import_id", sa.Integer(), nullable=False),
        sa.Column("citizen_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("town", sa.String(), nullable=False),
        sa.Column("street", sa.String(), nullable=False),
        sa.Column("building", sa.String(), nullable=False),
        sa.Column("apartment", sa.Integer(), nullable=False),
        sa.Column("gender", sa.Enum("male", "female", name="gender"), nullable=False),
        sa.ForeignKeyConstraint(
            ["import_id"],
            ["imports.import_id"],
            name=op.f("fk__citizens__import_id__imports"),
        ),
        sa.PrimaryKeyConstraint("import_id", "citizen_id", name=op.f("pk__citizens")),
    )
    op.create_index(op.f("ix__citizens__town"), "citizens", ["town"], unique=False)
    op.create_table(
        "relations",
        sa.Column("import_id", sa.Integer(), nullable=False),
        sa.Column("citizen_id", sa.Integer(), nullable=False),
        sa.Column("relative_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["import_id", "citizen_id"],
            ["citizens.import_id", "citizens.citizen_id"],
            name=op.f("fk__relations__import_id_citizen_id__citizens"),
        ),
        sa.ForeignKeyConstraint(
            ["import_id", "relative_id"],
            ["citizens.import_id", "citizens.citizen_id"],
            name=op.f("fk__relations__import_id_relative_id__citizens"),
        ),
        sa.PrimaryKeyConstraint("import_id", "citizen_id", "relative_id", name=op.f("pk__relations")),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("relations")
    op.drop_table("citizens")
    op.drop_table("imports")
    GenderType.drop(op.get_bind())
    # ### end Alembic commands ###
