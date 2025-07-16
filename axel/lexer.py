
import re
from axel.tokens import TokenEnum, Token as Token, Register, Mnemonic
from axel.tokens import Branch_Mnemonics
from axel.symbol import Symbol_Table, U_Int16
from collections import deque
from typing import Optional, TypeVar, Deque, Tuple
from mypy_extensions import TypedDict

M = TypeVar('M', bound='Lexer')


class yylex_t(TypedDict, total=False):
    """Lexer'ın döndürdüğü veri yapısı. 
    
    YACC/LEX formatına benzer şekilde tasarlanmış:
    - token: Bulunan token türü (enum)
    - data: Token'ın gerçek metinsel verisi (YACC'taki yytext)
    """
    token: TokenEnum
    data: Optional[str]  # The `yytext` data


class Lexer:
    """6800 Assembly Dili için Lexical Analyzer (Sözcüksel Çözümleyici)

    Bu sınıf assembly kaynak kodunu tarayarak token'lara (sözcüklere) ayırır.
    LL(1) parser için uygun token akışı üretir ve aynı zamanda sembol tablosu oluşturur.
    
    Temel İşlevleri:
    - Assembly kodunu karakter karakter tarar
    - Mnemonik'leri (ADD, LDA, vb.) tanır
    - Register'ları (A, B, X) tanır  
    - Adres türlerini ayırt eder (immediate, direct, extended)
    - Label'ları ve değişkenleri sembol tablosuna ekler
    - Yorum satırlarını atlar
    
    Kullanım:
        lexer = Lexer("LDAA #$FF\\nSTAA $00")
        for token in lexer:
            print(token)
    """
    
    def __init__(self, source: str) -> None:
        """Lexer'ı kaynak kod ile başlatır.
        
        Args:
            source: Çözümlenecek assembly kaynak kodu
        """
        self._source: str = source                    # Assembly kaynak kodu
        self._pointer: int = 0                        # Şu anki karakter pozisyonu
        self.yylex: yylex_t = {                      # Son bulunan token bilgisi
            'token': Token.T_UNKNOWN,
            'data': None
        }
        self._at = self._pointer                      # Son token öncesi pozisyon
        self._symbol_table: Symbol_Table = Symbol_Table()  # Label ve değişken tablosu
        self._symbol_stack: Deque[Tuple[str, str]] = deque()  # Geçici sembol yığını
        self._last: TokenEnum = Token.T_UNKNOWN      # En son bulunan token türü

    @property
    def pointer(self) -> str:
        """Şu anki karakter pozisyonundaki karakteri döndürür.
        
        Returns:
            Mevcut karakter, dosya sonu ise boş string
        """
        try:
            return self._source[self._pointer]
        except IndexError:
            return ''

    @property
    def symbols(self) -> Symbol_Table:
        """Oluşturulan sembol tablosunu döndürür.
        
        Returns:
            Label'lar ve değişkenlerin saklandığı sembol tablosu
        """
        return self._symbol_table

    @property
    def last_token(self) -> TokenEnum:
        """En son bulunan token türünü döndürür.
        
        Returns:
            Son lexical token
        """
        return self._last

    @property
    def last_addr(self) -> int:
        """Son iterasyon öncesi pointer pozisyonunu döndürür.
        
        Returns:
            Son token'ın başlangıç pozisyonu
        """
        return self._at

    def __iter__(self: M) -> M:
        """Iterator protokolü için gerekli metod."""
        return self

    def __next__(self) -> TokenEnum:
        """Bir sonraki token'ı tarar ve döndürür.
        
        Bu metod her çağrıldığında:
        1. Bir sonraki terimi okur (whitespace ve yorum atlanır)
        2. Terimi uygun token türüne dönüştürür
        3. Sembol tablosunu günceller (gerekirse)
        
        Returns:
            Bulunan token türü
            
        Raises:
            StopIteration: Kaynak kod bittiğinde
        """
        self._at = self._pointer                      # Mevcut pozisyonu kaydet
        term = self._read_term()                      # Bir sonraki terimi oku
        token: Optional[TokenEnum] = None
        
        if not term:
            raise StopIteration('Lexer Iterator out of bounds')

        self._reset()                                 # Token bilgisini sıfırla
        token = self._get_token(term)                # Terimi token'a dönüştür

        # Eğer token tanınmadıysa, sembol tablosunda ara
        if token == Token.T_UNKNOWN:
            if term in self._symbol_table.table:
                symbol = self._symbol_table.get(term)
                if symbol is not None:
                    # Değişken ise, değerini tekrar tokenize et
                    if symbol[1] == 'variable' and isinstance(symbol[2], str):
                        token = self._get_token(symbol[2])

        return token

    def _get_token(self, term: str) -> TokenEnum:
        """Bir terimi uygun token türüne dönüştürür.

        Bu metod sırayla farklı token türlerini kontrol eder:
        1. Satır sonu (EOL)
        2. Register'lar (A, B, X)
        3. Mnemonik'ler (LDA, STA, ADD, vb.)
        4. Dallanma adresleri (branch displacement)
        5. Bellek adresleri (direct/extended)
        6. Virgül ayırıcıları
        7. Eşitlik işareti
        8. Immediate değerler (#$FF)
        9. Label'lar
        10. Değişkenler

        Args:
            term: Çözümlenecek terim
            
        Returns:
            Uygun token türü veya T_UNKNOWN
        """
        token: Optional[TokenEnum] = None

        token = token or self._eol_token(term)                    # \n, \r\n
        token = token or self._register_token(term)               # A, B, X
        token = token or self._mnemonic_token(term)               # LDA, STA, ADD
        token = token or self._displacement_token(term)           # Branch adresleri
        token = token or self._direct_or_extended_token(term)     # $FF, $FFFF
        token = token or self._comma_token(term)                  # ,
        token = token or self._equal_token(term)                  # =
        token = token or self._immediate_token(term)              # #$FF
        token = token or self._equal_token(term)                  # = (tekrar kontrol)
        token = token or self._label_token(term)                  # LOOP:, START
        token = token or self._variable_token(term)               # VALUE =

        return token or Token.T_UNKNOWN

    def retract(self) -> None:
        """Pointer'ı son token öncesi pozisyona geri alır.
        
        Parser'da hatalı kabul durumlarında kullanılır.
        Örnek: Bir token'ın parser tarafından beklenmeyen yerde 
        bulunması durumunda geri alınabilir.
        """
        self._pointer = self._at

    def _inc(self) -> None:
        """Pointer'ı bir karakter ileri alır (pointer arithmetic benzeri)."""
        self._pointer += 1

    def _dec(self) -> None:
        """Pointer'ı bir karakter geri alır (pointer arithmetic benzeri)."""
        self._pointer -= 1

    def _read_term(self) -> str:
        """Kaynak koddan bir sonraki terimi okur.

        Bu metod:
        1. Boşlukları ve yorumları atlar
        2. Özel karakterleri (virgül, satır sonu) tekil olarak döndürür
        3. Normal terimleri boşluk/virgül/satır sonuna kadar okur
        
        Returns:
            Okunan terim string'i
        """
        term: str = ''
        self._skip_whitespace_and_comments()          # Boşluk ve yorumları atla
        
        # Özel karakterler
        if self.pointer == '\r':
            self._inc()
            return '\r\n'
        elif self.pointer == '\n':
            return '\n'
        elif self.pointer == ',':
            return ','
            
        # Normal terim okuma (delimiter'a kadar)
        while self.pointer and not re.match('[,\t\n ]', self.pointer):
            term += self.pointer
            self._inc()
        return term

    def _peek_next(self) -> str:
        """Bir sonraki terimi pointer'ı hareket ettirmeden gözetler.
        
        Parser'da lookahead için kullanılır. Örneğin bir terimin
        label mi yoksa değişken mi olduğunu anlamak için sonraki
        terimin '=' olup olmadığına bakılır.
        
        Returns:
            Bir sonraki terim (pointer değişmez)
        """
        term: str = ''
        self._skip_whitespace_and_comments()
        index: int = self._pointer
        size: int = len(self._source)
        
        # Geçici pointer ile sonraki terimi oku
        while index < size and not re.match('[,\t\r\n ]', self._source[index]):
            term += self._source[index]
            index += 1

        return term

    def _reset(self) -> None:
        """Scanner verilerini sıfırlar."""
        self.yylex = {
            'token': Token.T_UNKNOWN,
            'data': None
        }

    def _set_token(self, token: TokenEnum, term: str) -> None:
        """Son bulunan token'ı ve scanner verisini ayarlar."""
        self._last = token
        self.yylex = {
            'token': token,
            'data': term
        }

    def _skip_whitespace_and_comments(self) -> None:
        """Boşlukları ve yorumları özyinelemeli olarak atlar.
        
        Assembly'de yorumlar ';' ile başlar ve satır sonuna kadar devam eder.
        Bu metod tüm boşlukları (tab, space) ve yorum satırlarını
        bir sonraki anlamlı karaktere kadar atlar.
        """
        # Boşluk karakterlerini atla
        if re.match('[\t ]', self.pointer):
            self._inc()
            self._skip_whitespace_and_comments()
            
        # Yorum satırını atla (';' ile başlayan)
        if self.pointer == ';':
            self._skip_to_next_line()
            self._skip_whitespace_and_comments()

    def _skip_to_next_line(self) -> None:
        """Satır sonu karakterlerine kadar tüm karakterleri atlar.
        
        Yorum satırlarını atlamak için kullanılır.
        """
        skip = True
        while skip:
            if not self.pointer:                     # Dosya sonu
                skip = False
                break
            self._inc()
            if self.pointer == '\n' or self.pointer == '\r':
                skip = False

    def _eol_token(self, term: str) -> Optional[TokenEnum]:
        """Satır sonu (End of Line) token'larını tanır.
        
        Windows (\r\n) ve Unix (\n) formatlarını destekler.
        
        Args:
            term: Kontrol edilecek terim
            
        Returns:
            T_EOL token'ı veya None
        """
        if term[:2] == '\r\n':                       # Windows format
            self._inc()
            self._inc()
            self._set_token(Token.T_EOL, '\r\n')
            return Token.T_EOL
        elif term[0] == '\n':                        # Unix format
            self._inc()
            self._set_token(Token.T_EOL, '\n')
            return Token.T_EOL
        return None

    def _variable_token(self, term: str) -> Optional[TokenEnum]:
        """Değişken tanımlamalarını tokenize eder.
        
        Assembly'de değişkenler şu formatta tanımlanır:
        VARIABLE_NAME = $FF
        
        Bu metod değişken adını tanır ve sembol yığınına ekler.
        
        Args:
            term: Kontrol edilecek terim
            
        Returns:
            T_VARIABLE token'ı veya None
        """
        # Sonraki terim '=' ise bu bir değişken tanımı
        if self._peek_next() == '=':
            self._symbol_stack.append(('variable', term))
            self._set_token(Token.T_VARIABLE, term)
            return Token.T_VARIABLE
        return None

    def _comma_token(self, term: str) -> Optional[TokenEnum]:
        """Virgül ayırıcılarını tokenize eder.
        
        6800 assembly'de register'lar arası ayırma için kullanılır:
        LDA A,X  (A register'ından X index register'ı ile)
        
        Args:
            term: Kontrol edilecek terim
            
        Returns:
            T_COMMA token'ı veya None
        """
        if self.pointer == ',':
            self._inc()
            self._set_token(Token.T_COMMA, term)
            return Token.T_COMMA
        return None

    def _label_token(self, term: str) -> Optional[TokenEnum]:
        """Label'ları (etiketleri) tokenize eder.
        
        Assembly'de label'lar:
        1. Satır başında olmalı
        2. İsteğe bağlı ':' ile bitebilir
        3. Arkasından mnemonik gelmeli
        
        Örnekler:
        LOOP:    LDA #$FF
        START    NOP
        
        Args:
            term: Kontrol edilecek terim
            
        Returns:
            T_LABEL token'ı veya None
        """
        # Önceki karakterin satır başı olup olmadığını kontrol et
        peek_back = self._pointer - (len(term) + 1)
        previous_line = self._source[peek_back] if peek_back >= 0 else '\n'
        
        if previous_line == '\n' or peek_back <= 0:
            # Sonraki terim mnemonik mi veya ':' ile mi bitiyor?
            if f'T_{self._peek_next()}' in Mnemonic.__members__ or term[-1:] == ':':
                self._symbol_stack.append(('label', term))
                self._set_token(Token.T_LABEL, term)
                return Token.T_LABEL
        return None

    def _equal_token(self, term: str) -> Optional[TokenEnum]:
        """Eşitlik işaretini tokenize eder ve değişken ataması yapar.
        
        Değişken tanımlarında kullanılır:
        VALUE = $FF
        
        Bu metod aynı zamanda sembol yığınından değişken adını alır
        ve sembol tablosuna ekler.
        
        Args:
            term: Kontrol edilecek terim
            
        Returns:
            T_EQUAL token'ı veya None
        """
        if term == '=':
            # Sembol yığınından değişken adını al ve sembol tablosuna ekle
            if len(self._symbol_stack) and self._symbol_stack[-1][0] == 'variable':
                assign = self._symbol_stack.pop()
                self._symbol_table.set(
                    assign[1],                        # Değişken adı
                    U_Int16(self.last_addr - len(assign[1]) - 1),  # Pozisyon
                    'variable',                       # Tür
                    self._peek_next())               # Değer

            self._set_token(Token.T_EQUAL, term)
            return Token.T_EQUAL
        return None

    def _immediate_token(self, term: str) -> Optional[TokenEnum]:
        """Immediate (anlık) veri token'larını tanır.
        
        6800 assembly'de immediate veriler '#$' ile başlar:
        - #$FF    : 8-bit immediate değer
        - #$FFFF  : 16-bit immediate değer
        
        Örnekler:
        LDA #$01     (A register'ına 1 değerini yükle)
        LDA #$FF00   (A register'ına FF00 değerini yükle)
        
        Args:
            term: Kontrol edilecek terim
            
        Returns:
            T_IMM_UINT8, T_IMM_UINT16 veya None
        """
        if term[:1] == '#' and term[1:2] == '$':
            try:
                hex_part = term[2:]
                byte_len = len(bytes.fromhex(hex_part))
                
                if byte_len == 1:                    # 8-bit immediate
                    self._set_token(Token.T_IMM_UINT8, term)
                    return Token.T_IMM_UINT8
                elif byte_len == 2:                  # 16-bit immediate
                    self._set_token(Token.T_IMM_UINT16, term)
                    return Token.T_IMM_UINT16
            except ValueError:
                pass  # Geçersiz hex değeri
        return None

    def _direct_or_extended_token(self, term: str) -> Optional[TokenEnum]:
        """Direct veya Extended bellek adreslerini tokenize eder.
        
        6800 assembly'de bellek adresleri '$' ile başlar:
        - $FF     : 8-bit direct addressing (0x00-0xFF arası)
        - $FFFF   : 16-bit extended addressing (0x0000-0xFFFF arası)
        
        Direct addressing daha hızlı ama sınırlı adres aralığı.
        Extended addressing daha yavaş ama tüm bellek erişimi.
        
        Örnekler:
        LDA $80      (80h adresindeki değeri A'ya yükle - direct)
        LDA $8000    (8000h adresindeki değeri A'ya yükle - extended)
        
        TODO: Decimal, binary, tek karakter formatları eklenecek
        
        Args:
            term: Kontrol edilecek terim
            
        Returns:
            T_DIR_ADDR_UINT8, T_EXT_ADDR_UINT16 veya None
        """
        if term[:1] == '$':
            try:
                hex_part = term[1:]
                byte_len = len(bytes.fromhex(hex_part))
                
                if byte_len == 1:                    # 8-bit direct address
                    self._set_token(Token.T_DIR_ADDR_UINT8, term)
                    return Token.T_DIR_ADDR_UINT8
                elif byte_len == 2:                  # 16-bit extended address
                    self._set_token(Token.T_EXT_ADDR_UINT16, term)
                    return Token.T_EXT_ADDR_UINT16
            except ValueError:
                pass  # Geçersiz hex değeri
        return None

    def _displacement_token(self, term: str) -> Optional[TokenEnum]:
        """Dallanma (branch) displacement adreslerini tokenize eder.
        
        6800'de dallanma komutları (BEQ, BNE, BRA, vb.) relative addressing kullanır.
        Displacement değeri mevcut PC'den +/- 128 byte aralığında olmalı.
        
        Bu metod sadece son token'ın branch mnemonik'i olması durumunda
        çalışır ve register/eşitlik kontrolü yapar.
        
        Örnekler:
        BEQ LOOP     (LOOP label'ına branch et)
        BNE $10      (PC+16 adresine branch et)
        
        Args:
            term: Kontrol edilecek terim
            
        Returns:
            T_DISP_ADDR_INT8 veya None
        """
        # Son token branch mnemonik'i mi?
        if self._last in Branch_Mnemonics:
            # Register adı değil ve değişken tanımı değil
            if f'T_{term[3:]}' not in Register.__members__ and self._peek_next() != '=':
                self._set_token(Token.T_DISP_ADDR_INT8, term)
                return Token.T_DISP_ADDR_INT8
        return None

    def _mnemonic_token(self, term: str) -> Optional[TokenEnum]:
        """6800 ISA mnemonik'lerini tokenize eder.
        
        6800 mikroişlemcisi mnemonik'leri 3 harfli komutlardır:
        - LDA: Load Accumulator A
        - STA: Store Accumulator A  
        - ADD: Add to Accumulator
        - JMP: Jump
        - vb.
        
        Bazı mnemonik'ler register ile birleşik kullanılabilir:
        - LDAA: Load Accumulator A (A register spesifik)
        - STAB: Store Accumulator B (B register spesifik)
        
        Bu metod aynı zamanda label'lar için sembol tablosu girişi yapar.
        
        Örnekler:
        LDAA #$01    (3 harfli + register)
        TAB          (3 harfli tek başına)
        TST B        (3 harfli + ayrı register)
        
        Args:
            term: Kontrol edilecek terim
            
        Returns:
            Uygun mnemonik token'ı veya None
        """
        # 3 harfli mnemonik kontrol et
        if len(term) == 3 and f'T_{term[:3]}' in Mnemonic.__members__:
            self._set_token(Mnemonic[f'T_{term[:3]}'], term[:3])
            
            # Eğer bekleyen label varsa sembol tablosuna ekle
            if len(self._symbol_stack) and self._symbol_stack[-1][0] == 'label':
                assign = self._symbol_stack.pop()
                self._symbol_table.set(
                    assign[1],                        # Label adı
                    U_Int16(self.last_addr - len(assign[1]) - 1),  # Pozisyon
                    'label',                          # Tür
                    U_Int16(self.last_addr - len(assign[1]) - 1))  # Değer
            return Mnemonic[f'T_{term[:3]}']

        # 4 harfli mnemonik+register kombinasyonu (örn: LDAA)
        if (len(term) == 4 and 
            f'T_{term[:3]}' in Mnemonic.__members__ and 
            f'T_{term[3:]}' in Register.__members__):
            
            self._dec()  # Register karakterini geri al
            self._set_token(Mnemonic[f'T_{term[:3]}'], term[:3])
            
            # Label varsa sembol tablosuna ekle
            if len(self._symbol_stack) and self._symbol_stack[-1][0] == 'label':
                assign = self._symbol_stack.pop()
                self._symbol_table.set(
                    assign[1],
                    U_Int16(self.last_addr - len(assign[1]) - 1),
                    'label',
                    U_Int16(self.last_addr - len(assign[1]) - 1))

            return Mnemonic[f'T_{term[:3]}']
        return None

    def _register_token(self, term: str) -> Optional[TokenEnum]:
        """Register operandlarını tokenize eder.
        
        6800 mikroişlemcisinde register'lar:
        - A: Accumulator A (8-bit)
        - B: Accumulator B (8-bit)  
        - X: Index Register (16-bit, özel durum)
        
        X register'ı özel bir durumdur çünkü indexed addressing
        modunda virgül ile ayrılır: LDA $00,X
        
        Args:
            term: Kontrol edilecek terim
            
        Returns:
            Uygun register token'ı veya None
        """
        # X register özel durumu (sonraki karakter kontrol edilir)
        try:
            if self._source[self._pointer + 1] == 'X':
                self._inc()
                self._set_token(Register.T_X, 'X')
                return Register.T_X
        except IndexError:
            pass
            
        # Normal register kontrol et (A, B)
        if f'T_{term}' in Register.__members__:
            self._set_token(Register[f'T_{term}'], term)
            return Register[f'T_{term}']
        return None