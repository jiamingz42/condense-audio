from trim_movie.timestamp import Timestamp

def test_add():
    assert Timestamp.from_s(
        "00:01:00.000") + Timestamp.from_s("00:00:30.000") == Timestamp.from_s("00:01:30.000")

def test_minus():
    assert Timestamp.from_s(
        "00:01:00.000") - Timestamp.from_s("00:00:30.000") == Timestamp.from_s("00:00:30.000")

def test_from_s():
    assert Timestamp.from_s("00:04:28.351").total_milliseconds == 4 * 60000 + 28000 + 351
