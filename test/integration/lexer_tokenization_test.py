
# Gerekli test ve utility kütüphanelerini içe aktarım
import pytest  # Test framework'ü
import pathlib  # Dosya yolu işlemleri için
from typing import Callable  # Tip belirtimi için
from collections import deque  # Çift yönlü kuyruk veri yapısı

# Lexer ile ilgili sınıfları içe aktarım
from axel.tokens import Token, Mnemonic, Register  # Token türleri ve assembly komutları
from axel.lexer import Lexer  # Ana lexer sınıfı


@pytest.fixture  # type: ignore
def lexer() -> Callable[[str], Lexer]:
    """
    Pytest fixture - test fonksiyonlarında kullanılmak üzere lexer oluşturucu factory fonksiyonu
    Bu pattern, her test için temiz bir lexer instance'ı sağlar
    """
    def _make_lexer(source: str) -> Lexer:
        """
        Verilen kaynak koddan Lexer objesi oluşturur
        Args:
            source: Assembly kaynak kodu string'i
        Returns:
            Lexer: Yeni lexer instance'ı
        """
        return Lexer(source)
    
    return _make_lexer


# Beklenen token sırasını içeren deque (çift yönlü kuyruk)
# Bu, test dosyasından çıkarılması gereken token'ların doğru sırasını temsil eder
expected = deque([
    # Değişken tanımı: REDIS = $FFFF
    Token.T_VARIABLE,        # Değişken adı
    Token.T_EQUAL,           # Eşittir işareti
    Token.T_EXT_ADDR_UINT16, # 16-bit genişletilmiş adres
    Token.T_EOL,             # Satır sonu
    
    # Değişken tanımı: DIGADD = $00
    Token.T_VARIABLE,        # Değişken adı
    Token.T_EQUAL,           # Eşittir işareti
    Token.T_DIR_ADDR_UINT8,  # 8-bit doğrudan adres
    Token.T_EOL,             # Satır sonu
    
    # Değişken tanımı: OUTCH = $FFFF
    Token.T_VARIABLE,        # Değişken adı
    Token.T_EQUAL,           # Eşittir işareti
    Token.T_EXT_ADDR_UINT16, # 16-bit genişletilmiş adres
    Token.T_EOL,             # Satır sonu
    
    Token.T_EOL,             # Boş satır
    
    # Assembly kodunun başlangıcı
    Token.T_LABEL,           # Label (START:)
    Mnemonic.T_JSR,          # Jump to Subroutine komutu
    Token.T_EXT_ADDR_UINT16, # Hedef adres
    Token.T_EOL,             # Satır sonu
    
    # Load Accumulator komutu
    Mnemonic.T_LDA,          # Load Accumulator
    Register.T_A,            # A register'ı
    Token.T_IMM_UINT8,       # 8-bit immediate değer
    Token.T_EOL,             # Satır sonu
    
    # Branch Always komutu
    Mnemonic.T_BRA,          # Branch Always
    Token.T_DISP_ADDR_INT8,  # 8-bit signed displacement
    Token.T_EOL,             # Satır sonu
    
    # Başka bir label ve komut
    Token.T_LABEL,           # Label (SAME:)
    Mnemonic.T_LDA,          # Load Accumulator
    Register.T_B,            # B register'ı
    Token.T_DIR_ADDR_UINT8   # 8-bit doğrudan adres
])


# Beklenen sembol tablosundaki sembollerin listesi
# Bu semboller assembly kodunda tanımlanan değişken ve label'ları temsil eder
symbols = deque([
    'REDIS',   # $FFFF değerindeki değişken
    'DIGADD',  # $00 değerindeki değişken
    'OUTCH',   # $FFFF değerindeki değişken
    'START',   # Assembly kodunun başlangıç label'ı
    'SAME'     # İkinci label
])


def test_lexer_tokenization() -> None:
    """
    Lexer'ın tokenization (sözcük analizi) işlevini test eden ana test fonksiyonu
    
    Test şu işlemleri gerçekleştirir:
    1. fixture.asm dosyasını okur
    2. Lexer ile dosyayı analiz eder
    3. Üretilen token'ları beklenen token'larla karşılaştırır
    4. Sembol tablosunun doğru oluşturulduğunu kontrol eder
    """
    
    # Test dosyasının yolunu dinamik olarak oluştur
    # __file__ bu Python dosyasının yolu
    # parent.parent ile iki seviye yukarı çık
    # /etc/fixture.asm dosyasını aç
    with open(f'{pathlib.Path(__file__).parent.parent}/etc/fixture.asm') as f:
        # Dosya içeriğini okuyarak Lexer objesi oluştur
        test = Lexer(f.read())
        
        # Lexer iterator olarak çalışır, her iterasyonda bir token döner
        for token in test:
            # Üretilen token'ı beklenen token ile karşılaştır
            # popleft() ile deque'nin solundan eleman çıkar
            assert token is expected.popleft()
        
        # Tüm beklenen token'ların işlendiğini kontrol et
        assert len(expected) == 0
        
        # Sembol tablosu testi
        # Lexer'ın sembol tablosunda beklenen sayıda sembol olduğunu kontrol et
        assert len(test.symbols.table) == len(symbols)
        
        # Her beklenen sembolün sembol tablosunda bulunduğunu kontrol et
        while len(symbols):
            # pop() ile deque'nin sağından eleman çıkar ve sembol tablosunda ara
            assert symbols.pop() in test.symbols.table