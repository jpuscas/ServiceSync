import pytest
from features.services.standard_datetime import format_service_datetime, normalize_time, normalize_date

def test_normalize_time():
    assert normalize_time('9:30 AM') == '09:30'
    assert normalize_time('9:30PM') == '21:30'
    assert normalize_time('21:30') == '21:30'

def test_normalize_date():
    assert normalize_date('03-08-2026') == '2026-03-08'
    assert normalize_date('3/8/2026') == '2026-03-08'
    assert normalize_date('2026-03-08') == '2026-03-08'

def test_normalize_date_invalid():
    with pytest.raises(ValueError):
        normalize_date('2026/03/08')

def test_format_service_datetime(): #still need to test
    assert format_service_datetime('2026-03-08', '09:30') == '3/8/26, 9:30 AM'