#### **Implementační dokumentace k 2. úloze do IPP 2021/2022**
#### **Jméno a příjmení: Radek Šerejch**
#### **Login: xserej00**
## interpret.py
###### způsob řešení:
Pro zpracování argumentů jsem si naimplementoval třídu Argument. Metoda init projde každý prvek v argv, a zjistí zda to není některý z podporovaných. Pokud je to --source nebo --input, uloží jejich hodnotu. Dále následuje kontrola, zda je zadán aspoň jeden z těchto argumentů, aby mohl být případně druhý soubor načten ze stdin. Dále podle zadaných argumentů přečtu kořenový prvek xml souboru. Potom kontroluji základní tagy, atributy a argumenty. Potom jsem se rozhodl, že by bylo vhodné si pro uložení jednotlivých instrukcí a argumentů vytvořit pro ně třídy _Instruction_ a _Arg_. Následně procházím instrukce, vytvořím instanci třídy, naplním argumenty a přidám instrukci do slovníku. Celé provádění programu se pak děje v metodě init třídy _Execute_
###### třída _Instruction_:
Metoda init uloží do proměnných třídy operační kód instrukce, její order, a deklaruje prázdné pole argumentů. Metoda add_argument následně plní toto pole instancemi třídy _Arg_, které předávám typ argumentu a jeho hodnotu. Metoda add_to_dir přidá instrukci do slovníku uloženého přímo ve třídě. Klíčem bude Order instrukce, a data operační kód a list argumentů. Dále třída obsahuje pomocné gettry
###### třída _Arg_:
Metoda init uloží typ a hodnotu argumentu, dále třída obsahuje pomocné gettry
###### třída _Execute_:
Metoda init nejprve inicializuje instanci třídy _Lists_ a _Variable_. Dále probíhá provádění jendotlivých instrukcí, ke kterým se přistupuje na základě jejich orderu, který se vezme z pole orderů na příslušném indexu, podle pozice programu. Dále třída obsahuje metodu pro kontrolu proměnné. Nejprve se provádí kontrola typu argumentu, potom případná kontrola rámce, a až poté samotná kontrola definice, tudíž návratový kód _53_ má přednost před _55_, a ten zase před _54_. Dále třída obsahuje metody pro kontrolu argumentů jednotlivých funkcí, metodu pro výpis dat, a metodu pro kontrolu inicializace proměnné
###### třída _Lists_:
Metoda init projde všechny instrukce a naplní pole orderů a slovník labelů, pro který je klíčem název labelu, a do dat uložím příslušný order. Nakonec seřadí pole orderů pro správný průchod programem. Třída dále obsahuje pomocné gettry na pole, které jsou uloženy přímo v třídě
###### třída _Variable_:
Metoda init nainicializuje prázdný globální, lokální a dočasný rámec. Dále třída obsahuje metody pro definici proměnné na příslušném rámci, přidání hodnoty do danné proměnné, vytvoření, pushnutí a popnutí rámce, kontrolu definice proměnné a pomocné gettry
## test.php
###### způsob řešení:
Nejprve zpracovávám argumenty pomocí funkce getopt, která mi vytvoří pole podporovaných argumentů. Následně si vytvořím instanci třídy Argument, do které uložím hodnoty argumentů, nebo příznaky jejich zadání. Dále pomocí metody get_files třídy Loader načtu soubory ze zadaného adresáře. Metoda get_tests následně vytvoří slovník testů, pro který je klíčem relativní cesta ze zadaného adresáře a jeho jméno. Data obsahují jméno a cestu k souboru, a příznaky existence jednotlivých souborů potřebných pro spuštění testu. Následně pomocí metody test_test třídy Tests otestuji každý test, zda obsahuje potřebné soubory, popřípadě je dogeneruji. Dále spustím požadované testy metodou run_test, a výsledek uložím do instance třídy test_result. Tyto výsledky následně tisknu do html souboru pomocí metody create_html třídy generate_html.
###### třída _Argument_:
třída obsahuje data podporovaných argumentů, a pomocné metody pro jejich nastavení
###### třída _test_result_:
třída pro uložení dat celého testu(data jednotlivých testů, cestu k souborům, a celkový výsledek testu)
###### třída _test_result_:
třída pro uložení dat části testu - parser nebo interpret (očekávaný návratový kód, reálný návratový kód, cestu a výsledek testu)
###### třída _Tests_:
třída obsahuje cestu k tesstu, jeho jméno a příznaky existence jednotlivých souborů potřbných k testu. Metoda __construct nastací cestu a jméno při vytvoření testu. Metody set_src, set_in, set_out, set_rc pak nastavují příznaky souborů. Metoda test_test zkontroluje, zda má daný test src sooubor, pokud ne, test je neplatný. Pokud nemá nějaký jiný soubor, dogeneruje ho. Metody run_int_test a run_parse_test provedou test jednotlivých skriptů a uloží výsledky testu do instance třídy partial_result. Metoda run_test je metoda pro provedení provedení testu, která volá podle zadaných argumentů metody na provádění jednotlivých testů, případně odstraní pomocné soubory, a uloží celkový výsledek testu.
###### třída _Loader_:
Metoda get_files rekurzivně prohledá podadresáře zadaného adresáře a uloží všechny soubory pomocí funkce pathinfo. Metoda get_tests prochází soubory z pole, a ukládá je do slovníku testů. Pokud již test existuje, nastavím mu příznak podle koncovky aktuálního souboru.
###### třída _generate_html_:
Metoda create_html nejprve vytvoří hlavičku, kam vloží počet úspěšných, neúspěšných a celkový počet testů, následně vkládá postupně testy pomocí metody generate_tests, podle toho zda byly úspěšné, a nakonec uzavře soubot pomocí metody generate_bottom