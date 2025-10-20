from dnora_destine.polytope_functions import get_destine_steps


def test_trivial():
    start_time = "2025-10-10 00:00"
    end_time = "2025-10-10 00:00"
    date_str, steps = get_destine_steps(start_time, end_time)
    assert date_str == "20251010"
    assert steps == [0]


def test_one_hour():
    start_time = "2025-10-10 00:00"
    end_time = "2025-10-10 01:00"
    date_str, steps = get_destine_steps(start_time, end_time)
    assert date_str == "20251010"
    assert steps == [0, 1]


def test_24h():
    start_time = "2025-10-10 00:00"
    end_time = "2025-10-11 00:00"
    date_str, steps = get_destine_steps(start_time, end_time)
    assert date_str == "20251010"
    assert steps == list(range(25))
    assert steps == [
        0,
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
    ]


def test_96h():
    start_time = "2025-10-10 00:00"
    end_time = "2025-10-14 00:00"
    date_str, steps = get_destine_steps(start_time, end_time)
    assert date_str == "20251010"
    assert steps == list(range(97))


def test_start_not_00():
    start_time = "2025-10-10 03:00"
    end_time = "2025-10-11 05:00"
    date_str, steps = get_destine_steps(start_time, end_time)
    assert date_str == "20251010"
    assert steps == list(range(3, 30))
