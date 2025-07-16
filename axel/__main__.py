# Gerekli modülleri import ediyoruz
from axel.lexer import Lexer      # Lexical analysis (sözcüksel analiz) için
from axel.parser import Parser    # Syntax analysis (sözdizimsel analiz) için
from gui import launch_gui  # Eğer ImportError alırsan, sys.path ile yolu ekleyebiliriz

# Assembly kaynak dosyasını okuyoruz
with open('./etc/healthkit.asm') as f:
    source = f.read()  # Dosya içeriğini string olarak alıyoruz
    
    # ADIM 1: LEXICAL ANALYSIS (Sözcüksel Analiz)
    # Assembly kodunu token'lara (sözcüklere) ayırıyoruz
    test = Lexer(source)
    
    # Tüm token'ları işliyoruz (lexer iterator olarak çalışıyor)
    for token in test:
        pass  # Şimdilik token'ları sadece işliyoruz, yazdırmıyoruz
    
    # ADIM 2: SYNTAX ANALYSIS (Sözdizimsel Analiz)
    # Lexer'dan elde edilen token'ları ve sembolleri kullanarak parser oluşturuyoruz
    test2 = Parser(source, test.symbols)
    
    # Parser'dan ilk satırı alıyoruz
    line = test2.line()
    
    # ADIM 3: ASSEMBLY KOMUTLARINI İŞLEME VE ÇIKTI ALMA
    print('\nInstructions:')  # Komutlar başlığı
    
    # Tüm satırları işleyene kadar devam ediyoruz
    while line:
        # Eğer satır boolean değilse (yani gerçek bir komut/veri ise)
        if not isinstance(line, bool):
            print(line)  # Komut/veriyi yazdırıyoruz
        
        # Bir sonraki satırı al
        line = test2.line()
    
    # ADIM 4: SEMBOL TABLOSUNU YAZDIRMA
    # Assembly kodunda tanımlanan etiketler, değişkenler vs.
    print('\nSymbols:\n', test2.symbols.table)
    
    # Parsed instructions ve symbol table'ı GUI'ye aktarmak için hazırlıyoruz
    parsed_instructions = test2.instructions if hasattr(test2, 'instructions') else []
    symbol_table = test2.symbols.table

    # Burada GUI çağrısını yapıyoruz:
    launch_gui(parsed_instructions, symbol_table)