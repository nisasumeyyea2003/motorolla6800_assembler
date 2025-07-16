# Gerekli modüller, tip tanımları ve sınıf tanımları yapılmış.
import axel.tokens as Tokens
from collections import deque
from typing import Union, List, overload, Deque, Tuple
from axel.lexer import Lexer, yylex_t
from axel.symbol import Symbol_Table, U_Int16

# Tip alias'ları: Token türleri ve Instruction (komut) tuple'ı tanımlanmış.
Token_T = Union[Tokens.Token, Tokens.Mnemonic, Tokens.Register]
Instruction_T = Tuple[Tokens.TokenEnum, Deque[yylex_t]]

# Özel hata sınıfı: Parser hatalarında kullanılacak.
class AssemblerParserError(Exception):
    pass

# Parser sınıfı: 6800 assembly dili kaynak kodunu satır satır çözüp yorumlayacak.
class Parser:
    """
    6800 assembler parser:
    - Lexer'dan aldığı tokenları okur,
    - Satır satır analiz eder,
    - Etiket, değişken veya komutları algılar,
    - Sembolleri sembol tablosuna kaydeder,
    - Komutları ve operandları parçalar.
    """

    def __init__(self, source: str,
                 symbols: Symbol_Table = Symbol_Table()) -> None:
        self._line = 1                   # Satır sayacı
        self.lexer: Lexer = Lexer(source)  # Kaynak kodu lexing işlemi için Lexer sınıfı
        self.symbols: Symbol_Table = symbols  # Sembol tablosu (etiketler, değişkenler vs)

    # Hata mesajı üretme fonksiyonu
    def error(self, expected: str, found: Tokens.TokenEnum) -> None:
        # Hangi konumda hata olduğu bilgisi alınıyor
        location = self.lexer.last_addr
        source = self.lexer._source[location:location + 12].replace('\n', ' ')
        # Detaylı hata mesajı oluşturup istisna fırlatılıyor
        raise AssemblerParserError(
            f'Parser failed near "{source}", '
            f'expected one of {expected}, '
            f'but found "{found.name}" '
            f'on line {self._line}.')

    # Immediate değerleri hex string'den bytes olarak çeviren fonksiyon
    @classmethod
    def parse_immediate_value(self, value: str) -> bytes:
        """
        Örnek: '#$1A' ya da '#1A' gibi stringleri bytes'a dönüştürür.
        TODO: decimal, binary, karakter gibi formatlar eklenebilir.
        """
        if value[:1] == '#' and value[1:2] == '$':
            return bytes.fromhex(value[2:])
        else:
            return bytes.fromhex(value[1:])

    # "take" fonksiyonu: Beklenen token tiplerini test eder, bulamazsa hata fırlatır.
    @overload
    def take(self, test: List[Token_T]) -> None: ...

    @overload
    def take(self, test: Token_T) -> None: ...

    def take(self, test: Union[Token_T, List[Token_T]]) -> None:
        """
        Lexer'dan bir sonraki token alınır.
        Eğer token, beklenenlerden biri değilse lexer geri çekilir ve hata verilir.
        """

        lexer = self.lexer
        next_token = next(lexer)  # Lexer'dan token al

        if isinstance(test, list):
            # Eğer beklenenler listesi ise, token listede var mı kontrol et
            if next_token not in test:
                options = list(map(lambda x: x.name, test))
                lexer.retract()  # Token geri çekilir
                self.error(', '.join(options), next_token)  # Hata mesajı
        else:
            # Tek bir beklenen token varsa, karşılaştır
            if next_token is not test:
                lexer.retract()
                self.error(test.name, next_token)

    # Kaynak koddan bir satır okuma ve yorumlama fonksiyonu
    def line(self) -> Union[
            Tuple[Tokens.TokenEnum, Deque[yylex_t]],
            bool]:
        """
        Satırdaki ilk token okunur.
        Boş satırlar atlanır.
        Satırdaki içerik:
            - Etiket varsa, devamında komut beklenir, komut ve operandlar döner.
            - Değişken tanımı varsa, sembol tablosuna kaydedilir.
            - Direkt komut varsa, komut ve operandlar döner.
        Satır sonuna gelince True, False ya da komut tuple'ı döner.
        """

        lexer = self.lexer
        # Beklenen token isimleri listesi
        test = [
            Tokens.Token.T_LABEL.name,
            Tokens.Token.T_VARIABLE.name,
            Tokens.Token.T_MNEMONIC.name]
        try:
            next(lexer)
            current = lexer.yylex['token']  # Geçerli token

            # Boş satırları atla (EOL tokenları)
            while current == Tokens.Token.T_EOL:
                self._line += 1
                next(lexer)
                current = lexer.yylex['token']

            if current == Tokens.Token.T_LABEL:
                # Etiket bulundu, hemen ardından mnemonic (komut) beklenir
                self.take(list(Tokens.Mnemonic))
                line = self.instruction(lexer.yylex)  # Komut ve operandları çöz
                self.take(Tokens.Token.T_EOL)          # Satır sonu bekle
                self._line += 1
                return line  # Komut ve operandlar döner

            elif current == Tokens.Token.T_VARIABLE:
                # Değişken tanımı
                self.variable(lexer.yylex)   # Değişkeni işle
                self.take(Tokens.Token.T_EOL)  # Satır sonu bekle
                self._line += 1
                return True  # Değişken tanımlandığını bildir

            elif isinstance(current, Tokens.Mnemonic):
                # Direkt komut varsa
                line = self.instruction(lexer.yylex)
                self.take(Tokens.Token.T_EOL)
                self._line += 1
                return line

        except StopIteration:
            # Dosya sonu, işlem bitti
            return False

        # Yukarıdaki durumların dışında hata var demektir.
        self.error(', '.join(test), lexer.yylex['token'])
        return False

    # Değişken tanımı işleme fonksiyonu
    def variable(self, label: yylex_t) -> None:
        """
        Etiket adı ve adres alınır.
        '=' ve ardından adres değeri beklenir.
        Sembol tablosunda değişken kaydı yapılır.
        """
        name = label['data']       # Değişken adı (string)
        addr = self.lexer.last_addr  # Adres bilgisi

        self.take(Tokens.Token.T_EQUAL)  # '=' bekle
        self.take([Tokens.Token.T_DIR_ADDR_UINT8,
                   Tokens.Token.T_EXT_ADDR_UINT16])  # Değişken değeri bekle

        # Sembol tablosundaki kayıt alınır ve bytes olarak güncellenir.
        if isinstance(name, str) and self.lexer.yylex['data'] is not None:
            symbol = self.symbols.get(name)
            if symbol is not None and isinstance(symbol[2], str):
                self.symbols.set(
                    name,
                    U_Int16(addr),
                    'variable',
                    Parser.parse_immediate_value(symbol[2]))
            else:
                raise AssemblerParserError(
                    f'Parser failed on variable "{name}"')

    # Operandları işleyen fonksiyon
    def operands(self) -> Deque[yylex_t]:
        """
        Operatörler, registerlar ve çeşitli veri türleri alınır.
        Operantlar deque yapısına ters sırada eklenir (yığın gibi).
        Hata olursa veya yeni token kalmazsa işlem biter.
        """
        stack: Deque[yylex_t] = deque()

        # Desteklenen operand türleri
        datatypes = [
            Tokens.Token.T_IMM_UINT8,
            Tokens.Token.T_IMM_UINT16,
            Tokens.Token.T_DIR_ADDR_UINT8,
            Tokens.Token.T_EXT_ADDR_UINT16,
            Tokens.Token.T_DISP_ADDR_INT8,
        ]
        while True:
            try:
                # Register, virgül veya veri tiplerinden biri beklenir
                self.take([
                    *list(Tokens.Register),
                    Tokens.Token.T_COMMA,
                    *datatypes])
                stack.appendleft(self.lexer.yylex)  # En başa ekle
            except AssemblerParserError:
                self.lexer.retract()  # Token geri çekilir
                break
            except StopIteration:
                break
        return stack

    # Komut ve operandları işleyen fonksiyon
    def instruction(self, instruction: yylex_t) -> Instruction_T:
        """
        Komut tokenı ve operandları çözümlenir.
        Tuple olarak (<komut tipi>, operandlar deque) döner.
        """
        return (instruction['token'], self.operands())
