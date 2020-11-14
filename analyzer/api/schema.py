from datetime import date

from marshmallow import Schema, validates_schema, validates
from marshmallow.fields import Int, Str, Date, Nested, List, Float
from marshmallow.validate import Range, Length, OneOf, ValidationError

from analyzer.db.schema import Gender
from analyzer.utils.consts import DATE_FORMAT

POSITIVE_VALUE = Range(min=0)
BASIC_STRING_LENGTH = Length(min=1, max=256)


class CitizenSchema(Schema):
    citizen_id = Int(validate=POSITIVE_VALUE, required=True)
    name = Str(validate=BASIC_STRING_LENGTH, required=True)
    gender = Str(validate=OneOf([gender.name for gender in Gender]), required=True)
    birth_date = Date(format=DATE_FORMAT, required=True)
    town = Str(validate=BASIC_STRING_LENGTH, required=True)
    street = Str(validate=BASIC_STRING_LENGTH, required=True)
    building = Str(validate=BASIC_STRING_LENGTH, required=True)
    apartment = Int(validate=POSITIVE_VALUE, required=True)
    relatives = List(Int(validate=POSITIVE_VALUE), required=True)


class PatchCitizenRequestSchema(Schema):
    name = Str(validate=BASIC_STRING_LENGTH)
    gender = Str(validate=OneOf([gender.name for gender in Gender]))
    birth_date = Date(format=DATE_FORMAT)
    town = Str(validate=BASIC_STRING_LENGTH)
    street = Str(validate=BASIC_STRING_LENGTH)
    building = Str(validate=BASIC_STRING_LENGTH)
    apartment = Int(validate=POSITIVE_VALUE)
    relatives = List(Int(validate=POSITIVE_VALUE))

    @validates('birth_date')
    def validate_birth_date(self, value: date) -> None:
        """
        Валидация на то, что дата рождения не может быть датой из будущего.

        :param value: дата для валидации
        """
        if value > date.today():
            raise ValidationError('Birth date can not be in future')

    @validates('relatives')
    def validate_relatives_unique(self, value: list) -> None:
        """
        Валидация на уникальной id-шников родственников.

        :param value: список id-шников родственников
        """
        if len(value) != len(set(value)):
            raise ValidationError('Relatives must be unique')


class ImportRequestSchema(Schema):
    citizens = Nested(CitizenSchema, many=True, required=True, validate=Length(max=1000))

    @validates_schema
    def validate_unique_citizen_id(self, data: dict, **_) -> None:
        """
        Валидация на уникальность id-шников жителей в рамках выгрузки.

        :param data: данные схемы
        """
        unique_ids = set()
        for citizen in data['citizens']:
            if citizen['citizen_id'] in unique_ids:
                raise ValidationError(
                    'citizen_id {0!r} is not unique'.format(citizen['citizen_id'])
                )

            unique_ids.add(citizen['citizen_id'])

    @validates_schema
    def validate_relatives(self, data: dict, **_) -> None:
        """
        Валидация родственников.

        Если у родственника #1 есть родственник #2,
        то и родственника #2 должен быть родственник #1.

        :param data: данные схемы
        """
        relatives_map = {
            citizen['citizen_id']: set(citizen['relatives'])
            for citizen in data['citizens']
        }

        for citizen_id, relatives in relatives_map.items():
            for relative_id in relatives:
                if citizen_id not in relatives_map.get(relative_id, set()):
                    raise ValidationError(
                        'citizen_id {0!r} does not have relation with {1!r}'.format(
                            relative_id, citizen_id
                        )
                    )


class ImportIdSchema(Schema):
    import_id = Int(required=True)


class ImportResponseSchema(Schema):
    data = Nested(ImportIdSchema, required=True)


class CitizenListResponseSchema(Schema):
    data = Nested(CitizenSchema, many=True, required=True)


class PatchCitizenResponseSchema(Schema):
    data = Nested(CitizenSchema, required=True)


class PresentsSchema(Schema):
    citizen_id = Int(validate=Range(min=0), required=True)
    presents = Int(validate=Range(min=0), required=True)


CitizenPresentsByMonthSchema = type(
    'CitizenPresentsByMonthSchema', (Schema,),
    {
        str(i): Nested(PresentsSchema, many=True, required=True)
        for i in range(1, 13)
    }
)


class CitizenPresentsResponseSchema(Schema):
    data = Nested(CitizenPresentsByMonthSchema, required=True)


class TownAgeStatSchema(Schema):
    town = Str(validate=BASIC_STRING_LENGTH, required=True)
    p50 = Float(validate=POSITIVE_VALUE, required=True)
    p75 = Float(validate=POSITIVE_VALUE, required=True)
    p99 = Float(validate=POSITIVE_VALUE, required=True)


class TownAgeStatResponseSchema(Schema):
    data = Nested(TownAgeStatSchema, many=True, required=True)
