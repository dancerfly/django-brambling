from localflavor.us.forms import USZipCodeField
from localflavor.gb.forms import GBPostcodeField


def clean_postal_code(country, code):
    if country == 'GB':
        field = GBPostcodeField()
    elif country == 'US':
        field = USZipCodeField()
    else:
        return code
    return field.clean(code)
