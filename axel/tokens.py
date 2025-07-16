"""
ASSEMBLER TOKEN VE ENUM TANIMLARI
================================

Bu dosya, 6800 mikroişlemci assembler'ının lexical analyzer (sözcüksel çözümleyici)
kısmında kullanılan token'ları ve enum'ları tanımlar.

Token = Assembly kodundaki en küçük anlamlı birim (kelime, sayı, operatör vs.)
Enum = Sabit değerler listesi (C'deki enum gibi)
"""

from enum import Enum, unique, auto
from typing import TypeVar

# Tür güvenliği için TypeVar tanımı
T = TypeVar('T', bound='TokenEnum')


class TokenEnum(Enum):
    """Token Numaralandırmaları için temel sınıf.
    
    Her enum'da faydalı detayları kapsüller ve hızlı erişim sağlar.
    Aynı zamanda her 'auto()' çağrısında benzersizlik garantisi verir.
    
    Bu sınıf, standart Python Enum'unu genişleterek assembler'a
    özel özellikler ekler.
    """
    
    def _generate_next_value_(  # type: ignore
            self: T,
            start: int,
            count: int,
            last_values: int) -> T:
        """Otomatik değer üretici fonksiyonu.
        
        Python'un auto() fonksiyonu çağrıldığında bu fonksiyon çalışır.
        Normalde auto() 1, 2, 3... şeklinde sayılar üretir.
        Burada ise enum'un kendisini döndürüyoruz.
        
        Args:
            self: Enum nesnesi
            start: Başlangıç değeri
            count: Kaçıncı çağrı olduğu
            last_values: Önceki değerler
            
        Returns:
            Enum nesnesinin kendisi
        """
        return self


@unique  # Bu decorator, enum değerlerinin benzersiz olmasını garantiler
class Token(TokenEnum):
    """Sözcüksel Token'lar.
    
    Assembly dilindeki genel dil öğeleri ve veri türleri.
    Bu token'lar lexical analyzer tarafından üretilir ve
    parser tarafından kullanılır.
    
    Örnek: "LDA #100" → [T_MNEMONIC, T_IMM_UINT8]
    """
    
    # === GENEL TOKENLAR ===
    T_VARIABLE = auto()         # Değişken adı (örn: COUNT, INDEX)
    T_LABEL = auto()           # Etiket (örn: LOOP1:, START:)
    T_EQUAL = auto()           # = işareti (değişken tanımında)
    T_COMMA = auto()           # , virgül (parametreleri ayırır)
    T_EOL = auto()             # Satır sonu (End of Line)
    
    # === ASSEMBLY ÖĞELERİ ===
    T_MNEMONIC = auto()        # Komut adı (LDA, ADD, JMP vs.)
    T_REGISTER = auto()        # Register adı (A, B, X, SP vs.)
    T_UNKNOWN = auto()         # Tanınmayan token (hata durumu)
    
    # === SAYI VE ADRES TÜRLERI ===
    T_IMM_UINT8 = auto()       # 8-bit immediate değer (#100)
    T_IMM_UINT16 = auto()      # 16-bit immediate değer (#$1000)
    T_DIR_ADDR_UINT8 = auto()  # 8-bit direct adres ($50)
    T_EXT_ADDR_UINT16 = auto() # 16-bit extended adres ($1000)
    T_DISP_ADDR_INT8 = auto()  # 8-bit signed displacement (X+5)


@unique
class AddressingMode(TokenEnum):
    """Adresleme Modları.
    
    6800 mikroişlemci'nin desteklediği farklı adresleme şekilleri.
    Her komut belirli adresleme modlarını destekler.
    
    Örnek:
    - LDA #100    → Immediate addressing
    - LDA $50     → Direct addressing  
    - LDA $1000   → Extended addressing
    """
    
    # Akümülatör adresleme - register A üzerinde işlem
    ACC = auto()    # Örn: ROLA (Rotate Left A)
    
    # Immediate adresleme - sabit değer
    IMM = auto()    # Örn: LDA #100 (A'ya 100 yükle)
    
    # Direct adresleme - 8-bit adres (0-255 arası bellek)
    DIR = auto()    # Örn: LDA $50 (50. adresten A'ya yükle)
    
    # Extended adresleme - 16-bit adres (tüm bellek)
    EXT = auto()    # Örn: LDA $1000 (4096. adresten A'ya yükle)
    
    # Indexed adresleme - X register + offset
    IDX = auto()    # Örn: LDA 5,X (X+5 adresinden A'ya yükle)
    
    # Implied/Inherent adresleme - parametre yok
    INH = auto()    # Örn: NOP (No Operation)
    
    # Relative adresleme - dallanma komutları için
    REL = auto()    # Örn: BEQ LOOP1 (eşitse LOOP1'e dal)


@unique
class Register(TokenEnum):
    """Register'lar.
    
    6800 mikroişlemci'nin sahip olduğu register'lar.
    Her register farklı amaçlar için kullanılır.
    """
    
    T_A = auto()    # Accumulator A - ana hesaplama register'ı
    T_B = auto()    # Accumulator B - yardımcı hesaplama register'ı
    T_X = auto()    # Index Register - diziler ve pointer'lar için
    T_PC = auto()   # Program Counter - şu an çalışan komutun adresi
    T_SP = auto()   # Stack Pointer - stack'in tepesini gösterir
    T_SR = auto()   # Status Register - bayraklar (flags) register'ı


@unique
class Mnemonic(TokenEnum):
    """Mnemonikler (Komut Adları).
    
    6800 mikroişlemci'nin desteklediği tüm assembly komutları.
    Her mnemonic bir makine kodu komutuna karşılık gelir.
    
    Kategoriler:
    - Aritmetik: ADD, SUB, ADC, SBC
    - Mantıksal: AND, ORA, EOR
    - Transfer: LDA, STA, LDX, STX
    - Dallanma: JMP, JSR, BEQ, BNE
    - Stack: PSH, PUL
    - Shift/Rotate: ASL, ASR, ROL, ROR
    """
    
    # === ARİTMETİK KOMUTLAR ===
    T_ABA = auto()  # Add B to A - B'yi A'ya ekle
    T_ADC = auto()  # Add with Carry - carry ile topla
    T_ADD = auto()  # Add - topla
    T_SBA = auto()  # Subtract B from A - A'dan B'yi çıkar
    T_SBC = auto()  # Subtract with Carry - carry ile çıkar
    T_SUB = auto()  # Subtract - çıkar
    
    # === MANTIKSAL KOMUTLAR ===
    T_AND = auto()  # Logical AND - mantıksal VE
    T_ORA = auto()  # Logical OR - mantıksal VEYA
    T_EOR = auto()  # Exclusive OR - özel VEYA (XOR)
    T_COM = auto()  # Complement - 1'in tümleyeni
    T_NEG = auto()  # Negate - 2'nin tümleyeni (işaret değiştir)
    
    # === SHIFT VE ROTATE KOMUTLARI ===
    T_ASL = auto()  # Arithmetic Shift Left - sola aritmetik kaydır
    T_ASR = auto()  # Arithmetic Shift Right - sağa aritmetik kaydır
    T_LSR = auto()  # Logical Shift Right - sağa mantıksal kaydır
    T_ROL = auto()  # Rotate Left - sola döndür
    T_ROR = auto()  # Rotate Right - sağa döndür
    
    # === DALLANMA KOMUTLARI (Branch) ===
    T_BCC = auto()  # Branch if Carry Clear - carry 0 ise dal
    T_BCS = auto()  # Branch if Carry Set - carry 1 ise dal
    T_BEQ = auto()  # Branch if Equal (Zero) - eşitse dal
    T_BNE = auto()  # Branch if Not Equal - eşit değilse dal
    T_BGE = auto()  # Branch if Greater or Equal - büyük/eşit ise dal
    T_BGT = auto()  # Branch if Greater Than - büyükse dal
    T_BLE = auto()  # Branch if Less or Equal - küçük/eşit ise dal
    T_BLT = auto()  # Branch if Less Than - küçükse dal
    T_BHI = auto()  # Branch if Higher - yüksekse dal (unsigned)
    T_BLS = auto()  # Branch if Lower or Same - düşük/aynı ise dal
    T_BMI = auto()  # Branch if Minus - negatifse dal
    T_BPL = auto()  # Branch if Plus - pozitifse dal
    T_BVC = auto()  # Branch if Overflow Clear - overflow yoksa dal
    T_BVS = auto()  # Branch if Overflow Set - overflow varsa dal
    T_BRA = auto()  # Branch Always - her zaman dal
    T_BSR = auto()  # Branch to Subroutine - alt rutine dal
    
    # === ATLAMA KOMUTLARI (Jump) ===
    T_JMP = auto()  # Jump - atla
    T_JSR = auto()  # Jump to Subroutine - alt rutine atla
    T_RTI = auto()  # Return from Interrupt - interrupt'tan dön
    T_RTS = auto()  # Return from Subroutine - alt rutinden dön
    
    # === VERİ TRANSFER KOMUTLARI ===
    T_LDA = auto()  # Load Accumulator A - A'ya yükle
    T_LDS = auto()  # Load Stack Pointer - Stack Pointer'a yükle
    T_LDX = auto()  # Load Index Register - X'e yükle
    T_STA = auto()  # Store Accumulator A - A'yı kaydet
    T_STS = auto()  # Store Stack Pointer - Stack Pointer'ı kaydet
    T_STX = auto()  # Store Index Register - X'i kaydet
    
    # === REGISTER TRANSFER KOMUTLARI ===
    T_TAB = auto()  # Transfer A to B - A'dan B'ye transfer
    T_TBA = auto()  # Transfer B to A - B'den A'ya transfer
    T_TSX = auto()  # Transfer Stack Pointer to X - SP'den X'e
    T_TXS = auto()  # Transfer X to Stack Pointer - X'den SP'ye
    T_TAP = auto()  # Transfer A to Processor Status - A'dan SR'ye
    T_TPA = auto()  # Transfer Processor Status to A - SR'den A'ya
    
    # === STACK KOMUTLARI ===
    T_PSH = auto()  # Push - stack'e at (A veya B)
    T_PUL = auto()  # Pull - stack'ten çek (A veya B)
    
    # === TEST VE KARŞILAŞTIRMA ===
    T_BIT = auto()  # Bit Test - bit testi
    T_CBA = auto()  # Compare A with B - A ile B'yi karşılaştır
    T_CMP = auto()  # Compare - karşılaştır
    T_CPX = auto()  # Compare Index Register - X'i karşılaştır
    T_TST = auto()  # Test - test et (sıfır kontrolü)
    
    # === ARTIRMA/AZALTMA ===
    T_DEC = auto()  # Decrement - bir azalt
    T_INC = auto()  # Increment - bir artır
    T_DEX = auto()  # Decrement Index Register - X'i bir azalt
    T_INX = auto()  # Increment Index Register - X'i bir artır
    T_DES = auto()  # Decrement Stack Pointer - SP'yi bir azalt
    T_INS = auto()  # Increment Stack Pointer - SP'yi bir artır
    
    # === STATUS REGISTER KOMUTLARI ===
    T_CLC = auto()  # Clear Carry - carry bayrağını temizle
    T_CLI = auto()  # Clear Interrupt - interrupt bayrağını temizle
    T_CLV = auto()  # Clear Overflow - overflow bayrağını temizle
    T_SEC = auto()  # Set Carry - carry bayrağını set et
    T_SEI = auto()  # Set Interrupt - interrupt bayrağını set et
    T_SEV = auto()  # Set Overflow - overflow bayrağını set et
    
    # === ÖZEL KOMUTLAR ===
    T_CLR = auto()  # Clear - sıfırla
    T_DAA = auto()  # Decimal Adjust Accumulator - ondalık ayarlama
    T_NOP = auto()  # No Operation - hiçbir şey yapma
    T_SWI = auto()  # Software Interrupt - yazılım interrupt'ı
    T_WAI = auto()  # Wait for Interrupt - interrupt bekle


# === DALLANMA KOMUTLARI KÜMESİ ===
"""
Dallanma Mnemonikleri.

Bu küme, tüm dallanma komutlarını içerir. 
Assembler'da dallanma komutları özel işlem gerektirir çünkü:
1. Relative addressing kullanır
2. Sadece -128 ile +127 byte aralığında atlayabilir
3. Etiket çözümlemesi gerekir

Kullanım: if mnemonic in Branch_Mnemonics: ...
"""
Branch_Mnemonics = set([
    Mnemonic.T_BCC,  # Branch if Carry Clear
    Mnemonic.T_BCS,  # Branch if Carry Set
    Mnemonic.T_BEQ,  # Branch if Equal
    Mnemonic.T_BGE,  # Branch if Greater or Equal
    Mnemonic.T_BGT,  # Branch if Greater Than
    Mnemonic.T_BHI,  # Branch if Higher
    Mnemonic.T_BLE,  # Branch if Less or Equal
    Mnemonic.T_BLS,  # Branch if Lower or Same
    Mnemonic.T_BLT,  # Branch if Less Than
    Mnemonic.T_BMI,  # Branch if Minus
    Mnemonic.T_BNE,  # Branch if Not Equal
    Mnemonic.T_BPL,  # Branch if Plus
    Mnemonic.T_BRA,  # Branch Always
    Mnemonic.T_BSR,  # Branch to Subroutine
    Mnemonic.T_BVC,  # Branch if Overflow Clear
    Mnemonic.T_BVS   # Branch if Overflow Set
])


# === KULLANIM ÖRNEKLERİ ===
"""
Bu enum'lar assembler'ın farklı aşamalarında kullanılır:

1. LEXICAL ANALYSIS (Tokenization):
   "LDA #100" → [Token.T_MNEMONIC, Token.T_IMM_UINT8]

2. PARSING:
   - Token.T_MNEMONIC → Mnemonic.T_LDA
   - Token.T_IMM_UINT8 → AddressingMode.IMM

3. CODE GENERATION:
   - Mnemonic.T_LDA + AddressingMode.IMM → Machine code: 86 64

Örnek kullanım:
```python
if token_type == Token.T_MNEMONIC:
    if mnemonic in Branch_Mnemonics:
        addressing_mode = AddressingMode.REL
    else:
        # Normal komut işleme
```
"""