from babel.numbers import format_currency

def php(amount):
    return format_currency(amount, 'PHP', locale='en_PH')