import datetime
import calendar

import click

from aww.obsidian import Level


def whole_year(the_date: datetime.date) -> list[datetime.date]:
    year = the_date.year
    start_date = datetime.date(year, 1, 1)
    end_date = datetime.date(year, 12, 31)
    dates = [
        start_date + datetime.timedelta(days=i)
        for i in range((end_date - start_date).days + 1)
    ]
    return dates


def whole_month(the_date: datetime.date) -> list[datetime.date]:
    year = the_date.year
    month = the_date.month
    num_days = calendar.monthrange(year, month)[1]
    dates = [datetime.date(year, month, day) for day in range(1, num_days + 1)]
    return dates


def whole_week(the_date: datetime.date) -> list[datetime.date]:
    """Returns the weekly dates (Mon to Friday) for the week that contains the given date."""
    monday = the_date - datetime.timedelta(days=the_date.weekday())
    return [monday + datetime.timedelta(days=i) for i in range(7)]


def get_dates_for_level(
    level: Level, date: datetime.datetime, yesterday: bool
) -> list[datetime.date]:
    """Calculates the list of dates for a given level, date, and yesterday flag."""
    the_date = date.date()
    if yesterday:
        if level != Level.daily:
            raise click.ClickException("--yesterday can only be used with daily level")
        the_date = the_date - datetime.timedelta(days=1)

    match level:
        case Level.daily:
            return [the_date]
        case Level.weekly:
            return whole_week(the_date)
        case Level.monthly:
            return whole_month(the_date)
        case Level.yearly:
            return whole_year(the_date)
        case _:
            # Should not happen with click.Choice
            raise click.ClickException(f"Unknown level '{level}'")
