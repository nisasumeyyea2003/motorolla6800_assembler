
# Gerekli kütüphaneleri içe aktar
import types  # Python tip sistemi için
from typing import Deque, Dict, Any  # Tip ipuçları için
from bitarray import bitarray  # Bit dizileri için (flag işlemleri)
from axel.tokens import AddressingMode  # Adres belirtme modları
from axel.parser import Parser, AssemblerParserError  # Assembly parser
from axel.lexer import yylex_t  # Lexical analyzer tipi
from axel.data import processing  # Veri işleme dekoratörü
from axel.assembler import Registers as Register_T
from test.unit.data_test import addr_codes  # Register sınıf tipi


class Processor(type):
    """6800 İşlemci Metaklası - Opcode Çevirici Dekoratörü

    Bu metaklas, her assembly instruction'ı için otomatik pre/post-processing 
    ekler. Her komut çalıştırıldıktan sonra:
    
    1. Accumulator register'larının (A, B) değerlerini günceller
    2. Status Register (SR) flag'larını yeniden hesaplar
    3. Condition Code Register (CCR) flag'larını ayarlar
    
    6800 mikroişlemcisinde her aritmetik/mantık işlemi sonucunda
    işlemci flag'ları (Zero, Negative, Carry, Overflow) güncellenmelidir.
    Bu metaklas bu işlemi otomatik olarak yapar.
    """
    def __new__(cls, name: str, bases: Any, attr: Dict[Any, Any]) -> Any:
        """Yeni sınıf oluştururken her method'u processing ile dekore et."""
        # Sınıfın tüm attribute'larını dolaş
        for attr_name, value in attr.items():
            # Eğer değer bir fonksiyon ise ve string değilse
            if (not isinstance(value, types.FunctionType) and 
                not isinstance(value, str)):
                # Processing dekoratörü ile sar
                attr[attr_name] = processing(value.__func__)
        
        # Süper sınıfın __new__ metodunu çağır ve yeni sınıfı döndür
        return super(Processor, cls).__new__(cls, name, bases, attr)


class Translate(metaclass=Processor):
    """6800 Assembly Komutlarını Makine Koduna Çeviren Sınıf"""

    @staticmethod
    def aba(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """ABA - Add Accumulator B to Accumulator A"""
        # ABA komutu için opcode: 0x1B
        opcode = bytearray.fromhex('1B')
        
        # Eğer accumulator modunda ise
        if addr_mode == AddressingMode.ACC:
            # A = A + B işlemi yap
            registers.AccA += registers.AccB.num
            
        return opcode

    @staticmethod
    def adc(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """ADC - Add with Carry"""
        opcode: bytearray = bytearray()  # Boş opcode başlat
        data: int = 0  # Veri değişkeni
        status: bitarray = registers.SR  # Status register'ı al
        
        # İlk operandı al
        o = operands[0]['data']
        # Operand string olmalı, değilse hata fırlat
        if not isinstance(o, str):
            raise AssemblerParserError(f'Invalid instruction operand')
        
        # Immediate (anlık) mod kontrolü
        if addr_mode == AddressingMode.IMM:
            # A register'ına mı yoksa B'ye mi ekleniyor kontrol et
            if operands[-1]['data'] == 'A':
                opcode = bytearray.fromhex('89')  # ADCA immediate opcode
            else:
                opcode = bytearray.fromhex('C9')  # ADCB immediate opcode
            
            # Immediate değeri parse et ve hex'e çevir
            operand = int(Parser.parse_immediate_value(o).hex(), 16)
            
            # Carry flag set edilmiş mi kontrol et
            if status[0] is True:
                # Carry varsa binary'e çevir ve carry bit'ini ekle
                b = bin(operand)
                data = int('0b' + status.to01()[0] + b[2:], 2)
            else:
                # Carry yoksa direkt binary'e çevir
                data = int(bin(operand), 2)
            
            # A register'ına veriyi ekle
            registers.AccA += data
        
        # Opcode ve veriyi birleştirerek döndür
        return opcode + bytearray.fromhex(hex(data)[2:])

    @staticmethod
    def add(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """ADD - Add without carry"""
        opcode: bytearray = bytearray()  # Boş opcode başlat
        
        # Immediate (anlık) mod kontrolü
        if addr_mode == AddressingMode.IMM:
            # A register'ına mı ekleniyor kontrol et
            if operands[-1]['data'] == 'A':
                opcode = bytearray.fromhex('8B')  # ADDA immediate opcode
                # Immediate değeri parse et ve A'ya ekle
                operand = int(Parser.parse_immediate_value(operands[0]['data']).hex(), 16)
                registers.AccA += operand
            else:
                opcode = bytearray.fromhex('CB')  # ADDB immediate opcode
                # Immediate değeri parse et ve B'ye ekle
                operand = int(Parser.parse_immediate_value(operands[0]['data']).hex(), 16)
                registers.AccB += operand
        # Direct (doğrudan) mod kontrolü
        elif addr_mode == AddressingMode.DIR:
            # A register'ına mı ekleniyor kontrol et
            if operands[-1]['data'] == 'A':
                opcode = bytearray.fromhex('9B')  # ADDA direct opcode
            else:
                opcode = bytearray.fromhex('DB')  # ADDB direct opcode
        
        return opcode

    @staticmethod
    def and_(addr_mode: AddressingMode,
             operands: Deque[yylex_t],
             registers: Register_T) -> bytearray:
        """AND - Logical AND"""
        opcode: bytearray = bytearray()  # Boş opcode başlat
        
        # Immediate (anlık) mod kontrolü
        if addr_mode == AddressingMode.IMM:
            # A register'ıyla mı AND yapılıyor kontrol et
            if operands[-1]['data'] == 'A':
                opcode = bytearray.fromhex('84')  # ANDA immediate opcode
                # Immediate değeri parse et ve A ile AND yap
                operand = int(Parser.parse_immediate_value(operands[0]['data']).hex(), 16)
                registers.AccA &= operand
            else:
                opcode = bytearray.fromhex('C4')  # ANDB immediate opcode
                # Immediate değeri parse et ve B ile AND yap
                operand = int(Parser.parse_immediate_value(operands[0]['data']).hex(), 16)
                registers.AccB &= operand
        
        return opcode

    @staticmethod
    def asl(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """ASL - Arithmetic Shift Left"""
        opcode: bytearray = bytearray()  # Boş opcode başlat
        
        # Accumulator mod kontrolü
        if addr_mode == AddressingMode.ACC:
            # A register'ını mı shift ediyoruz kontrol et
            if operands[0]['data'] == 'A':
                opcode = bytearray.fromhex('48')  # ASLA opcode
                # A register'ını 1 bit sola kaydır (çarpma x2)
                registers.AccA <<= 1
            else:
                opcode = bytearray.fromhex('58')  # ASLB opcode
                # B register'ını 1 bit sola kaydır (çarpma x2)
                registers.AccB <<= 1
        
        return opcode

    @staticmethod
    def asr(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """ASR - Arithmetic Shift Right"""
        opcode: bytearray = bytearray()  # Boş opcode başlat
        
        # Accumulator mod kontrolü
        if addr_mode == AddressingMode.ACC:
            # A register'ını mı shift ediyoruz kontrol et
            if operands[0]['data'] == 'A':
                opcode = bytearray.fromhex('47')  # ASRA opcode
                # A register'ını 1 bit sağa kaydır (bölme /2)
                registers.AccA >>= 1
            else:
                opcode = bytearray.fromhex('57')  # ASRB opcode  
                # B register'ını 1 bit sağa kaydır (bölme /2)
                registers.AccB >>= 1
        
        return opcode

    @staticmethod
    def bcc(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """BCC - Branch if Carry Clear"""
        opcode = bytearray.fromhex('24')  # BCC opcode
        # Operand varsa hex'den int'e çevir, yoksa 0
        offset = int(operands[0]['data'], 16) if operands else 0
        # Opcode ve offset'i birleştir
        return opcode + bytearray([offset])

    @staticmethod
    def bcs(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """BCS - Branch if Carry Set"""
        opcode = bytearray.fromhex('25')  # BCS opcode
        # Operand varsa hex'den int'e çevir, yoksa 0
        offset = int(operands[0]['data'], 16) if operands else 0
        # Opcode ve offset'i birleştir
        return opcode + bytearray([offset])

    @staticmethod
    def beq(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """BEQ - Branch if Equal"""
        opcode = bytearray.fromhex('27')  # BEQ opcode
        # Operand varsa hex'den int'e çevir, yoksa 0
        offset = int(operands[0]['data'], 16) if operands else 0
        # Opcode ve offset'i birleştir
        return opcode + bytearray([offset])

    @staticmethod
    def bge(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """BGE - Branch if Greater or Equal"""
        opcode = bytearray.fromhex('2C')  # BGE opcode
        # Operand varsa hex'den int'e çevir, yoksa 0
        offset = int(operands[0]['data'], 16) if operands else 0
        # Opcode ve offset'i birleştir
        return opcode + bytearray([offset])

    @staticmethod
    def bgt(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """BGT - Branch if Greater Than"""
        opcode = bytearray.fromhex('2E')  # BGT opcode
        # Operand varsa hex'den int'e çevir, yoksa 0
        offset = int(operands[0]['data'], 16) if operands else 0
        # Opcode ve offset'i birleştir
        return opcode + bytearray([offset])

    @staticmethod
    def bhi(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """BHI - Branch if Higher"""
        opcode = bytearray.fromhex('22')  # BHI opcode
        # Operand varsa hex'den int'e çevir, yoksa 0
        offset = int(operands[0]['data'], 16) if operands else 0
        # Opcode ve offset'i birleştir
        return opcode + bytearray([offset])

    @staticmethod
    def ble(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """BLE - Branch if Less or Equal"""
        opcode = bytearray.fromhex('2F')  # BLE opcode
        # Operand varsa hex'den int'e çevir, yoksa 0
        offset = int(operands[0]['data'], 16) if operands else 0
        # Opcode ve offset'i birleştir
        return opcode + bytearray([offset])

    @staticmethod
    def bls(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """BLS - Branch if Lower or Same"""
        opcode = bytearray.fromhex('23')  # BLS opcode
        # Operand varsa hex'den int'e çevir, yoksa 0
        offset = int(operands[0]['data'], 16) if operands else 0
        # Opcode ve offset'i birleştir
        return opcode + bytearray([offset])

    @staticmethod
    def blt(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """BLT - Branch if Less Than"""
        opcode = bytearray.fromhex('2D')  # BLT opcode
        # Operand varsa hex'den int'e çevir, yoksa 0
        offset = int(operands[0]['data'], 16) if operands else 0
        # Opcode ve offset'i birleştir
        return opcode + bytearray([offset])

    @staticmethod
    def bmi(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """BMI - Branch if Minus"""
        opcode = bytearray.fromhex('2B')  # BMI opcode
        # Operand varsa hex'den int'e çevir, yoksa 0
        offset = int(operands[0]['data'], 16) if operands else 0
        # Opcode ve offset'i birleştir
        return opcode + bytearray([offset])

    @staticmethod
    def bne(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """BNE - Branch if Not Equal"""
        opcode = bytearray.fromhex('26')  # BNE opcode
        # Operand varsa hex'den int'e çevir, yoksa 0
        offset = int(operands[0]['data'], 16) if operands else 0
        # Opcode ve offset'i birleştir
        return opcode + bytearray([offset])

    @staticmethod
    def bpl(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """BPL - Branch if Plus"""
        opcode = bytearray.fromhex('2A')  # BPL opcode
        # Operand varsa hex'den int'e çevir, yoksa 0
        offset = int(operands[0]['data'], 16) if operands else 0
        # Opcode ve offset'i birleştir
        return opcode + bytearray([offset])

    @staticmethod
    def bra(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """BRA - Branch Always"""
        opcode = bytearray.fromhex('20')  # BRA opcode
        # Operand varsa hex'den int'e çevir, yoksa 0
        offset = int(operands[0]['data'], 16) if operands else 0
        # Opcode ve offset'i birleştir
        return opcode + bytearray([offset])

    @staticmethod
    def bsr(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """BSR - Branch to Subroutine"""
        opcode = bytearray.fromhex('8D')  # BSR opcode
        # Operand varsa hex'den int'e çevir, yoksa 0
        offset = int(operands[0]['data'], 16) if operands else 0
        # Opcode ve offset'i birleştir
        return opcode + bytearray([offset])

    @staticmethod
    def bvc(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """BVC - Branch if Overflow Clear"""
        opcode = bytearray.fromhex('28')  # BVC opcode
        # Operand varsa hex'den int'e çevir, yoksa 0
        offset = int(operands[0]['data'], 16) if operands else 0
        # Opcode ve offset'i birleştir
        return opcode + bytearray([offset])

    @staticmethod
    def bvs(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """BVS - Branch if Overflow Set"""
        opcode = bytearray.fromhex('29')  # BVS opcode
        # Operand varsa hex'den int'e çevir, yoksa 0
        offset = int(operands[0]['data'], 16) if operands else 0
        # Opcode ve offset'i birleştir
        return opcode + bytearray([offset])

    @staticmethod
    def cba(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """CBA - Compare Accumulators"""
        opcode = bytearray.fromhex('11')  # CBA opcode
        # A - B karşılaştırması yapar, sonuç flag'larda saklanır
        # Gerçek çıkarma yapılmaz, sadece flag'lar güncellenir
        return opcode

    @staticmethod
    def clc(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """CLC - Clear Carry"""
        opcode = bytearray.fromhex('0C')  # CLC opcode
        registers.SR[0] = False  # Carry flag'ını temizle (bit 0)
        return opcode

    @staticmethod
    def cli(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """CLI - Clear Interrupt Mask"""
        opcode = bytearray.fromhex('0E')  # CLI opcode
        registers.SR[4] = False  # Interrupt mask flag'ını temizle (bit 4)
        return opcode

    @staticmethod
    def clr(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """CLR - Clear"""
        opcode: bytearray = bytearray()  # Boş opcode başlat
        
        # Accumulator mod kontrolü
        if addr_mode == AddressingMode.ACC:
            # A register'ını mı temizliyoruz kontrol et
            if operands[0]['data'] == 'A':
                opcode = bytearray.fromhex('4F')  # CLRA opcode
                registers.AccA = 0  # A register'ını sıfırla
            else:
                opcode = bytearray.fromhex('5F')  # CLRB opcode
                registers.AccB = 0  # B register'ını sıfırla
        
        return opcode

    @staticmethod
    def clv(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """CLV - Clear Overflow"""
        opcode = bytearray.fromhex('0A')  # CLV opcode
        registers.SR[1] = False  # Overflow flag'ını temizle (bit 1)
        return opcode

    @staticmethod
    def cmp(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """CMP - Compare"""
        opcode: bytearray = bytearray()  # Boş opcode başlat
        
        # Immediate (anlık) mod kontrolü
        if addr_mode == AddressingMode.IMM:
            # A register'ıyla mı karşılaştırıyoruz kontrol et
            if operands[-1]['data'] == 'A':
                opcode = bytearray.fromhex('81')  # CMPA immediate opcode
            else:
                opcode = bytearray.fromhex('C1')  # CMPB immediate opcode
        
        return opcode

    @staticmethod
    def com(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """COM - Complement"""
        opcode: bytearray = bytearray()  # Boş opcode başlat
        
        # Accumulator mod kontrolü
        if addr_mode == AddressingMode.ACC:
            # A register'ının mı complement'ini alıyoruz kontrol et
            if operands[0]['data'] == 'A':
                opcode = bytearray.fromhex('43')  # COMA opcode
                # A register'ının tüm bitlerini ters çevir (1'ler complement)
                registers.AccA = ~registers.AccA & 0xFF
            else:
                opcode = bytearray.fromhex('53')  # COMB opcode
                # B register'ının tüm bitlerini ters çevir (1'ler complement)
                registers.AccB = ~registers.AccB & 0xFF
        
        return opcode

    @staticmethod
    def cpx(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """CPX - Compare Index Register"""
        opcode: bytearray = bytearray()  # Boş opcode başlat
        
        # Immediate (anlık) mod kontrolü
        if addr_mode == AddressingMode.IMM:
            opcode = bytearray.fromhex('8C')  # CPX immediate opcode
        # Direct (doğrudan) mod kontrolü
        elif addr_mode == AddressingMode.DIR:
            opcode = bytearray.fromhex('9C')  # CPX direct opcode
        
        return opcode

    @staticmethod
    def daa(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """DAA - Decimal Adjust Accumulator"""
        opcode = bytearray.fromhex('19')  # DAA opcode
        # BCD (Binary Coded Decimal) decimal adjust işlemi
        # BCD aritmetiği sonrası A register'ını düzelt
        return opcode

    @staticmethod
    def dec(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """DEC - Decrement"""
        opcode: bytearray = bytearray()  # Boş opcode başlat
        
        # Accumulator mod kontrolü
        if addr_mode == AddressingMode.ACC:
            # A register'ını mı azaltıyoruz kontrol et
            if operands[0]['data'] == 'A':
                opcode = bytearray.fromhex('4A')  # DECA opcode
                registers.AccA -= 1  # A register'ını 1 azalt
            else:
                opcode = bytearray.fromhex('5A')  # DECB opcode
                registers.AccB -= 1  # B register'ını 1 azalt
        
        return opcode

    @staticmethod
    def des(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """DES - Decrement Stack Pointer"""
        opcode = bytearray.fromhex('34')  # DES opcode
        registers.SP -= 1  # Stack Pointer'ını 1 azalt
        return opcode

    @staticmethod
    def dex(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """DEX - Decrement Index Register"""
        opcode = bytearray.fromhex('09')  # DEX opcode
        registers.X -= 1  # Index Register'ını 1 azalt
        return opcode

    @staticmethod
    def eor(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """EOR - Exclusive OR"""
        opcode: bytearray = bytearray()  # Boş opcode başlat
        
        # Immediate (anlık) mod kontrolü
        if addr_mode == AddressingMode.IMM:
            # A register'ıyla mı XOR yapıyoruz kontrol et
            if operands[-1]['data'] == 'A':
                opcode = bytearray.fromhex('88')  # EORA immediate opcode
            else:
                opcode = bytearray.fromhex('C8')  # EORB immediate opcode
        
        return opcode

    @staticmethod
    def inc(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """INC - Increment"""
        opcode: bytearray = bytearray()  # Boş opcode başlat
        
        # Accumulator mod kontrolü
        if addr_mode == AddressingMode.ACC:
            # A register'ını mı artırıyoruz kontrol et
            if operands[0]['data'] == 'A':
                opcode = bytearray.fromhex('4C')  # INCA opcode
                registers.AccA += 1  # A register'ını 1 artır
            else:
                opcode = bytearray.fromhex('5C')  # INCB opcode
                registers.AccB += 1  # B register'ını 1 artır
        
        return opcode

    @staticmethod
    def ins(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """INS - Increment Stack Pointer"""
        opcode = bytearray.fromhex('31')  # INS opcode
        registers.SP += 1  # Stack Pointer'ını 1 artır
        return opcode

    @staticmethod
    def inx(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """INX - Increment Index Register"""
        opcode = bytearray.fromhex('08')  # INX opcode
        registers.X += 1  # Index Register'ını 1 artır
        return opcode

    @staticmethod
    def jmp(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """JMP - Jump"""
        opcode: bytearray = bytearray()  # Boş opcode başlat
        
        # Extended (genişletilmiş) mod kontrolü
        if addr_mode == AddressingMode.EXT:
            opcode = bytearray.fromhex('7E')  # JMP extended opcode
        # Indexed (indeksli) mod kontrolü
        elif addr_mode == AddressingMode.IND:
            opcode = bytearray.fromhex('6E')  # JMP indexed opcode
        
        return opcode

    @staticmethod
    def jsr(addr_mode: AddressingMode,
            operands: Deque[yylex_t],
            registers: Register_T) -> bytearray:
        """JSR - Jump to Subroutine"""
        opcode: bytearray = bytearray()  # Boş opcode başlat

        if addr_mode == AddressingMode.EXT:
            opcode = bytearray.fromhex('BD')  # JSR extended - Genişletilmiş adresleme ile alt yordam çağırma
        elif addr_mode == AddressingMode.IND:
            opcode = bytearray.fromhex('AD')  # JSR indexed - İndeksli adresleme ile alt yordam çağırma

        return opcode

@staticmethod
def lda(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """LDA - Load Accumulator A - A akümülatörüne veri yükle"""
    opcode: bytearray = bytearray()
    
    if addr_mode == AddressingMode.IMM:
        opcode = bytearray.fromhex('86')  # LDA immediate - Doğrudan değer ile A'ya yükle
        operand = int(Parser.parse_immediate_value(operands[0]['data']).hex(), 16)
        registers.AccA = operand  # A register'ına değeri ata
    elif addr_mode == AddressingMode.DIR:
        opcode = bytearray.fromhex('96')  # LDA direct - Doğrudan adresleme ile A'ya yükle
    elif addr_mode == AddressingMode.EXT:
        opcode = bytearray.fromhex('B6')  # LDA extended - Genişletilmiş adresleme ile A'ya yükle
    
    return opcode

@staticmethod
def ldb(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """LDB - Load Accumulator B - B akümülatörüne veri yükle"""
    opcode: bytearray = bytearray()
    
    if addr_mode == AddressingMode.IMM:
        opcode = bytearray.fromhex('C6')  # LDB immediate - Doğrudan değer ile B'ye yükle
        operand = int(Parser.parse_immediate_value(operands[0]['data']).hex(), 16)
        registers.AccB = operand  # B register'ına değeri ata
    elif addr_mode == AddressingMode.DIR:
        opcode = bytearray.fromhex('D6')  # LDB direct - Doğrudan adresleme ile B'ye yükle
    elif addr_mode == AddressingMode.EXT:
        opcode = bytearray.fromhex('F6')  # LDB extended - Genişletilmiş adresleme ile B'ye yükle
    
    return opcode

@staticmethod
def lds(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """LDS - Load Stack Pointer - Stack pointer'a değer yükle"""
    opcode: bytearray = bytearray()
    
    if addr_mode == AddressingMode.IMM:
        opcode = bytearray.fromhex('8E')  # LDS immediate - Doğrudan değer ile SP'ye yükle
    elif addr_mode == AddressingMode.DIR:
        opcode = bytearray.fromhex('9E')  # LDS direct - Doğrudan adresleme ile SP'ye yükle
    
    return opcode

@staticmethod
def ldx(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """LDX - Load Index Register - X index register'ına değer yükle"""
    opcode: bytearray = bytearray()
    
    if addr_mode == AddressingMode.IMM:
        opcode = bytearray.fromhex('CE')  # LDX immediate - Doğrudan değer ile X'e yükle
    elif addr_mode == AddressingMode.DIR:
        opcode = bytearray.fromhex('DE')  # LDX direct - Doğrudan adresleme ile X'e yükle
    
    return opcode

@staticmethod
def lsr(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """LSR - Logical Shift Right - Mantıksal sağa kaydırma"""
    opcode: bytearray = bytearray()
    
    if addr_mode == AddressingMode.ACC:
        if operands[0]['data'] == 'A':
            opcode = bytearray.fromhex('44')  # LSRA - A register'ını sağa kaydır
            registers.AccA >>= 1  # A'yı bir bit sağa kaydır
        else:
            opcode = bytearray.fromhex('54')  # LSRB - B register'ını sağa kaydır
            registers.AccB >>= 1  # B'yi bir bit sağa kaydır
    
    return opcode

@staticmethod
def neg(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """NEG - Negate - İki'nin tümleyenini al (negatif değer)"""
    opcode: bytearray = bytearray()
    
    if addr_mode == AddressingMode.ACC:
        if operands[0]['data'] == 'A':
            opcode = bytearray.fromhex('40')  # NEGA - A register'ının negatifini al
            registers.AccA = (-registers.AccA) & 0xFF  # A = -A (8-bit sınırında)
        else:
            opcode = bytearray.fromhex('50')  # NEGB - B register'ının negatifini al
            registers.AccB = (-registers.AccB) & 0xFF  # B = -B (8-bit sınırında)
    
    return opcode

@staticmethod
def nop(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """NOP - No Operation - Hiçbir işlem yapma (bekle)"""
    return bytearray.fromhex('01')  # NOP opcode'u

@staticmethod
def ora(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """ORA - Inclusive OR - Mantıksal VEYA işlemi"""
    opcode: bytearray = bytearray()
    
    if addr_mode == AddressingMode.IMM:
        if operands[-1]['data'] == 'A':
            opcode = bytearray.fromhex('8A')  # ORAA immediate - A register'ı ile VEYA
        else:
            opcode = bytearray.fromhex('CA')  # ORAB immediate - B register'ı ile VEYA
    
    return opcode

@staticmethod
def psh(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """PSH - Push - Register'ı stack'e pushla"""
    opcode: bytearray = bytearray()
    
    if operands[0]['data'] == 'A':
        opcode = bytearray.fromhex('36')  # PSHA - A register'ını stack'e pushla
    else:
        opcode = bytearray.fromhex('37')  # PSHB - B register'ını stack'e pushla
    
    return opcode

@staticmethod
def pul(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """PUL - Pull - Stack'ten register'a veri çek"""
    opcode: bytearray = bytearray()
    
    if operands[0]['data'] == 'A':
        opcode = bytearray.fromhex('32')  # PULA - Stack'ten A register'ına çek
    else:
        opcode = bytearray.fromhex('33')  # PULB - Stack'ten B register'ına çek
    
    return opcode

@staticmethod
def rol(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """ROL - Rotate Left - Carry flag ile birlikte sola döndür"""
    opcode: bytearray = bytearray()
    
    if addr_mode == AddressingMode.ACC:
        if operands[0]['data'] == 'A':
            opcode = bytearray.fromhex('49')  # ROLA - A register'ını sola döndür
            # Carry flag ile birlikte sola kaydırma işlemi
            carry = (registers.AccA & 0x80) >> 7  # En üst bit = yeni carry
            registers.AccA = ((registers.AccA << 1) | registers.SR[0]) & 0xFF  # Sola kaydır + eski carry
            registers.SR[0] = carry  # Yeni carry flag'ını set et
        else:
            opcode = bytearray.fromhex('59')  # ROLB - B register'ını sola döndür
            carry = (registers.AccB & 0x80) >> 7  # En üst bit = yeni carry
            registers.AccB = ((registers.AccB << 1) | registers.SR[0]) & 0xFF  # Sola kaydır + eski carry
            registers.SR[0] = carry  # Yeni carry flag'ını set et
    
    return opcode

@staticmethod
def ror(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """ROR - Rotate Right - Carry flag ile birlikte sağa döndür"""
    opcode: bytearray = bytearray()
    
    if addr_mode == AddressingMode.ACC:
        if operands[0]['data'] == 'A':
            opcode = bytearray.fromhex('46')  # RORA - A register'ını sağa döndür
            # Carry flag ile birlikte sağa kaydırma işlemi
            carry = registers.AccA & 0x01  # En alt bit = yeni carry
            registers.AccA = (registers.AccA >> 1) | (registers.SR[0] << 7)  # Sağa kaydır + eski carry
            registers.SR[0] = carry  # Yeni carry flag'ını set et
        else:
            opcode = bytearray.fromhex('56')  # RORB - B register'ını sağa döndür
            carry = registers.AccB & 0x01  # En alt bit = yeni carry
            registers.AccB = (registers.AccB >> 1) | (registers.SR[0] << 7)  # Sağa kaydır + eski carry
            registers.SR[0] = carry  # Yeni carry flag'ını set et
    
    return opcode

@staticmethod
def rti(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """RTI - Return from Interrupt - Interrupt'tan dön"""
    opcode = bytearray.fromhex('3B')
    # Stack'ten register'ları geri yükle
    # Sıralama: CCR, B, A, XH, XL, PCH, PCL
    return opcode

@staticmethod
def rts(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """RTS - Return from Subroutine - Alt yordamdan dön"""
    opcode = bytearray.fromhex('39')
    # Stack'ten return address'i çek ve PC'ye yükle
    return opcode

@staticmethod
def sba(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """SBA - Subtract Accumulator B from A - A'dan B'yi çıkar"""
    opcode = bytearray.fromhex('10')
    # A = A - B işlemi
    registers.AccA -= registers.AccB
    return opcode

@staticmethod
def sbc(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """SBC - Subtract with Carry - Carry ile birlikte çıkarma"""
    opcode: bytearray = bytearray()
    
    if addr_mode == AddressingMode.IMM:
        if operands[-1]['data'] == 'A':
            opcode = bytearray.fromhex('82')  # SBCA immediate - A'dan carry ile çıkar
        else:
            opcode = bytearray.fromhex('C2')  # SBCB immediate - B'den carry ile çıkar
        
        # A = A - M - C formülü (M: operand, C: carry flag)
        operand = int(Parser.parse_immediate_value(operands[0]['data']).hex(), 16)
        if operands[-1]['data'] == 'A':
            registers.AccA = registers.AccA - operand - registers.SR[0]  # A - operand - carry
        else:
            registers.AccB = registers.AccB - operand - registers.SR[0]  # B - operand - carry
    
    return opcode

@staticmethod
def sec(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """SEC - Set Carry - Carry flag'ını set et"""
    opcode = bytearray.fromhex('0D')
    registers.SR[0] = True  # Carry flag'ını 1 yap
    return opcode

@staticmethod
def sei(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """SEI - Set Interrupt Mask - Interrupt mask flag'ını set et"""
    opcode = bytearray.fromhex('0F')
    registers.SR[4] = True  # Interrupt mask flag'ını 1 yap (interrupt'ları devre dışı bırak)
    return opcode

@staticmethod
def sev(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """SEV - Set Overflow - Overflow flag'ını set et"""
    opcode = bytearray.fromhex('0B')
    registers.SR[1] = True  # Overflow flag'ını 1 yap
    return opcode

@staticmethod
def sta(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """STA - Store Accumulator A - A register'ının değerini belleğe kaydet"""
    opcode: bytearray = bytearray()
    
    if addr_mode == AddressingMode.DIR:
        opcode = bytearray.fromhex('97')  # STA direct - Doğrudan adresleme ile kaydet
    elif addr_mode == AddressingMode.EXT:
        opcode = bytearray.fromhex('B7')  # STA extended - Genişletilmiş adresleme ile kaydet
    elif addr_mode == AddressingMode.IND:
        opcode = bytearray.fromhex('A7')  # STA indexed - İndeksli adresleme ile kaydet
    
    return opcode

@staticmethod
def stb(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """STB - Store Accumulator B - B register'ının değerini belleğe kaydet"""
    opcode: bytearray = bytearray()
    
    if addr_mode == AddressingMode.DIR:
        opcode = bytearray.fromhex('D7')  # STB direct - Doğrudan adresleme ile kaydet
    elif addr_mode == AddressingMode.EXT:
        opcode = bytearray.fromhex('F7')  # STB extended - Genişletilmiş adresleme ile kaydet
    elif addr_mode == AddressingMode.IND:
        opcode = bytearray.fromhex('E7')  # STB indexed - İndeksli adresleme ile kaydet
    
    return opcode

@staticmethod
def sts(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """STS - Store Stack Pointer - Stack pointer'ın değerini belleğe kaydet"""
    opcode: bytearray = bytearray()
    
    if addr_mode == AddressingMode.DIR:
        opcode = bytearray.fromhex('9F')  # STS direct - Doğrudan adresleme ile kaydet
    elif addr_mode == AddressingMode.EXT:
        opcode = bytearray.fromhex('BF')  # STS extended - Genişletilmiş adresleme ile kaydet
    
    return opcode

@staticmethod
def stx(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """STX - Store Index Register - X register'ının değerini belleğe kaydet"""
    opcode: bytearray = bytearray()
    
    if addr_mode == AddressingMode.DIR:
        opcode = bytearray.fromhex('DF')  # STX direct - Doğrudan adresleme ile kaydet
    elif addr_mode == AddressingMode.EXT:
        opcode = bytearray.fromhex('FF')  # STX extended - Genişletilmiş adresleme ile kaydet
    
    return opcode

@staticmethod
def sub(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """SUB - Subtract - Çıkarma işlemi"""
    opcode: bytearray = bytearray()
    
    if addr_mode == AddressingMode.IMM:
        if operands[-1]['data'] == 'A':
            opcode = bytearray.fromhex('80')  # SUBA immediate - A'dan doğrudan değer çıkar
            operand = int(Parser.parse_immediate_value(operands[0]['data']).hex(), 16)
            registers.AccA -= operand  # A = A - operand
        else:
            opcode = bytearray.fromhex('C0')  # SUBB immediate - B'den doğrudan değer çıkar
            operand = int(Parser.parse_immediate_value(operands[0]['data']).hex(), 16)
            registers.AccB -= operand  # B = B - operand
    elif addr_mode == AddressingMode.DIR:
        if operands[-1]['data'] == 'A':
            opcode = bytearray.fromhex('90')  # SUBA direct - A'dan bellek değeri çıkar
        else:
            opcode = bytearray.fromhex('D0')  # SUBB direct - B'den bellek değeri çıkar
    
    return opcode

@staticmethod
def swi(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """SWI - Software Interrupt - Yazılım interrupt'ı"""
    opcode = bytearray.fromhex('3F')
    # Tüm register'ları stack'e push et ve interrupt vector'a jump et
    return opcode

@staticmethod
def tab(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """TAB - Transfer A to B - A register'ının değerini B'ye kopyala"""
    opcode = bytearray.fromhex('16')
    registers.AccB = registers.AccA  # B = A
    return opcode

@staticmethod
def tap(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """TAP - Transfer A to Condition Codes - A register'ının değerini CCR'ye transfer et"""
    opcode = bytearray.fromhex('06')
    # A register'ının her bitini CCR flag'larına aktar
    for i in range(8):
        registers.SR[i] = bool((registers.AccA >> i) & 1)
    return opcode

@staticmethod
def tba(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """TBA - Transfer B to A - B register'ının değerini A'ya kopyala"""
    opcode = bytearray.fromhex('17')
    registers.AccA = registers.AccB  # A = B
    return opcode

@staticmethod
def tpa(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """TPA - Transfer Condition Codes to A - CCR flag'larını A register'ına transfer et"""
    opcode = bytearray.fromhex('07')
    # CCR'nin değerini A register'ına transfer et
    registers.AccA = 0
    for i in range(8):
        if registers.SR[i]:  # Eğer flag set ise
            registers.AccA |= (1 << i)  # İlgili biti A'da set et
    return opcode

@staticmethod
def tst(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """TST - Test - Register'ı test et (0 ile karşılaştır)"""
    opcode: bytearray = bytearray()
    
    if addr_mode == AddressingMode.ACC:
        if operands[0]['data'] == 'A':
            opcode = bytearray.fromhex('4D')  # TSTA - A register'ını test et
            # A register'ını test et (A - 0 işlemi, sadece flag'lar etkilenir)
        else:
            opcode = bytearray.fromhex('5D')  # TSTB - B register'ını test et
            # B register'ını test et (B - 0 işlemi, sadece flag'lar etkilenir)
    
    return opcode

@staticmethod
def tsx(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """TSX - Transfer Stack Pointer to X - Stack pointer'ı X register'ına transfer et"""
    opcode = bytearray.fromhex('30')
    registers.X = registers.SP + 1  # X = SP + 1 (MC6800'ün özelliği)
    return opcode

@staticmethod
def txs(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """TXS - Transfer X to Stack Pointer - X register'ını stack pointer'a transfer et"""
    opcode = bytearray.fromhex('35')
    registers.SP = registers.X - 1  # SP = X - 1 (MC6800'ün özelliği)
    return opcode

@staticmethod
def wai(addr_mode: AddressingMode,
        operands: Deque[yylex_t],
        registers: Register_T) -> bytearray:
    """WAI - Wait for Interrupt - Interrupt bekle"""
    opcode = bytearray.fromhex('3E')
    # Tüm register'ları stack'e push et ve interrupt gelene kadar bekle
    return opcode