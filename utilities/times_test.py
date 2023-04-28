import unittest

from utilities.times import date_to_epoch
from utilities.times import epoch_to_time
from utilities.times import epoch_to_string
from utilities.times import epoch_to_date
from utilities.times import get_epoch_now
from utilities.times import string_to_epoch
from utilities.times import time_to_epoch
from utilities.times import Timer
from utilities.times import wait_for_seconds


class TestTimes(unittest.TestCase):

    def test_epoch_translation(self):
        current_epoch = get_epoch_now()
        current_time = epoch_to_time(current_epoch, localTime=False)
        epoch_from_time = time_to_epoch(current_time, localTime=False)
        self.assertEqual(epoch_from_time, current_epoch)

        current_local_time = epoch_to_time(current_epoch, localTime=True)
        epoch_from_local_time = time_to_epoch(
            current_local_time, localTime=True)
        self.assertEqual(epoch_from_local_time, current_epoch)

        current_date = epoch_to_date(current_epoch, localTime=False)
        epoch_from_date = date_to_epoch(current_date, localTime=False)
        self.assertEqual(epoch_from_date // 86400, current_epoch // 86400)

        current_local_date = epoch_to_date(current_epoch, localTime=True)
        epoch_from_date_local = date_to_epoch(
            current_local_date, localTime=True)
        self.assertEqual(epoch_from_date_local //
                         86400, current_epoch // 86400)

        current_time_string = epoch_to_string(current_epoch, localTime=False)
        epoch_from_string = string_to_epoch(
            current_time_string, localTime=False)
        self.assertEqual(epoch_from_string, current_epoch)

        current_local_time_string = epoch_to_string(
            current_epoch, localTime=True)
        epoch_from_string_local = string_to_epoch(
            current_local_time_string, localTime=True)
        self.assertEqual(epoch_from_string_local, current_epoch)
    
    def test_timer(self):
        t = Timer()
        self.assertRaises(ValueError, t.stop)
        t.start()
        wait_for_seconds(2)
        self.assertEqual(t.elapsed_seconds(), 2)
        wait_for_seconds(3)
        t.stop()
        self.assertEqual(t.elapsed_seconds(), 5)
        self.assertEqual(t.remaining_seconds_estimation(0.5), 10)


if __name__ == '__main__':
    unittest.main()
