# Gerekli modülleri import ediyoruz
from io import BytesIO                              # Binary veri işleme için
from collections import deque                       # Stack veri yapısı için
from typing import Deque, Union, Optional           # Type hinting için
from axel.symbol import Symbol_Table, U_Int8, U_Int16  # Sembol tablosu ve veri tipleri
from axel.lexer import Lexer                        # Lexical analyzer
from axel.parser import Parser                      # Syntax analyzer
from bitarray import bitarray                       # Bit düzeyinde işlemler için

# Stack veri tipi tanımlaması - int veya string değerleri tutabilir
Stack_T = Deque[Union[int, str]]

class Registers:
    """
    6800 Mikroişlemcisinin register'larını temsil eden sınıf
    Her register, gerçek donanımdaki karşılığını simüle eder
    """
    
    # 8-bit Accumulator A register'ı - Aritmetik işlemler için ana register
    AccA: U_Int8 = U_Int8(0)
    
    # 8-bit Accumulator B register'ı - İkincil accumulator
    AccB: U_Int8 = U_Int8(0)
    
    # 16-bit Index register - Dizi indeksleme ve adres hesaplamaları için
    X: U_Int16 = U_Int16(0)
    
    # 16-bit Stack Pointer - Stack'in tepesini gösterir
    SP: U_Int16 = U_Int16(0)
    
    # 16-bit Program Counter - Çalıştırılacak sonraki komutun adresini tutar
    PC: U_Int16 = U_Int16(0)
    
    # Status Register - İşlemci durumunu gösteren flag'ler
    # 6 bit'lik bitarray: [C, Z, S, O, I, AC]
    # C  - Carry: Taşma flag'i
    # Z  - Zero: Sonuç sıfır flag'i  
    # S  - Sign: İşaret flag'i (negatif/pozitif)
    # O  - Overflow: Aritmetik taşma flag'i
    # I  - Interrupt Mask: Kesme maskesi (henüz implement edilmemiş)
    # AC - Auxiliary Carry: Yardımcı taşma flag'i
    SR: bitarray = bitarray([False] * 6)
    
    # Stack veri yapısı - LIFO (Last In, First Out) prensibiyle çalışır
    # Fonksiyon çağrıları, geçici değerler için kullanılır
    _stack: Stack_T = deque()

class Assembler:
    """
    6800 Mikroişlemcisi için 2-geçişli Assembler
    
    Birinci geçiş: Lexical Analysis (Sözcüksel Analiz)
    - Kaynak kodu token'lara ayırır
    - Sembol tablosunu oluşturur
    
    İkinci geçiş: Code Generation (Kod Üretimi)  
    - Token'ları makine koduna çevirir
    - Sembol referanslarını çözümler
    """
    
    def __init__(self, source: str) -> None:
        """
        Assembler'ı başlatır ve 2-geçişli işlemi başlatır
        
        Args:
            source: Assembly kaynak kodu (string formatında)
        """
        # Lexer referansı - başlangıçta None, sonra Lexer objesi olacak
        self.lexer = Optional[Lexer]
        
        # Birinci geçiş: Sembol tablosunu oluştur
        # Bu aşamada tüm etiketler, değişkenler ve adresleri belirlenir
        self.symbol_table: Symbol_Table = self._construct_symbol_table(source)
        
        # İkinci geçiş: Parser'ı başlat
        # Sembol tablosu ile birlikte syntax analysis yapar
        self.parser: Parser = Parser(source, self.symbol_table)
        
        # Üretilen makine kodunu tutacak binary stream
        # BytesIO, memory'de binary veri tutmak için kullanılır
        self.program: BytesIO = BytesIO()
    
    def _construct_symbol_table(self, source: str) -> Symbol_Table:
        """
        Birinci geçiş: Sembol tablosunu oluşturur
        
        Bu method assembly kodundaki tüm:
        - Label'ları (etiketler)
        - Variable'ları (değişkenler) 
        - Constant'ları (sabitler)
        - Address'leri (adresler)
        
        tespit eder ve sembol tablosuna ekler.
        
        Args:
            source: Assembly kaynak kodu
            
        Returns:
            Symbol_Table: Oluşturulan sembol tablosu
        """
        # Lexer'ı oluştur ve kaynak kodu ver
        self.lexer = Lexer(source)
        
        # Tüm token'ları işle - bu sırada sembol tablosu otomatik oluşur
        # Lexer iterator olarak çalışır, her token için bir kez çağrılır
        for token in self.lexer:
            pass  # Token'ları şimdilik sadece işliyoruz
        
        # Lexer'ın oluşturduğu sembol tablosunu döndür
        return self.lexer.symbols
    
    def assemble(self) -> BytesIO:
        """
        Assembly işlemini tamamlar ve makine kodunu döndürür
        
        Bu method:
        1. Parser'dan assembly komutlarını alır
        2. Her komutu makine koduna çevirir  
        3. Üretilen kodu program buffer'ına yazar
        
        Returns:
            BytesIO: Üretilen makine kodu (binary format)
        """
        # Şu anda sadece boş program buffer'ını döndürüyor
        # Gerçek implementasyonda burada kod üretimi yapılacak
        return self.program