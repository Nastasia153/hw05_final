import datetime as dt


def year(request):
    now = dt.datetime.now()
    return {
        'year': now.year
    }
