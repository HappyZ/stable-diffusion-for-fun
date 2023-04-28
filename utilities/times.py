import calendar
import time


def get_epoch_now() -> int:
    '''
    Gets current elapsed epoch since 1970-1-1, 00:00 UTC.
    The returned epoch is timezone-independent.
    '''
    return int(time.time())


def epoch_to_time(epoch: int, localTime: bool = False) -> time.struct_time:
    '''
    Converts epoch to the time struct.
    @param localTime sets to return local time zone considered time.
    '''
    return time.localtime(epoch) if localTime else time.gmtime(epoch)


def epoch_to_string(epoch: int, localTime: bool = False, customFormat: str = "%Y-%m-%dT%H:%M:%S") -> str:
    '''
    Converts epoch to the string in the form of something like "2019-01-11T10:30:00".
    @param localTime sets to return local time zone considered string.
    '''
    return time.strftime(customFormat, epoch_to_time(epoch, localTime=localTime))


def epoch_to_date(epoch: int, localTime: bool = False) -> str:
    '''
    Converts epoch to the date of the epoch.
    @param localTime sets to return local time zone considered date.
    '''
    return time.strftime('%Y-%m-%d', epoch_to_time(epoch, localTime=localTime))


def epoch_to_yearmonth(epoch: int, localTime: bool = False) -> str:
    '''
    Converts epoch to the year-month of the epoch.
    @param localTime sets to return local time zone considered date.
    '''
    return time.strftime('%Y-%m', epoch_to_time(epoch, localTime=localTime))


def string_to_epoch(timeString: str, localTime: bool = False, dashOnly: bool = False) -> int:
    '''
    Converts time string from something like "2019-01-11T10:30:00" to the epoch.
    @param localTime sets to return local time zone considered epoch.
    '''
    if 'Z' == timeString[-1]:
        timeString = timeString[:-1]
        localTime = False
    if dashOnly:
        t = time.strptime(timeString, '%Y-%m-%dT%H-%M-%S')
    else:
        t = time.strptime(timeString, '%Y-%m-%dT%H:%M:%S')
    offset = 0
    if localTime:
        currentT = get_epoch_now()
        offset = int(calendar.timegm(epoch_to_time(currentT)) -
                     calendar.timegm(epoch_to_time(currentT, localTime=True)))
    return int(calendar.timegm(t)) + offset


def date_to_epoch(timeString: str, localTime: bool = False) -> int:
    '''
    Converts date string from something like "2019-01-11" to the epoch.
    @param localTime sets to return local time zone considered epoch.
    '''
    return string_to_epoch('{}T0:0:0'.format(timeString), localTime=localTime)


def time_to_epoch(t, localTime: bool = False) -> int:
    '''
    Converts epoch to the time struct.
    @param localTime sets to return local time zone considered time.
    '''
    offset = 0
    if localTime:
        currentT = get_epoch_now()
        offset = int(calendar.timegm(epoch_to_time(currentT)) -
                     calendar.timegm(epoch_to_time(currentT, localTime=True)))
    return int(calendar.timegm(t)) + offset


def wait_for_seconds(wait_sec: int):
    time.sleep(wait_sec)


def is_epoch_weekend(epoch: int, localTime: bool = False) -> bool:
    '''
    Checks if given epoch is during a weekend (Sat/Sun).
    @param localTime sets to return local time zone considered time.
    '''
    return epoch_to_time(epoch, localTime=localTime).tm_wday >= 5


class Timer():
    def __init__(self):
        self.__start_time = None
        self.__stop_time = None

    def start(self):
        self.__start_time = get_epoch_now()
    
    def stop(self):
        if self.__start_time is None:
            raise ValueError("start() must be called first")
        self.__stop_time = get_epoch_now()
    
    def elapsed_seconds(self) -> int:
        if self.__stop_time is None:
            return get_epoch_now() - self.__start_time
        return self.__stop_time - self.__start_time

    def remaining_seconds_estimation(self, current_progress: float) -> int:
        return int(self.elapsed_seconds() / current_progress)
