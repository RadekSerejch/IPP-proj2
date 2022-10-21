import sys
import xml.etree.ElementTree as ET
import re


# třída pro zpracování argumentů
class Argument:
    def __init__(self):
        self.source = ""
        self.input = None
        argv = sys.argv[1:]
        self.source_count = 0
        self.input_count = 0
        # pro každý argument zkontroluj, zda je to nějaký z poporovaných
        for i in argv:
            if i == "--help":
                if len(argv) > 1:
                    sys.stderr.write("help cannot be combined with other arguments")
                    exit(10)
                print("--source=file vstupní soubor s XML reprezentací zdrojového kódu ")
                print("--input=file soubor se vstupy pro samotnou interpretaci zadaného zdrojového kódu")
                exit(0)
            elif i[0:9] == "--source=":
                self.source_count += 1
                self.source = i[9:]
            elif i[0:8] == "--input=":
                self.input_count += 1
                self.input = i[8:]
            else:
                print("wrong parameter, try using --help")
        if self.input_count == 0 and self.source_count == 0:
            print("no source or input given")
            exit(10)

    # metody pro vracení hodnot
    def get_source(self):
        return self.source

    def get_input(self):
        return self.input

    def get_source_count(self):
        return self.source_count

    def get_input_count(self):
        return self.input_count


# třída pro argumenty
class Arg:
    def __init__(self, arg_type, value):
        self.type = arg_type
        self.value = value

    def get_type(self):
        return self.type

    def get_value(self):
        return self.value


# třída pro instrikce, obsahuje slovník jejích instancí
class Instruction:
    instruction_dict = {}

    def __init__(self, opcode, order):
        self.opcode = opcode
        self.order = order
        self.args_list = []

    # metoda pro přidání argumentu do danné instrukce
    def add_argument(self, arg_type, value):
        self.args_list.append(Arg(arg_type, value))

    # metoda pro přidání instrukce do slovníku
    def add_to_dir(self):
        self.instruction_dict[self.order] = self.opcode, self.args_list

    # pomocné gettry
    def get_dict(self):
        return self.instruction_dict

    def get_instruction(self, order):
        return self.instruction_dict[order]


# třída pro pomocné seznamy labelů a orderů
class Lists:
    label_dict = {}
    order_list = []

    def __init__(self, ins_root):
        # pro každou instrukci se zkontroluje zda není label
        for ins in ins_root:
            # list labelů
            if ins.attrib["opcode"] == "LABEL":
                # kontrola typu
                if list(ins)[0].attrib["type"] != "label":
                    sys.stderr.write("label type not label")
                    exit(52)
                # kontrola redefinice
                if list(ins)[0].text not in self.label_dict:
                    self.label_dict[list(ins)[0].text] = ins.attrib["order"]
                else:
                    sys.stderr.write("label redefinition")
                    exit(52)
            # list orderů
            # kontrola duplicity orderů
            if ins.attrib["order"] not in self.order_list:
                self.order_list.append(ins.attrib["order"])
            else:
                sys.stderr.write("order duplicity")
                exit(52)
        # seřazení listu orderů pro správný průchod programu
        self.order_list.sort(key=int)

    # pomocné gettery
    def get_labels(self):
        return self.label_dict

    def get_orders(self):
        return self.order_list


# třída pro ukládání proměnných
class Variable:
    # rámce
    var_dict_global = {}
    var_dict_temp = {}
    var_stack_local = []
    # příznaky definic
    temp_def = False

    # počáteční inicializace
    def __init__(self):
        self.var_dict_temp = {}

    # metoda pro inicializování proměnné
    def init_var(self, name, frame):
        name = name[3:]
        # ukládání na dočasný rámec
        if frame == "TF":
            # kontrola duplicity jmen
            if name in self.var_dict_temp:
                sys.stderr.write("duplicit var name\n")
                exit(52)
            # kontrola definice rámce
            if not self.temp_def:
                sys.stderr.write("TF not defined\n")
                exit(55)
            # definice proměnné
            self.var_dict_temp[name] = [None, None]
        # ukládání na globální rámec
        elif frame == "GF":
            # kontrola duplicity jmen
            if name in self.var_dict_global:
                sys.stderr.write("duplicit var name\n")
                exit(52)
            # definice proměnné
            self.var_dict_global[name] = [None, None]
        # ukládání na lokální rámec
        elif frame == "LF":
            # kontrola definice rámce
            if not self.var_stack_local:
                sys.stderr.write("LF not defined\n")
                exit(55)
            # kontrola duplicity jmen
            if name in self.var_stack_local[len(self.var_stack_local) - 1]:
                sys.stderr.write("duplicit var name\n")
                exit(52)
            # definice proměnné
            self.var_stack_local[len(self.var_stack_local) - 1][name] = [None, None]
        else:
            # špatný identifikátor framu
            sys.stderr.write("wrong frame identifier")
            exit(52)

    # metoda pro nastavení hodnoty proměnné
    # zkontroluje, zda proměnná existuje, pokud ano, nastaví ji hodnoty
    def add_val(self, name, val_type, value, frame):
        name = name[3:]
        # úprava hodnot pro případy hodnoty typu string nebo nil
        if val_type == "string" and value is None:
            value = ""
        if val_type == "nil":
            value = None
        # ukládání do příslušných rámců za pomocí klíčového jména proměnné
        if frame == "GF":
            if name not in self.var_dict_global:
                sys.stderr.write("variable does not exist")
                exit(54)
            self.var_dict_global[name] = [val_type, value]
        elif frame == "TF":
            if name not in self.var_dict_temp:
                sys.stderr.write("variable does not exist")
                exit(54)
            self.var_dict_temp[name] = [val_type, value]
        elif frame == "LF":
            if name not in self.var_stack_local[len(self.var_stack_local) - 1]:
                sys.stderr.write("variable does not exist")
                exit(54)
            self.var_stack_local[len(self.var_stack_local) - 1][name] = [val_type, value]
        else:
            sys.stderr.write("wrong frame identifier")
            exit(52)

    # metoda pro pushnutí dočasného rámce na zásobník lokálních rámců
    def push_frame(self):
        if not Variable.temp_def:
            sys.stderr.write("pushing not created frame")
            exit(55)
        self.var_stack_local.append(self.var_dict_temp)
        self.var_dict_temp = {}
        Variable.temp_def = False

    # metoda, která vytváří nový dočasný rámec
    def create_frame(self):
        self.var_dict_temp = {}
        Variable.temp_def = True

    # metoda, která popne vrchní lokální rámec do dočasného rámce
    def pop_frame(self):
        if not self.var_stack_local:
            sys.stderr.write("no frame in lf to pop")
            exit(55)
        self.var_dict_temp = self.var_stack_local.pop(-1)
        Variable.temp_def = True

    # metoda pro kontrolu definování proměnné
    def is_defined(self, name):
        if name[:2] == "GF":
            if name[3:] in self.var_dict_global:
                return True
            else:
                return False
        elif name[:2] == "TF":
            if not self.temp_def:
                sys.stdin.write("undefined frame")
                exit(55)
            if self.temp_def and name[3:] in self.var_dict_temp:
                return True
            else:
                return False
        elif name[:2] == "LF":
            if not self.var_stack_local:
                sys.stdin.write("undefined frame")
                exit(55)
            if name[3:] in self.var_stack_local[len(self.var_stack_local) - 1]:
                return True
            else:
                return False
        else:
            sys.stderr.write("wrong frame identifier")
            exit(52)

    # metoda pro získání dat proměnné
    def get_data(self, name):
        if name[:2] == "GF":
            return self.var_dict_global[name[3:]]
        elif name[:2] == "TF":
            return self.var_dict_temp[name[3:]]
        elif name[:2] == "LF":
            return self.var_stack_local[len(self.var_stack_local) - 1][name[3:]]
        else:
            sys.stderr.write("wrong frame identifier")
            exit(52)

    def get_tmp_def(self):
        return self.temp_def

    def get_local_frame(self):
        return self.var_stack_local


# pomocná funkce pro string
def replace(match):
    return chr(int(match.group(1)))


# třída pro provádění programu
class Execute:
    def __init__(self, instruct, root_exec, arg_exec):
        # načtení pomocných polí, nastavení counteru na 1
        self.lists = Lists(root_exec)
        self.instruction_order = 1
        self.instruction_order_list = []
        self.data_stack = []
        self.data1 = ""
        self.data2 = ""
        self.type1 = ""
        self.type2 = ""
        self.var = None
        self.var = Variable()
        self.instruction_count = 0
        # pokud nemám vstupní soubor zadaný argumentem, načtu ho ze standartního vstupu
        if arg_exec.get_input() is None:
            file = sys.stdin
        else:
            # pokud mám soubor zadaný argumentem, pokusím se ho otevřít
            try:
                file = open(arg_exec.get_input(), "r")
            except:
                sys.stderr.write("File could not be load")
                exit(11)
        # cyklím dokud mi counter nevyskočí za poslední instrukci
        while self.instruction_order <= len(instruct.get_dict()):
            # načtení opcodu a instrukce na příslušném orderu, získaném z pole orderů pomocí program counteru
            self.opcode = instruct.get_instruction(str(self.lists.get_orders()[self.instruction_order - 1]))[0].upper()
            self.instruction = instruct.get_instruction(str(self.lists.get_orders()[self.instruction_order - 1]))
            # provádění jednotlivých instrukcí
            if self.opcode == "MOVE":
                # pomocí metody check_var kontrola, zda je první argument definovaná proměnná
                self.check_var(0)
                if self.instruction[1][1].get_type() == "var":
                    # pokud je druhý argument proměnná, zkontroluji její definici a inicializaci a uložím data
                    self.check_var(1)
                    self.check_var_inicialized(1)
                    # jméno proměnné a frame získám z nultého argumentu instrukce, typ a data pak z proměnné na příslušném framu
                    self.var.add_val(self.instruction[1][0].get_value(), self.var.get_data(self.instruction[1][1].get_value())[0],
                                     self.var.get_data(self.instruction[1][1].get_value())[1], self.instruction[1][0].get_value()[:2])
                else:
                    # pokud je drhý argument statická hodnota, uložím její data
                    self.var.add_val(self.instruction[1][0].get_value(), self.instruction[1][1].get_type(),
                                 self.instruction[1][1].get_value(), self.instruction[1][0].get_value()[:2])
            # práce s rámci a inicializace proměnné využívají metody třídy Varible
            elif self.opcode == "CREATEFRAME":
                self.var.create_frame()
            elif self.opcode == "PUSHFRAME":
                self.var.push_frame()
            elif self.opcode == "POPFRAME":
                self.var.pop_frame()
            elif self.opcode == "DEFVAR":
                self.var.init_var(self.instruction[1][0].get_value(), self.instruction[1][0].get_value()[:2])
            elif self.opcode == "CALL":
                # kontrola, zda je argument label, a zda je devinovaný
                if self.instruction[1][0].get_type() != "label":
                    sys.stderr.write("call arg type is not label")
                    exit(53)
                if self.instruction[1][0].get_value() not in self.lists.get_labels():
                    sys.stderr.write("call non existing label")
                    exit(52)
                # uložení aktuální pozice programu na zásobník volání
                self.instruction_order_list.append(self.instruction_order)
                # nastavení pozice programu na pozici danného návěští získanou z pomocného slovníku návěští
                self.instruction_order = self.lists.get_orders().index(
                    self.lists.get_labels()[self.instruction[1][0].get_value()])
            elif self.opcode == "RETURN":
                # kontrola zda byl proveden apoň jeden call
                if not self.instruction_order_list:
                    sys.stderr.write("returning without correct call")
                    exit(56)
                # nastavení pozice programu zpět na pozici callu
                self.instruction_order = self.instruction_order_list.pop(-1)
            elif self.opcode == "PUSHS":
                if self.instruction[1][0].get_type() == "var":
                    # pokud pushuji hodnotu proměnné, zkontroluji zda je proměnné definována i inicializována
                    self.check_var(0)
                    self.check_var_inicialized(0)
                    # uložení typu dat a hodnoty na datový zásobník
                    self.data_stack.append(self.var.get_data(self.instruction[1][0].get_value()))
                else:
                    # pokud statická data, uložím jejich typ a hodnotu na datový zásobník
                    self.data_stack.append([self.instruction[1][0].get_type(), self.instruction[1][0].get_value()])
            elif self.opcode == "POPS":
                # kontrola definice proměnné
                self.check_var(0)
                # pokud mám na zásobníku nějaké data, popnu je a přiřádím jejich typ a hodnotu proměnné
                if self.data_stack:
                    pops_data = self.data_stack.pop(-1)
                    self.var.add_val(self.instruction[1][0].get_value(), pops_data[0], pops_data[1],
                                     self.instruction[1][0].get_value()[:2])
                else:
                    sys.stderr.write("pops with empty data stack")
                    exit(56)
            # zkontroluji atributy pomocí metody check_add_like (viz komentáře metody), které předávám požadované typy,
            # a uložení výsledných dat do proměnné
            elif self.opcode == "ADD":
                self.check_add_like("int", "int", 2)
                self.var.add_val(self.instruction[1][0].get_value(), "int", int(self.data1) + int(self.data2),
                                 self.instruction[1][0].get_value()[:2])
            elif self.opcode == "SUB":
                self.check_add_like("int", "int", 2)
                self.var.add_val(self.instruction[1][0].get_value(), "int", int(self.data1) - int(self.data2),
                                 self.instruction[1][0].get_value()[:2])
            elif self.opcode == "MUL":
                self.check_add_like("int", "int", 2)
                self.var.add_val(self.instruction[1][0].get_value(), "int", int(self.data1) * int(self.data2),
                                 self.instruction[1][0].get_value()[:2])
            elif self.opcode == "IDIV":
                self.check_add_like("int", "int", 2)
                # kontrola dělení nulou
                if int(self.data2) == 0:
                    sys.stderr.write("divide by zero")
                    exit(57)
                self.var.add_val(self.instruction[1][0].get_value(), "int", int(self.data1) // int(self.data2),
                                 self.instruction[1][0].get_value()[:2])
            elif self.opcode == "LT":
                # zkontroluji atributy pomocí metody check_lt_like (viz komentáře metody)
                self.check_lt_like()
                # kontrola nepovoleného typu nil
                if self.type1 == "nil" or self.type2 == "nil":
                    sys.stderr.write("uncorrect usage of nil")
                    exit(53)
                # uložení výsledné hodnoty do proměnné
                if self.data1 < self.data2:
                    self.var.add_val(self.instruction[1][0].get_value(), "bool", "true",
                                     self.instruction[1][0].get_value()[:2])
                else:
                    self.var.add_val(self.instruction[1][0].get_value(), "bool", "false",
                                     self.instruction[1][0].get_value()[:2])
            # viz komentáře k LT
            elif self.opcode == "GT":
                self.check_lt_like()
                if self.type1 == "nil" or self.type2 == "nil":
                    sys.stderr.write("uncorrect usage of nil")
                    exit(53)
                if self.data1 > self.data2:
                    self.var.add_val(self.instruction[1][0].get_value(), "bool", "true",
                                     self.instruction[1][0].get_value()[:2])
                else:
                    self.var.add_val(self.instruction[1][0].get_value(), "bool", "false",
                                     self.instruction[1][0].get_value()[:2])
            # viz komentáře k LT
            elif self.opcode == "EQ":
                self.check_lt_like()
                if self.data1 == self.data2:
                    self.var.add_val(self.instruction[1][0].get_value(), "bool", "true",
                                     self.instruction[1][0].get_value()[:2])
                else:
                    self.var.add_val(self.instruction[1][0].get_value(), "bool", "false",
                                     self.instruction[1][0].get_value()[:2])
            elif self.opcode == "AND":
                # zkontroluji atributy pomocí metody check_and_like (viz komentáře metody)
                # předávám příznak že se nejedná o NOT
                self.check_and_like(False)
                # uložení výsledné hodnoty
                if self.data1 and self.data2:
                    self.var.add_val(self.instruction[1][0].get_value(), "bool", "true",
                                     self.instruction[1][0].get_value()[:2])
                else:
                    self.var.add_val(self.instruction[1][0].get_value(), "bool", "false",
                                     self.instruction[1][0].get_value()[:2])
            # viz komentáře k AND
            elif self.opcode == "OR":
                self.check_and_like(False)
                if self.data1 or self.data2:
                    self.var.add_val(self.instruction[1][0].get_value(), "bool", "true",
                                     self.instruction[1][0].get_value()[:2])
                else:
                    self.var.add_val(self.instruction[1][0].get_value(), "bool", "false",
                                     self.instruction[1][0].get_value()[:2])
            # viz komentáře k AND, příznak zda se jedná o NOT je nastaven na True
            elif self.opcode == "NOT":
                self.check_and_like(True)
                if self.data1:
                    self.var.add_val(self.instruction[1][0].get_value(), "bool", "false",
                                     self.instruction[1][0].get_value()[:2])
                else:
                    self.var.add_val(self.instruction[1][0].get_value(), "bool", "true",
                                     self.instruction[1][0].get_value()[:2])
            elif self.opcode == "INT2CHAR":
                # kontrola, zda je první argument definovaná proměnná
                self.check_var(0)
                # kontrola proměnné či statické hodnoty, uložení dat
                if self.instruction[1][1].get_type() == "var":
                    self.check_var(1)
                    if self.var.get_data(self.instruction[1][1].get_value())[0] != "int":
                        sys.stderr.write("wrong var type")
                        exit(53)
                    self.data1 = int(self.var.get_data(self.instruction[1][1].get_value())[1])
                elif self.instruction[1][1].get_type() == "int":
                    self.data1 = self.instruction[1][1].get_value()
                else:
                    sys.stderr.write("wrong arg type")
                    exit(53)
                # pokud je správný ascii kód, uložím znak do proměnné
                try:
                    self.var.add_val(self.instruction[1][0].get_value(), "string", chr(self.data1),
                                     self.instruction[1][0].get_value()[:2])
                except:
                    sys.stderr.write("wrong ascii code")
                    exit(58)
            elif self.opcode == "STRI2INT":
                # kontrola pomocí metody check_add_like, které předávám požadované typy
                self.check_add_like("string", "int", 2)
                # kontrola, zda není index mimo pole
                if int(self.data2) > (len(self.data1) - 1):
                    sys.stderr.write("index out of string")
                    exit(58)
                # přiřazení ascii hodnoty do proměnné
                self.var.add_val(self.instruction[1][0].get_value(), "int", ord(self.data1[int(self.data2)]),
                                 self.instruction[1][0].get_value()[:2])
            elif self.opcode == "READ":
                # kontrola proměnné a druhého argumentu type
                self.check_var(0)
                if self.instruction[1][1].get_type() != "type":
                    sys.stderr.write("wrong data type")
                    exit(53)
                # načtení dat ze souboru
                self.data1 = file.readline().strip()
                # uložím data do proměnné požadovaným typem
                if self.instruction[1][1].get_value() == "int":
                    try:
                        self.var.add_val(self.instruction[1][0].get_value(), "int", int(self.data1),
                                         self.instruction[1][0].get_value()[:2])
                    except:
                        self.var.add_val(self.instruction[1][0].get_value(), "nil", None,
                                         self.instruction[1][0].get_value()[:2])
                elif self.instruction[1][1].get_value() == "string":
                    try:
                        self.var.add_val(self.instruction[1][0].get_value(), "string", str(self.data1),
                                         self.instruction[1][0].get_value()[:2])
                    except:
                        self.var.add_val(self.instruction[1][0].get_value(), "nil", None,
                                         self.instruction[1][0].get_value()[:2])
                else:
                    try:
                        if self.data1.upper() == "TRUE":
                            self.var.add_val(self.instruction[1][0].get_value(), "bool", "true",
                                             self.instruction[1][0].get_value()[:2])
                        else:
                            self.var.add_val(self.instruction[1][0].get_value(), "bool", "false",
                                             self.instruction[1][0].get_value()[:2])
                    except:
                        self.var.add_val(self.instruction[1][0].get_value(), "nil", None,
                                         self.instruction[1][0].get_value()[:2])
            # výpis metodou write_val (viz komentáře metody)
            elif self.opcode == "WRITE":
                self.write_val(True)
            # kontrola proměnné, dalších argumentů metodou check_add_like, uložení výsledné hodnoty do proměnné
            elif self.opcode == "CONCAT":
                self.check_var(0)
                self.check_add_like("string", "string", 2)
                self.var.add_val(self.instruction[1][0].get_value(), "string", str(self.data1) + str(self.data2),
                                 self.instruction[1][0].get_value()[:2])
            # vit CONCAT
            elif self.opcode == "STRLEN":
                self.check_var(0)
                self.check_add_like("string", "", 1)
                self.var.add_val(self.instruction[1][0].get_value(), "int", len(str(self.data1)),
                                 self.instruction[1][0].get_value()[:2])
            # viz CONCAT
            elif self.opcode == "GETCHAR":
                self.check_var(0)
                self.check_add_like("string", "int", 2)
                # kontrola indexu
                if int(self.data2) > (len(self.data1) - 1):
                    sys.stderr.write("index out of string")
                    exit(58)
                self.var.add_val(self.instruction[1][0].get_value(), "string", self.data1[int(self.data2)],
                                 self.instruction[1][0].get_value()[:2])
            elif self.opcode == "SETCHAR":
                # kontrola proměnné a argumentů
                self.check_var(0)
                self.check_add_like("int", "string", 2)
                # první proměnná musí být typu string
                if self.var.get_data(self.instruction[1][0].get_value())[0] != "string":
                    sys.stderr.write("var is not string")
                    exit(53)
                # kontrola indexu stringu
                if int(self.data1) > (len(self.var.get_data(self.instruction[1][0].get_value())[1]) - 1) or self.data2 == "":
                    sys.stderr.write("index out of string")
                    exit(58)
                # úprava dat
                tmp_string = list(self.var.get_data(self.instruction[1][0].get_value())[1])
                tmp_string[int(self.data1)] = self.data2[0]
                # uložení dat zpět do proměnné
                self.var.add_val(self.instruction[1][0].get_value(), "string", "".join(tmp_string),
                                 self.instruction[1][0].get_value()[:2])
            elif self.opcode == "TYPE":
                self.check_var(0)
                if self.instruction[1][1].get_type() == "var":
                    # pokud beru typ z proměnné, zkontroluji definici a pokud není inicializovaná, nastavím data na prázdný string
                    # jinak si vezmu typ z hodnoty proměnné
                    self.check_var(1)
                    if self.var.get_data(self.instruction[1][1].get_value())[0] is None:
                        self.data1 = ""
                    else:
                        self.check_var(1)
                        self.data1 = self.var.get_data(self.instruction[1][1].get_value())[0]
                else:
                    # pokud neberu typ z proměnné, vezmu ho z argumentu instrukce
                    self.data1 = self.instruction[1][1].get_type()
                # uložení typu
                self.var.add_val(self.instruction[1][0].get_value(), "string", self.data1,
                                 self.instruction[1][0].get_value()[:2])
            elif self.opcode == "LABEL":
                pass
            # kontrola argumentů metodou check_jumps, předávám příznak zda se jedná o jednoduchý jump
            elif self.opcode == "JUMP":
                self.check_jumps(True)
                # nastavení pozice programu na požadovaný label
                self.instruction_order = self.lists.get_orders().index(self.lists.get_labels()[self.instruction[1][0].get_value()])
            # kontrola argumentů metodou check_jumps, předávám příznak zda se jedná o jednoduchý jump
            elif self.opcode == "JUMPIFEQ":
                self.check_jumps(False)
                # kontrola podmínky
                if self.data1 == self.data2:
                    # nastavení pozice programu na požadovaný label
                    self.instruction_order = self.lists.get_orders().index(
                        self.lists.get_labels()[self.instruction[1][0].get_value()])
            # kontrola argumentů metodou check_jumps, předávám příznak zda se jedná o jednoduchý jump
            elif self.opcode == "JUMPIFNEQ":
                self.check_jumps(False)
                # kontrola podmínky
                if self.data1 != self.data2:
                    # nastavení pozice programu na požadovaný label
                    self.instruction_order = self.lists.get_orders().index(
                        self.lists.get_labels()[self.instruction[1][0].get_value()])
            elif self.opcode == "EXIT":
                if self.instruction[1][0].get_type() == "var":
                    # pokud mám hodnotu z proměnné, zkontroluji proměnnou, a zda se jedná o int
                    self.check_var(0)
                    self.check_var_inicialized(0)
                    if self.var.get_data(self.instruction[1][0].get_value())[0] != "int":
                        sys.stderr.write("wrong type")
                        exit(53)
                    # kontrola zda se jedná o správný exit code
                    if 0 <= int(self.var.get_data(self.instruction[1][0].get_value())[1]) <= 49:
                        exit(int(self.var.get_data(self.instruction[1][0].get_value())[1]))
                    else:
                        sys.stderr.write("wrong exit code")
                        exit(57)
                elif self.instruction[1][0].get_type() == "int":
                    if 0 <= int(self.instruction[1][0].get_value()) <= 49:
                        exit(int(self.instruction[1][0].get_value()))
                    else:
                        sys.stderr.write("wrong exit code")
                        exit(57)
                else:
                    sys.stderr.write("uncorrect type")
                    exit(53)
            # výpis pomocí metody write_val, příznak False ukazuje, že se má vypisovat na stderr
            elif self.opcode == "DPRINT":
                self.write_val(False)
            # výpis globálního, dočasného a lokálního rámce, datového zásobníku a počet provedených instrukcí na stderr
            elif self.opcode == "BREAK":
                sys.stderr.write("global Frame:")
                sys.stderr.write(str(self.var.var_dict_global))
                sys.stderr.write("temp frame:")
                sys.stderr.write(str(self.var.var_dict_temp))
                sys.stderr.write("local frame:")
                sys.stderr.write(str(self.var.var_stack_local))
                sys.stderr.write("data stack:")
                sys.stderr.write(str(self.data_stack))
                sys.stderr.write("instructions done:")
                sys.stderr.write(str(self.instruction_count))

            else:
                exit(32)
            # inkrement program counteru
            self.instruction_count += 1
            self.instruction_order += 1

    # metoda pro kontrolu, zda je argument na zadaném pořadí argumentu(var_arg s hodnotami 0-2) definovaná proměnná
    def check_var(self, var_arg):
        # kontrola, zda je argument variable
        if self.instruction[1][var_arg].get_type() != "var":
            sys.stderr.write("first attr not var")
            exit(53)
        # kontrola definice lokálního rámce
        if self.instruction[1][var_arg].get_value()[:2] == "LF":
            if not self.var.get_local_frame():
                sys.stderr.write("frame not defined")
                exit(55)
        # kontrola definice dočasného rámce
        if self.instruction[1][var_arg].get_value()[:2] == "TF":
            if not self.var.get_tmp_def():
                sys.stderr.write("frame not defined")
                exit(55)
        # kontrola definice metodou is_defined třídy Variable, předává se jméno proměnné
        if not self.var.is_defined(self.instruction[1][var_arg].get_value()):
            sys.stderr.write("accessing not defined variable")
            exit(54)

    # metoda pro kontrolu parametrů, a uložení užitečných dat pro vykonávání instrukcí
    # parametr first_type udává požadovaný typ prvního argumentu, second_type druhého,
    # args počet kontorlovaných argumentů
    def check_add_like(self, first_type, second_type, args):
        # první je vždy proměnná
        self.check_var(0)
        # pokud je první argument typu variable
        if self.instruction[1][1].get_type() == "var":
            # zkontroluji definici a inicializaci
            self.check_var(1)
            self.check_var_inicialized(1)
            # a až po tom kontroluji typ hodnoty proměnné
            if self.var.get_data(self.instruction[1][1].get_value())[0] != first_type:
                sys.stderr.write("wrong var type")
                exit(53)
            # pokud proběhla kontrola v pořádku, uložím si data proměnné
            self.data1 = self.var.get_data(self.instruction[1][1].get_value())[1]
        # pokud první argument není proměnná a zároveň nemá požadovaný typ - chyba 53
        elif self.instruction[1][1].get_type() != first_type:
            sys.stderr.write("wrong arg type")
            exit(53)
        # když je typ v pořádku, uložím data
        else:
            self.data1 = self.instruction[1][1].get_value()
            # pokud je typ string a hodnota je None, přepíši ji na prázdný string
            if self.instruction[1][1].get_type() == "string" and self.instruction[1][1].get_value() is None:
                self.data1 = ""
        # kontrola hodnoty dat
        if self.data1 is None:
            sys.stderr.write("missing value")
            exit(56)
        # pokud mám kontrolovat i druhý argument, provedu stejnou kontrolu jako pro první
        if args == 2:
            if self.instruction[1][2].get_type() == "var":
                self.check_var(2)
                self.check_var_inicialized(2)
                if self.var.get_data(self.instruction[1][2].get_value())[0] != second_type:
                    sys.stderr.write("wrong var type")
                    exit(53)
                self.data2 = self.var.get_data(self.instruction[1][2].get_value())[1]
                if self.data2 is None:
                    sys.stderr.write("missing value")
                    exit(56)
            elif self.instruction[1][2].get_type() != second_type:
                sys.stderr.write("wrong arg type")
                exit(53)
            else:
                self.data2 = self.instruction[1][2].get_value()
                if self.instruction[1][1].get_type() == "string" and self.instruction[1][1].get_value() is None:
                    self.data1 = ""
            if self.data2 is None:
                sys.stderr.write("missing value")
                exit(56)

    # metoda pro kontrolu instukcí LT, GT, a EQ
    # zkontroluji, zda první hodnota je proměnná, a spustím metodu pro kontrolu argumentů porovnávacích instrukcí
    def check_lt_like(self):
        self.check_var(0)
        self.check_lt_args()

    # metoda pro kontrolu instrukcí NOT, OR, a AND
    # příznak is_not říká zda kontrolovaná instrukce je NOT, tudíž zda se má kontrolovat jen první argument
    def check_and_like(self, is_not):
        # první argument musí být proměnná
        self.check_var(0)
        # pokud je druhý argument proměnná, zkontroluji definici, inicializaci, a podle hodnoty uložím data
        if self.instruction[1][1].get_type() == "var":
            self.check_var(1)
            self.check_var_inicialized(1)
            if self.var.get_data(self.instruction[1][1].get_value())[0] != "bool":
                sys.stderr.write("arg is not bool")
                exit(53)
            if self.var.get_data(self.instruction[1][1].get_value())[1] == "true":
                self.data1 = True
            else:
                self.data1 = False
        # pro statickou hodnotu zkontroluji typ a uložím data
        elif self.instruction[1][1].get_type() == "bool":
            if self.instruction[1][1].get_value() == "true":
                self.data1 = True
            else:
                self.data1 = False
        else:
            sys.stderr.write("arg is not bool")
            exit(53)
        # pokud se nejedná o NOT, zkontroluji stejným způsobem i druhý argument a uložím data
        if not is_not:
            if self.instruction[1][2].get_type() == "var":
                self.check_var(2)
                self.check_var_inicialized(2)
                if self.var.get_data(self.instruction[1][2].get_value())[0] != "bool":
                    sys.stderr.write("arg is not bool")
                    exit(53)
                if self.var.get_data(self.instruction[1][2].get_value())[1] == "true":
                    self.data2 = True
                else:
                    self.data2 = False
            elif self.instruction[1][2].get_type() == "bool":
                if self.instruction[1][2].get_value() == "true":
                    self.data2 = True
                else:
                    self.data2 = False
            else:
                sys.stderr.write("arg is not bool")
                exit(53)

    # kontrola skoků
    def check_jumps(self, is_jump):
        # kontrola typu argumentu, a zda label existuje
        if self.instruction[1][0].get_type() != "label":
            sys.stderr.write("jump arg type not label")
            exit(53)
        if self.instruction[1][0].get_value() not in self.lists.get_labels():
            sys.stderr.write("label not defined")
            exit(52)
        # pokud se jedná o podmíněný skok, zkontroluj argumenty a ulož data
        if not is_jump:
            self.check_lt_args()

    # metoda pro kontrolu argumentů porovnávacích instrukcí
    def check_lt_args(self):
        # vezmu data a typ prvních dvou instrukcí
        if self.instruction[1][1].get_type() == "var":
            self.check_var(1)
            self.check_var_inicialized(1)
            self.type1 = self.var.get_data(self.instruction[1][1].get_value())[0]
            self.data1 = self.var.get_data(self.instruction[1][1].get_value())[1]
        else:
            self.type1 = self.instruction[1][1].get_type()
            self.data1 = self.instruction[1][1].get_value()
        if self.instruction[1][2].get_type() == "var":
            self.check_var(2)
            self.check_var_inicialized(2)
            self.type2 = self.var.get_data(self.instruction[1][2].get_value())[0]
            self.data2 = self.var.get_data(self.instruction[1][2].get_value())[1]
        else:
            self.type2 = self.instruction[1][2].get_type()
            self.data2 = self.instruction[1][2].get_value()
        # kontrola, zda jsou stejného typu, a zároveň kontrola, zda některý není nil, kvůli JUMPIFNEQ
        if self.type1 != self.type2 and self.type1 != "nil" and self.type2 != "nil":
            sys.stderr.write("arg types not same")
            exit(53)
        # úprava typu dat
        if self.type1 == "nil":
            self.data1 = None
        if self.type2 == "nil":
            self.data2 = None
        if self.type1 == "int":
            self.data1 = int(self.data1)
        if self.type2 == "int":
            self.data2 = int(self.data2)

    # metoda pro výpis dat, příznak std říká, zda se má vypsat na stdout nebo stderr
    def write_val(self, std):
        # data na výpis z proměnné
        if self.instruction[1][0].get_type() == "var":
            self.check_var(0)
            self.check_var_inicialized(0)
            # uložím data, pokud se jedná o string, převedu escaepe sekvence
            if self.var.get_data(self.instruction[1][0].get_value())[0] == "string":
                aux = self.var.get_data(self.instruction[1][0].get_value())[1]
                regex = re.compile(r"\\(\d{1,3})")
                new = regex.sub(replace, aux)
            else:
                new = self.var.get_data(self.instruction[1][0].get_value())[1]
            # pokud se jedná o nil vypíšu prázdný string
            if self.var.get_data(self.instruction[1][0].get_value())[0] == "nil":
                if std:
                    print("", end="")
                else:
                    sys.stderr.write("")
            # pokud o něco jiného, vypíšu data
            else:
                if std:
                    print(new, end="")
                else:
                    sys.stderr.write(new)
        # pokud vypisuji přímo hodnotu
        # vypíšu prázdný string pro nil
        elif self.instruction[1][0].get_type() == "nil":
            if std:
                print("", end="")
            else:
                sys.stderr.write("")
        # ostatní data s odstraněnými escape sekvencemi
        else:
            aux = str(self.instruction[1][0].get_value())
            regex = re.compile(r"\\(\d{1,3})")
            new = regex.sub(replace, aux)
            if std:
                print(new, end="")
            else:
                sys.stderr.write(new)

    # metoda pro kontrolu inicializace proměnné
    def check_var_inicialized(self, var_arg):
        if self.var.get_data(self.instruction[1][var_arg].get_value())[0] is None:
            sys.stderr.write("variable not inicialized")
            exit(56)


# ----------- argumenty ---------------------
arguments = Argument()

# -------------nacteni xml souboru------------------
# pokud jsem dostal soubor zadany na stdin
if arguments.get_source_count() == 0:
    std_input = ""
    for line in sys.stdin:
        std_input += line
    try:
        root = ET.fromstring(std_input)
    except:
        print("wrong input")
        exit(31)
# pokud ze souboru
else:
    try:
        tree = ET.parse(arguments.get_source())
        root = tree.getroot()
    except:
        print("wrong input")
        exit(31)

# ------------- xml check ---------------
# if root.attrib[0] != 'language' and root.attrib[1] != 'IPPcode22':
if root.tag != 'program' or "language" not in root.attrib or root.attrib['language'] != "IPPcode22":
    exit(32)
if not list(root):
    exit(0)

for instruction in root:
    if instruction.tag != "instruction" or "order" not in instruction.attrib or "opcode" not in instruction.attrib:
        print("notok")
        exit(32)
    for arg in instruction:
        if not re.match(r"^arg[123]$", arg.tag):
            print("notok")
            exit(32)

# ------------ xml to objects --------------
for instruction in root:
    a = Instruction(instruction.attrib["opcode"], instruction.attrib["order"])
    if instruction.attrib["order"] in a.get_dict() or instruction.attrib["order"] < "1" or instruction.attrib[
        "order"].isnumeric() is False:
        exit(32)
    for arg in instruction:
        a.add_argument(arg.attrib["type"], arg.text)
    a.add_to_dir()

# ---------- execute program --------------
execute = Execute(a, root, arguments)
# print("orders:")
# print(error.lists.get_orders())
# print("global Frame:")
# print(error.var.var_dict_global)
# print("labels:")
# print(error.lists.label_dict)
# print("temp frame")
# print(error.var.var_dict_temp)
# print("local frame")
# print(error.var.var_stack_local)
# print("data stack")
# print(error.data_stack)
