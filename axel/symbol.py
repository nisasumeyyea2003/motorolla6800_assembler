

# Tip tanımlamaları için gerekli modül
from typing import Union, Dict, Tuple, TypeVar

# TypeVar'lar - kendi sınıflarımızı bound olarak kullanarak tür güvenliği sağlıyoruz
X = TypeVar('X', bound='U_Int8')    # U_Int8 sınıfı için tür değişkeni
Y = TypeVar('Y', bound='Int8')      # Int8 sınıfı için tür değişkeni  
M = TypeVar('M', bound='U_Int16')   # U_Int16 sınıfı için tür değişkeni


class U_Int8:
    """8-bit işaretsiz tamsayı davranışını simüle eden sınıf.
    
    Bu sınıf, 8-bit mikroişlemcilerdeki işaretsiz byte değerlerini temsil eder.
    Taşma (overflow) ve elde (carry) verilerini ham sayısal detaylarla birlikte tutar.
    
    Normal sayısal türler üzerinde kullanımı kolay operatörler sağlar ve
    sonucu işaretsiz türe dönüştürür.
    """
    
    def __init__(self, num: int) -> None:
        """U_Int8 nesnesini başlatır.
        
        Args:
            num: Başlangıç değeri (herhangi bir integer)
        """
        self.raw = num              # Ham değer - taşma bilgisi için saklanır
        self.num = num & 255        # 8-bit maske (0-255 arası) uygulanmış değer

    def __repr__(self) -> str:
        """Nesnenin string temsilini döndürür."""
        return str(self.num)

    def __add__(self, of: int) -> int:
        """Toplama operatörü (+).
        
        Normal Python integer'ı ile toplama yapar ve sonucu 8-bit'e sınırlar.
        Bu operatör nesneyi değiştirmez, sadece sonucu döndürür.
        
        Args:
            of: Eklenecek değer
            
        Returns:
            8-bit sınırları içinde toplama sonucu
        """
        self.raw += of              # Ham değeri güncelle (taşma takibi için)
        return (self.num + of) & 255    # 8-bit maske uygulanmış sonuç

    def __iadd__(self: X, of: int) -> X:
        """Yerinde toplama operatörü (+=).
        
        Nesnenin kendisini değiştirir ve kendisini döndürür.
        
        Args:
            of: Eklenecek değer
            
        Returns:
            Güncellenmiş nesnenin kendisi
        """
        self.raw += of              # Ham değeri güncelle
        self.num = (self.num + of) & 255    # Maskelenmiş değeri güncelle
        return self

    def __sub__(self, of: int) -> int:
        """Çıkarma operatörü (-).
        
        Normal Python integer'dan çıkarma yapar ve sonucu 8-bit'e sınırlar.
        
        Args:
            of: Çıkarılacak değer
            
        Returns:
            8-bit sınırları içinde çıkarma sonucu
        """
        self.raw -= of              # Ham değeri güncelle
        return (self.num - of) & 255    # 8-bit maske uygulanmış sonuç

    def __isub__(self: X, of: int) -> X:
        """Yerinde çıkarma operatörü (-=).
        
        Args:
            of: Çıkarılacak değer
            
        Returns:
            Güncellenmiş nesnenin kendisi
        """
        self.raw -= of              # Ham değeri güncelle
        self.num = (self.num - of) & 255    # Maskelenmiş değeri güncelle
        return self


class Int8:
    """8-bit işaretli tamsayı davranışını simüle eden sınıf.
    
    Bu sınıf, 8-bit mikroişlemcilerdeki işaretli byte değerlerini temsil eder.
    2'nin tümleyeni (2's complement) ile işaretli aritmetik sağlar.
    
    Normal sayısal türler üzerinde kullanımı kolay operatörler sağlar ve
    sonucu 2'nin tümleyeni ile işaretli türe dönüştürür.
    """
    
    def __init__(self, num: int) -> None:
        """Int8 nesnesini başlatır.
        
        Args:
            num: Başlangıç değeri
        """
        self.num = self._to_int8(num)   # Değeri 8-bit işaretli forma dönüştür

    def _to_int8(self, num: int) -> int:
        """Bir sayıyı 8-bit işaretli tamsayıya (2's complement) dönüştürür.
        
        8-bit işaretli sayılar -128 ile +127 arasında değer alır.
        En yüksek bit (bit 7) işaret bitidir.
        
        Args:
            num: Dönüştürülecek sayı
            
        Returns:
            8-bit işaretli tamsayı değeri
        """
        mask7 = 128     # 10000000 - 7. bit maskesi (işaret biti)
        mask2s = 127    # 01111111 - 2'nin tümleyeni için maske
        
        # Eğer işaret biti set ise (negatif sayı)
        if (mask7 & num == 128):
            # 2'nin tümleyenini uygula: NOT işlemi + 1, sonra negatif yap
            num = -((~int(num) + 1) & mask2s)
        return num

    def __repr__(self) -> str:
        """Nesnenin string temsilini döndürür."""
        return str(self.num)

    def __add__(self, of: int) -> int:
        """Toplama operatörü (+).
        
        Args:
            of: Eklenecek değer
            
        Returns:
            8-bit işaretli sınırlar içinde toplama sonucu
        """
        return self._to_int8(self.num + of)

    def __iadd__(self: Y, of: int) -> Y:
        """Yerinde toplama operatörü (+=).
        
        Args:
            of: Eklenecek değer
            
        Returns:
            Güncellenmiş nesnenin kendisi
        """
        self.num = self._to_int8(self.num + of)
        return self

    def __sub__(self, of: int) -> int:
        """Çıkarma operatörü (-).
        
        Args:
            of: Çıkarılacak değer
            
        Returns:
            8-bit işaretli sınırlar içinde çıkarma sonucu
        """
        return self._to_int8(self.num - of)

    def __isub__(self: Y, of: int) -> Y:
        """Yerinde çıkarma operatörü (-=).
        
        Args:
            of: Çıkarılacak değer
            
        Returns:
            Güncellenmiş nesnenin kendisi
        """
        self.num = self._to_int8(self.num - of)
        return self


class U_Int16:
    """16-bit işaretsiz tamsayı davranışını simüle eden sınıf.
    
    NOT: Sınıf yorumunda "18bit" yazıyor ama aslında 16-bit (0-65535 arası).
    Bu muhtemelen bir yazım hatası.
    
    Bu sınıf, 16-bit mikroişlemci adreslerini ve büyük değerleri temsil eder.
    Normal sayısal türler üzerinde kullanımı kolay operatörler sağlar ve
    sonucu işaretsiz türe dönüştürür.
    """
    
    def __init__(self, num: int) -> None:
        """U_Int16 nesnesini başlatır.
        
        Args:
            num: Başlangıç değeri
        """
        self.num = num & 65535      # 16-bit maske (0-65535 arası)

    def __repr__(self) -> str:
        """Nesnenin string temsilini döndürür."""
        return str(self.num)

    def __add__(self, of: int) -> int:
        """Toplama operatörü (+).
        
        Args:
            of: Eklenecek değer
            
        Returns:
            16-bit sınırları içinde toplama sonucu
        """
        return (self.num + of) & 65535

    def __iadd__(self: M, of: int) -> M:
        """Yerinde toplama operatörü (+=).
        
        Args:
            of: Eklenecek değer
            
        Returns:
            Güncellenmiş nesnenin kendisi
        """
        self.num = (self.num + of) & 65535
        return self

    def __sub__(self, of: int) -> int:
        """Çıkarma operatörü (-).
        
        Args:
            of: Çıkarılacak değer
            
        Returns:
            16-bit sınırları içinde çıkarma sonucu
        """
        return (self.num - of) & 65535

    def __isub__(self: M, of: int) -> M:
        """Yerinde çıkarma operatörü (-=).
        
        Args:
            of: Çıkarılacak değer
            
        Returns:
            Güncellenmiş nesnenin kendisi
        """
        self.num = (self.num - of) & 65535
        return self


# Sembol tablosu alan tipinin tanımı
# Her alan: (adres, tip, değer) şeklinde tuple
TableField_T = Tuple[U_Int16, str, Union[U_Int16, str, bytes]]


class Symbol_Table:
    """Assembler Sembol Tablosu.
    
    6800 mikroişlemci programlarındaki etiketler (labels) veya değişkenler
    ve bunların bellekteki konumu, tipi ve verilerini tutan sembol tablosu.
    
    Assembler'da kullanılan sembolik isimler (örn: LOOP1, DATA_START) 
    gerçek bellek adreslerine çevrilirken bu tablo kullanılır.
    """
    
    def __init__(self) -> None:
        """Sembol tablosunu başlatır."""
        # Sembol adından tablo alanına eşleme
        # Anahtar: sembol adı (string)
        # Değer: (adres, tip, değer) tuple'ı
        self.table: Dict[str, TableField_T] = {}

    def set(self,
            label: str,
            addr: U_Int16,
            type: str,
            value: Union[U_Int16, str, bytes]) -> None:
        """Bir etiket veya değişken için tablo girişi ayarlar.
        
        Args:
            label: Sembol adı (örn: "LOOP1", "DATA_START")
            addr: Bellekteki adresi (16-bit)
            type: Sembol tipi (örn: "LABEL", "VARIABLE", "CONSTANT")
            value: Sembol değeri (sayı, string veya byte verisi olabilir)
        """
        self.table[label] = (addr, type, value)

    def get(self, label: str) -> TableField_T:
        """Bir etiket veya değişken için tablo girişini getirir.
        
        Args:
            label: Aranacak sembol adı
            
        Returns:
            (adres, tip, değer) tuple'ı
            
        Raises:
            KeyError: Eğer sembol tabloda bulunamazsa
        """
        return self.table[label]