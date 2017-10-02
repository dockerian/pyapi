"""
# db module - database adapter functions
"""


from sqlalchemy import DateTime, TypeDecorator


# pylint: disable=abstract-method
class DateTimeUtc(TypeDecorator):
    '''
    Results returned as offset-aware datetimes.
    '''
    impl = DateTime

    # pylint: disable=unused-argument
    def process_result_value(self, value, dialect):
        """
        set UTC time zone with processing value
        """
        return value.replace(tzinfo=pytz.utc)
