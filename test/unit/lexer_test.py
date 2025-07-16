
import pytest
from os import linesep
from typing import List, Callable
from axel.tokens import Token as Token, Mnemonic, Register
from axel.lexer import Lexer

f1_t = Callable[[str], Lexer]
f2_t = List[str]


@pytest.fixture  # type: ignore
def lexer() -> Callable[[str], Lexer]:

    def _make_lexer(source: str) -> Lexer:
        return Lexer(source)

    return _make_lexer


@pytest.fixture  # type: ignore
def whitespace() -> List[str]:
    return [
        '''  SAME	LDA B DIGADD	; FIX DISPLAY ADDRESS
            ADD B #$10
        ''',
        '      LDA B DIGADD',
        '''; This is a comment\nADD B #$10
        ''',
        '''LDA B DIGADD ; This is a comment \nADD B #$10''']


def test_skip_whitespace_comments(lexer: f1_t, whitespace: f2_t) -> None:
    test = lexer(whitespace[0])
    test._skip_whitespace_and_comments()
    assert test.pointer == 'S'
    test = lexer(whitespace[1])
    test._skip_whitespace_and_comments()
    assert test.pointer == 'L'
    test = lexer(whitespace[2])
    test._skip_whitespace_and_comments()
    test._pointer += len(linesep)  # halt at newline
    assert test.pointer == 'A'


def test_read_term(lexer: f1_t) -> None:
    test = lexer(' ADD  B   #$10  ')
    term1 = test._read_term()
    term2 = test._read_term()
    term3 = test._read_term()

    assert term1 == 'ADD'
    assert term2 == 'B'
    assert term3 == '#$10'


def test_get_token(lexer: f1_t) -> None:
    test = lexer('ADD B #$10')
    assert test._get_token("ADD") == Mnemonic.T_ADD
    assert test._get_token("B") == Register.T_B
    assert test._get_token('#$10') == Token.T_IMM_UINT8


def test_retract(lexer: f1_t) -> None:
    test = lexer('ADD B ##10')
    test._pointer = 4
    test._at = 3
    test.retract()
    assert test._pointer == test._at


def test_inc(lexer: f1_t) -> None:
    test = lexer('ADD B #$10')
    test._pointer = 3
    test._inc()
    assert test._pointer == 4


def test_dec(lexer: f1_t) -> None:
    test = lexer('ADD B #$10')
    test._pointer = 3
    test._dec()
    assert test._pointer == 2


def test_reset(lexer: f1_t) -> None:
    test = lexer('ADD B #$10')
    default = {
        'token': Token.T_UNKNOWN,
        'data': None
    }
    test.yylex = {
        'token': Token.T_LABEL,
        'data': 'TEST'
    }
    test._reset()
    assert test.yylex['token'] == list(default.values())[0]
    assert test.yylex['data'] == list(default.values())[1]


def test_set_token(lexer: f1_t) -> None:
    test = lexer('ADD B #$10')
    test._set_token(Token.T_LABEL, 'TEST')
    result = {
        'token': Token.T_LABEL,
        'data': 'TEST'
    }
    assert test.yylex['token'] == list(result.values())[0]
    assert test.yylex['data'] == list(result.values())[1]
    assert test._last == Token.T_LABEL


def test_skip_to_next_line(lexer: f1_t, whitespace: f2_t) -> None:
    test = lexer(whitespace[3])
    test._skip_to_next_line()
    test._pointer += len(linesep)  # halt at newline
    assert test.pointer == 'A'


def test_peek_next(lexer: f1_t) -> None:
    test = lexer('ABA  #$10')
    test._pointer = 3
    peek = test._peek_next()
    assert peek == '#$10'


def test_variable_token(lexer: f1_t) -> None:
    test = lexer('OUT = $F0')
    test._pointer = 3
    assert test._variable_token('OUT') is Token.T_VARIABLE
    test._pointer = 5
    assert test._variable_token('OUT') is None


def test_comma_token(lexer: f1_t) -> None:
    test = lexer('LDAA $10,X')
    test._pointer = 8
    assert test._comma_token(',') is Token.T_COMMA
    test._pointer = 0
    assert test._comma_token(',') is None


def test_label_token(lexer: f1_t) -> None:
    test = lexer('TEST ABA #$10')
    test._pointer = 4
    assert test._label_token('TEST') is Token.T_LABEL
    test._pointer = 6
    assert test._variable_token('TEST') is None


def test_equal_token(lexer: f1_t) -> None:
    test = lexer('OUT = $F0')
    assert test._equal_token('=') is Token.T_EQUAL
    assert test._equal_token('ABA') is None


def test_immediate_token(lexer: f1_t) -> None:
    test = lexer('LDA A #$01')
    test._pointer = 7
    # assert immediate uint8
    assert test._immediate_token('#$01') is Token.T_IMM_UINT8
    test = lexer('LDX #$2F00')
    test._pointer = 5
    # assert immediate uint16
    assert test._immediate_token('#$2F00') is Token.T_IMM_UINT16
    assert test._immediate_token('LDA') is None


def test_direct_or_extended_token(lexer: f1_t) -> None:
    test = lexer('DIGADD = $F0')
    test._pointer = 10
    # assert direct uint8
    assert test._direct_or_extended_token('$F0') is Token.T_DIR_ADDR_UINT8
    test = lexer('OUTCH	= $FE3A')
    test._pointer = 9
    # assert direct extended uint16
    assert test._direct_or_extended_token('$FE3A') is Token.T_EXT_ADDR_UINT16
    assert test._direct_or_extended_token('DIGADD') is None


def test_displacement_token(lexer: f1_t) -> None:
    test = lexer('BNE WAIT\nTAB')
    test._last = Mnemonic.T_BNE
    test._pointer = 4
    assert test._displacement_token('WAIT') is Token.T_DISP_ADDR_INT8
    assert test._displacement_token('LDA') is None


def test_mnemonic_token(lexer: f1_t) -> None:
    test = lexer('ASL A')
    test._pointer = 0
    assert test._mnemonic_token('ASL') is Mnemonic.T_ASL
    # some mnemonics may have their immediate register contiguously
    test = lexer('LDAA #$01')
    test._pointer = 4
    assert test._mnemonic_token('LDAA') is Mnemonic.T_LDA
    assert test._pointer == 3


def test_register_token(lexer: f1_t) -> None:
    test = lexer('LDAA $10,X')
    test._pointer = 3
    assert test._register_token('A') is Register.T_A
    test._pointer = 8
    assert test._register_token('X') is Register.T_X
    test = lexer('ADD B #$10')
    test._pointer = 4
    assert test._register_token('B') is Register.T_B
