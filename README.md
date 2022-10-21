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
