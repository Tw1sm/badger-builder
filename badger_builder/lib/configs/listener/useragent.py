from enum import Enum

UA_CHROME  = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36' # noqa
UA_FIREFOX = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0' # noqa
UA_EDGE    = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36 Edg/110.0.1587.69' # noqa
UA_IE      = 'Mozilla/5.0 (Windows NT 10.0; Trident/7.0; rv:11.0) like Gecko'

class UserAgent(Enum):
    CHROME  = 'Chrome'
    FIREFOX = 'Firefox'
    EDGE    = 'Edge'
    IE      = 'IE'


def get_ua_string(ua: UserAgent):
    match ua:
        case UserAgent.CHROME:
            return UA_CHROME
        case UserAgent.FIREFOX:
            return UA_FIREFOX
        case UserAgent.EDGE:
            return UA_EDGE
        case UserAgent.IE:
            return UA_IE
