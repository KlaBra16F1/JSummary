"""Some tests"""
from JSummary import get_input, check_date_time, adjust_json_type, RE_URL, RE_FILE

def test_get_url():
    """Testing regex detection."""
    assert get_input(RE_URL, "http://example.com/") == "http://example.com/"
    assert get_input(RE_URL, "www.example.com") is None
    assert get_input(RE_FILE, "test.json") == "test.json"
    assert get_input(RE_FILE, "./myfolder/my.json") == "./myfolder/my.json"
    assert get_input(RE_FILE, "..\\my.json") == "..\\my.json"
    assert get_input(RE_FILE, "test.txt") is None
    
def test_check_date_time():
    """Testing propper date, date-time detection"""
    assert check_date_time("2025-12-14") == "date"
    assert check_date_time("20/12/2026") == "date"
    assert check_date_time("1.1.26") == "date"
    assert check_date_time("2012-01-31T08:59Z") == "date-time"
    assert check_date_time("23:45") == "time"
    assert check_date_time("24. June 2025") == "string"


def test_adjust_json_type():
    """Testing type adjustment"""
    assert adjust_json_type("int") == "number"
    assert adjust_json_type("float") == "number"
    assert adjust_json_type("bool") == "boolean"
    assert adjust_json_type("NoneType") == "null"
