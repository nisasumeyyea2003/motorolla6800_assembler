
import pytest
from typing import Callable, Any
from typing import Iterator
from axel.symbol import U_Int8
from axel.assembler import Registers
from axel.tokens import AddressingMode
from axel.parser import Parser
from axel.opcode import Translate

f1_t = Callable[[], Any]
f2_t = Callable[[str], Parser]


@pytest.fixture(scope='module')  # type: ignore
def registers() -> Iterator[Any]:
    Registers.AccA = U_Int8(0)
    Registers.AccB = U_Int8(0)
    yield Registers


@pytest.fixture  # type: ignore
def parser() -> Callable[[str], Parser]:
    def _get_parser(source: str) -> Parser:
        parser = Parser(source)
        return parser

    return _get_parser


def test_opcode_aba(parser: f2_t, registers: f1_t) -> None:
    test = parser('ABA\n')
    line = test.line()
    if isinstance(line, bool):
        raise AssertionError('line is bool')
    instruction, operands = line
    r = registers()
    r.AccA = U_Int8(5)
    r.AccB = U_Int8(10)
    assert Translate.aba(AddressingMode.ACC, operands, r) == b'\x1b'
    assert r.AccA.num == 15


def test_opcode_adc(parser: f2_t, registers: f1_t) -> None:
    test = parser('ADC A #$10\n')
    line = test.line()
    if isinstance(line, bool):
        raise AssertionError('line is bool')
    instruction, operands = line
    r = registers()
    r.AccA = U_Int8(255)
    assert Translate.adc(AddressingMode.IMM, operands, r) == b'\x89\x10'
    # test carry
    assert Translate.adc(AddressingMode.IMM, operands, r) == b'\x890'
    test = parser('ADC B #$10\n')
    line = test.line()
    if isinstance(line, bool):
        raise AssertionError('line is bool')
    instruction, operands = line
    r = registers()
    r.AccB = U_Int8(0)
    assert Translate.adc(AddressingMode.IMM, operands, r) == b'\xC9\x10'
