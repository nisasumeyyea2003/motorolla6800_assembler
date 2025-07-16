# Gerekli test ve yardımcı kütüphaneleri import ediliyor
import pytest          # Python test framework'ü
import pathlib         # Dosya yolu işlemleri için
from typing import Callable    # Type hinting için - fonksiyon tipi tanımı
from collections import deque  # Çift uçlu kuyruk veri yapısı
from axel.symbol import Symbol_Table     # Sembol tablosu sınıfı
from axel.tokens import Token, Mnemonic, Register  # Token, mnemonic ve register tanımları
from axel.lexer import Lexer            # Lexical analyzer (sözcüksel çözümleyici)
from axel.parser import Parser, AssemblerParserError  # Parser ve hata sınıfı

# Callable type alias tanımı - string alıp Symbol_Table dönen fonksiyon tipi
f1_t = Callable[[str], Symbol_Table]

@pytest.fixture  # type: ignore
def symbol_table() -> Callable[[str], Symbol_Table]:
    """
    Pytest fixture - test fonksiyonlarında kullanılmak üzere sembol tablosu üreten fonksiyon
    Bu fixture, verilen kaynak koddan sembol tablosu çıkartan bir closure döner
    """
    def _get_symbols(source: str) -> Symbol_Table:
        """
        İç fonksiyon: Kaynak kodu alır, lexer ile tokenize eder ve sembol tablosunu döner
        
        Args:
            source: Assembly kaynak kodu string'i
            
        Returns:
            Symbol_Table: Lexer tarafından oluşturulan sembol tablosu
        """
        scanner = Lexer(source)     # Kaynak kodu için lexer oluştur
        for token in scanner:       # Tüm tokenları tara (sembol tablosunu doldur)
            pass                    # Token'ları işlemek yerine sadece tara
        return scanner.symbols      # Lexer'ın oluşturduğu sembol tablosunu döner
    
    return _get_symbols  # Closure döner

# Beklenen test sonuçları - assembly instruction'ların token sırası
expected = deque([
    # Her tuple bir instruction'ı temsil eder: (mnemonic, operand1, operand2, ...)
    (Mnemonic.T_JSR, Token.T_EXT_ADDR_UINT16),        # JSR external_address
    (Mnemonic.T_LDA, Register.T_A, Token.T_IMM_UINT8), # LDA A, #immediate_value
    (Mnemonic.T_BRA, Token.T_DISP_ADDR_INT8),         # BRA displacement_address
    (Mnemonic.T_LDA, Register.T_B, Token.T_DIR_ADDR_UINT8) # LDA B, direct_address
])

def test_assembly_parser_error(symbol_table: f1_t) -> None:
    """
    Parser'ın hata durumlarını test eder
    
    Args:
        symbol_table: Sembol tablosu üreten fixture fonksiyonu
    """
    # Test 1: Bilinmeyen/geçersiz token testi
    # "FAIL" geçersiz bir mnemonic, parser bunu tanıyamayacak
    test = Parser('FAIL\nADD B #$10\n', symbol_table('FAIL\nADD B #$10\n'))
    with pytest.raises(AssemblerParserError):  # AssemblerParserError beklendiğini belirt
        test.take(Mnemonic.T_ADD)  # ADD mnemonic'ini beklediğini söyle, ama FAIL var

    # Test 2: Beklenmeyen token testi  
    # Geçerli kod ama yanlış token beklentisi
    test = Parser('ADD B #$10\n', symbol_table('ADD B #$10\n'))
    with pytest.raises(AssemblerParserError):  # AssemblerParserError beklendiğini belirt
        test.take(Token.T_VARIABLE)  # Variable token bekle, ama ADD mnemonic var

def test_assembly_parser(symbol_table: f1_t) -> None:
    """
    Parser'ın normal çalışma durumunu test eder
    
    Args:
        symbol_table: Sembol tablosu üreten fixture fonksiyonu
    """
    # Test dosyasını aç ve oku
    # __file__'ın parent'ının parent'ı/etc/fixture.asm dosyasını aç
    with open(f'{pathlib.Path(__file__).parent.parent}/etc/fixture.asm') as f:
        source = f.read()  # Dosya içeriğini oku
        
        # Parser'ı kaynak kod ve sembol tablosu ile başlat
        test = Parser(source, symbol_table(source))
        
        # İlk 3 satırın variable tanımları olduğunu test et
        assert test.line() is True  # 1. variable tanımı
        assert test.line() is True  # 2. variable tanımı  
        assert test.line() is True  # 3. variable tanımı
        
        # Boş satırları geç, sonraki instruction satırını al
        line = test.line()
        
        # line'ın boolean olmadığından emin ol (instruction olmalı)
        if isinstance(line, bool):
            raise AssertionError('failed test')  # Test başarısız
        
        # Her instruction'ı expected deque ile karşılaştır
        while line is not False:  # Dosya sonu gelene kadar
            expect = expected.popleft()  # Beklenen sonucu al
            instruction, operands = line  # type: ignore  # Instruction'ı ayrıştır
            
            # Instruction mnemonic'ini kontrol et
            assert instruction == expect[0]  # type: ignore
            
            # Operandları ters çevir (parser'ın döndürdüğü sırayı düzelt)
            operands.reverse()
            
            # Her operandı expected ile karşılaştır
            index = 1  # expect[0] mnemonic, operandlar 1'den başlar
            for ops in operands:
                assert ops['token'] == expect[index]  # type: ignore  # Token tipini kontrol et
                index += 1  # Sonraki operanda geç
            
            line = test.line()  # Sonraki satırı al