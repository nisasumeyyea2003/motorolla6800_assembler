
import pytest  # noqa: F401
from axel.symbol import U_Int8, Int8, U_Int16, Symbol_Table


def test_uint8() -> None:
    uint8 = U_Int8(0)
    uint8_2 = U_Int8(255)
    assert uint8 + 5 == 5
    assert uint8 - 5 == 255 - 5 + 1
    assert uint8_2 + 1 == 0
    assert uint8_2 - 5 == 255 - 5
    uint8 += 1
    assert uint8.num == 1
    uint8 -= 2
    assert uint8.num == 255
    assert uint8.raw == -1
    uint8_2 = U_Int8(255)
    uint8_2 += 2
    assert uint8_2.raw == 257


def test_int8() -> None:
    int8 = Int8(-128)
    int8_2 = Int8(127)
    assert int8 + 5 == 5
    assert int8 - 5 == -5
    assert int8_2 + 1 == 0
    assert int8_2 - 5 == 127 - 5
    int8 += 1
    assert int8.num == 1
    int8 -= 2
    assert int8.num == -1


def test_uint16() -> None:
    uint16 = U_Int16(0)
    uint16_2 = U_Int16(65535)
    assert uint16 + 5 == 5
    assert uint16 - 5 == 65535 - 5 + 1
    assert uint16_2 + 1 == 0
    assert uint16_2 - 5 == 65535 - 5
    uint16 += 1
    assert uint16.num == 1


def test_symbol_table_set() -> None:
    test = Symbol_Table()
    test.set('test', U_Int16(255), 'variable', 'testing')
    assert 'test' in test.table
    assert test.table['test'][0].num == 255
    assert test.table['test'][1] == 'variable'
    assert test.table['test'][2] == 'testing'


def test_symbol_table_get() -> None:
    test = Symbol_Table()
    test.table['test'] = (U_Int16(255), 'variable', 'testing')
    assert test.get('test')[0].num == 255
    assert test.get('test')[1] == 'variable'
    assert test.get('test')[2] == 'testing'
