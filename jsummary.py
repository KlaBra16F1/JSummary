"""jsummary"""
import argparse
import csv
import json
import os
import re
import sys
from ast import literal_eval
import requests
from tabulate2 import tabulate

# REGEX-Patterns and Messages
RE_URL = ("Enter URL ('https://example.com/endpoint'): ",
          "Invalid url",
          r"^https?://.+")
RE_FILE = ("Enter input filename or path ('./myfolder/my.json'): ",
          "Invalid filename or path",
          r"^(?:\.{1,2}\/|\.{1,2}\\)?(?:\w|\d)*(?:\w|\d|\.|\/|\\)*?(?:\w|\d)+\.json$")
RE_HEADERS = ("Enter header(s) ('key : value') - 'ENTER' when done: ",
              "Invalid input", r"^[\w\W]+:{1}.+$")
RE_OUTPUT = ("Enter output filename or path (can be .csv, .txt, .md or 'ENTER' for screen): ",
          "Invalid filename or path",
          r"^(?:\.{1,2}/|\.{1,2}\\)?(?:\w|\d)+(?:\w|\d|/|\\)*(?:\w|\d)+(\.csv|\.txt|\.md)$")

# Other global VARS

TBLFMT_TXT = "mixed_grid"
TBLFMT_MD = "github"
TBLFMT_SCREEN = "plain"


# Datacontainer
class Options:
    """Data container for json summary.
    
    Variables:
        INTERACTIVE - bool: Indicator if user input is needed and if the commandline 
                        prompt will get printed at the end of the program
        FILE - str: Stores the filename or path of the json file. 
                    Gets set to none if input is a url.
        URL - str: Same as FILE but for url.
        HEADERS - dict: Stores HTTP Headers. Can be extended via
                        user input or commandline arguments.
        OUTPUT - str: Stores the output name or path for the output file.
                        Default is 'screen' for CLI output.
        TREE - dict: Container for initial recursion from get_json_tree().
        ITEMS_COUNT - dict: Container for precise counting of json values
                    (number, string, boolean, null). Note that strings will be 
                    separated into string, date, date-time and time. 
    """
    INTERACTIVE = True
    FILE = None
    URL = None
    HEADERS = {
        "Accept": "application/json"
    }
    OUTPUT = "screen"
    TREE = {}
    ITEMS_COUNT = {}
    SYMBOL_ARRAY = "[]"
    SYMBOL_OBJECT = "{}"
    SYMBOL_ARRAY_ITEM = "[*]"
    INDENT = "  "
    MASK = 0
    TRIM = 50 # set to -1 for full length
    REDACTED = []
    REQUEST_TIMEOUT = 5
    CSV_DELIMITER = ","
    CNT = 0
    DEBUG = False

    @classmethod
    def print_config(cls):
        """Prints configuration"""
        if cls.FILE:
            print(f"FILE: {cls.FILE}")
        else:
            print(f"URL: {cls.URL}")
            print(f"HEADERS: {cls.HEADERS}")
        print(f"OOUTPUT: {cls.OUTPUT}\n")

    @classmethod
    def is_debug(cls):
        """Returns if programm is in debug mode"""
        return cls.DEBUG




def main():
    """Main function of json_summary."""
    load_config()

    if Options.INTERACTIVE:
        get_user_input()

    if Options.INTERACTIVE:
        print("Success: Loading user input:")
    Options.print_config()

    if Options.FILE:
        jsn = load_from_file(Options.FILE)
    else:
        jsn = load_from_url(Options.URL)
    if not jsn:
        sys.exit("Error: Can't load json data. Exiting...")

    get_json_tree(jsn)
    if not Options.TREE:
        sys.exit("Error: Can't analyze json structure. Exiting...")

    debug(f"Parsing json took {Options.CNT:,d} recursions")

    if table := get_summary_table(list_json(Options.TREE)):

        print(f"Sucess: Outputting table to {Options.OUTPUT}\n")
        if not Options.is_debug():
            output(table)
    else:
        sys.exit("Error: Can't create table. Exiting...")

    print("\nSuccess: Summary complete.\n")

    if Options.INTERACTIVE:
        str_input = f"-f {Options.FILE}" if Options.FILE else f"-u '{Options.URL}'"
        str_output = f"-o {Options.OUTPUT}" if Options.OUTPUT != "screen" else " "
        str_header = f"-H \"{Options.HEADERS}\"" if Options.URL and len(Options.HEADERS) > 1 else ""
        print("The commandline prompt for your request is:\n",
              f"\tpython jsummary.py {str_input} {str_output} {str_header}",
              "\n\nRun 'python json_summary.py -' for more options.\n")

# Input & Verification
def user_input(func):
    """Looped wrapper function for get_input().

    Args:
        see get_input()
    Return:
        user_input - str: Either None (if not verified in get_input)
                            or valid value for wrapper return.
        input_check - bool: Signal if while loop can be stopped.
    """
    def wrapped(*args):
        """The Loop for the decorator"""
        input_check = False
        while input_check is False:
            input_user, input_check = func(*args)

        return input_user

    return wrapped

@user_input
def get_input(verify: tuple, source= None):
    """Decorator for user_input. Also works as a validator for the 
    commandline arguments file, url and header.

    Args:
        verify - tuple: Three value tuple. [0] = prompt message (str),
        [1] = error message (str), [2] regex pattern (raw string)
        source - str: Value to be checked. Only needed for verification of 
        commandline arguments without user input. In this case TRUE is 
        returned in any case to escape the while loop of the wrapper.
    Return:
        source or None
        True or False
    """

    prompt = verify[0]
    error_message = verify[1]
    pattern = verify[2]

    cmd = bool(source)

    # If url is from cli-flags, second True is returned either way to escape loop.
    if cmd:
        check = re.search(pattern, source)
        if not check:
            print(error_message)
            print("dbg", re.search(pattern, source), source)
            return None, True
        return source, True
    # Else get interactive user input

    if Options.CNT == 0:
        print("User input or 'q' to quit")

    try:
        source = input(prompt)
        check = re.search(pattern, source)
        if source in ["q",""]:
            return None, True
        if not check:
            print(error_message)
            Options.CNT += 1
            return None, False

        Options.CNT = 0
        return source, True
    except EOFError:
        print("\nUser interrupted input.")
        return None, True

def get_user_input():
    """Collects neccessary user input for file and url input"""
    while True :
        try:
            choice = input("Import Json from (f)ile, (u)rl or (q)uit: ")
            match choice:
                case "f":
                    Options.FILE = get_input(RE_FILE)
                    if not Options.FILE:
                        sys.exit("Error: Can't continue without an input file. Exiting...")
                    Options.OUTPUT = get_input(RE_OUTPUT)
                    if Options.OUTPUT is None:
                        Options.OUTPUT = "screen"
                    break
                case "u":
                    Options.URL = get_input(RE_URL)
                    if not Options.URL:
                        sys.exit("Error: Can't continue without a url. Exitting...")
                    get_headers()
                    Options.OUTPUT = get_input(RE_OUTPUT)

                    if Options.OUTPUT is None:
                        Options.OUTPUT = "screen"
                    break
                case "q":
                    sys.exit("Good bye.")
        except EOFError:
            sys.exit("Good bye.")

def get_headers():
    """Sub function of get_user_input(). Lists all available headers,
    calls get_inout() and repeats until exit with 'ENTER'"""
    header = ""
    while header is not None:
        print("Current headers:")
        for k,v in Options.HEADERS.items():
            print(f"\t{k}: {v}")
        print()
        header = get_input(RE_HEADERS)
        if header and ":" in header:
            h1= str(header[:header.index(":")]).strip()
            h2 = str(header[header.index(":") + 1:]).strip()

            print(f"Adding {h1}: {h2} to headers\n")
            Options.HEADERS.update({h1: h2})
        # else:
        #         print("Error: Couldn't add header. Make sure you leave a",
        #               "space before and after ' : '")
        #         header = None

def check_date_time(s: str):
    """Detects date, date-time and time patterns in a string

    Args:
        s - string: Input string that will be checked
    Return:
        str: String with value 'date', 'date-time', 'time' or 'string'
    """
    pattern_date = r"^\d{1,4}[-\/\.]{1}\d{1,2}[-\/\.]\d{1,4}$"
    pattern_date_time = r"^\d{1,4}[-\/]{1}\d{1,2}[-\/]\d{1,4}[ T]\d{1,2}:\d{1,2}"
    pattern_time = r"^\d{1,2}:\d{1,2}"
    if re.search(pattern_date, s):
        return "date"
    if re.search(pattern_date_time, s):
        return "date-time"
    if re.search(pattern_time, s):
        return "time"
    return "string"


def adjust_json_type(t: str):
    """Swap python types to json types

    Args:
        s - str: String valie of python type
    Return:
        t - str: String value of json type"""
    match t:
        case "NoneType":
            t = "null"
        case "list":
            t = "array"
        case "dict":
            t = "object"
        case "int":
            t = "number"
        case "float":
            t = "number"
        case "bool":
            t = "boolean"
        case _:
            pass
    return t

def check_consistency(a: dict, b: dict):
    """Checks if a count mismatch results from 'null' values
    
    Args:
        a - dict: Options.ITEMS_COUNT
        b - dict: Counted items from the output table
    Return:
        level - str: 'Info' or 'Warning'
        msg - list: Infomessage for 2 tablerows"""
    difference = {}
    for k, v in a.items():
        difference[k] = v - b.get(k, 0)
    nulls = abs(difference.get("null", 0))
    rest = sum(abs(v) for (k, v) in difference.items() if k != "null")
    debug("Difference", difference)
    if nulls == rest:
        level = "INFO:"
        msg = ["Inconsistent data detected.", "Most likely from occasional 'null' values."]
    else:
        level = "WARNING:"
        msg = ["Inconsistent data detected.", "Most likely due to mixed types in json values"]
    return level, msg

def table_statistics(table, is_consistent, sum_item_count, secondary_itemcount):
    """Add statistics to table"""
    table.append([None, None, None, None, None, None])
    for k, v in sorted(Options.ITEMS_COUNT.items(), key=lambda v: v[1], reverse=True):
        table.append([f"Sum of {k}:",None, None, f"{v:,d}", None, None, None])

        item_sum = sum(list(Options.ITEMS_COUNT.values()))
        debug(item_sum)
        table.append([None, None, None, None, None, None])

        checksum = 0 if sum_item_count == item_sum else ("Count mismatch" +
                                                         f"{item_sum:,d}/{sum_item_count:,d}")
        table.append(["Sum of all items:", None, None,
                    f"{sum_item_count:,d}" if sum_item_count > 0 else None,
                    f"{checksum:,d}" if checksum > 0 else None, None, None])

        debug("Results ITEM_COUNT", Options.ITEMS_COUNT)
        debug("Results from rows", secondary_itemcount)
        if not is_consistent:
            level, msg = check_consistency(Options.ITEMS_COUNT, secondary_itemcount)
            table.append([level, None, None, None, msg[0], None, None])
            table.append([None, None, None, None, msg[1], None, None])
    return table

def get_parent(path: str):
    """Get parent from a dot-separated string"""
    parent = ""
    path_parent = None
    if "." in path:
        path_parent = path.split(".")
        for i in range(len(path_parent) -2, -1, -1):
            if Options.SYMBOL_ARRAY not in path_parent[i]:
                parent = path_parent[i]
                break

    return parent, path_parent

def process_list_items(data, path, path_parent, dot):
    """Subfunction of get_json_tree() for list items"""
    for i in data:
        # In case a list itself contains values.
        # Assuming that the content of the list is type-consistent.
        if type(i).__name__ not in ["list", "dict"]:

            list_type = type(i).__name__
            if isinstance(i, str):
                list_type = check_date_time(i)
            else:
                list_type = adjust_json_type(list_type)
            if path and path_parent:
                parent = path_parent[-1]
            else:
                parent = ""

            if isinstance(i, str):
                list_type = check_date_time(i)
            else:
                list_type = adjust_json_type(list_type)

            count_items(path + dot + Options.SYMBOL_ARRAY +
                        Options.SYMBOL_ARRAY_ITEM, list_type, i, parent)

        else:
            # Default case for lists
            get_json_tree(i, f"{path}{dot}{Options.SYMBOL_ARRAY}")

# Program
def load_config():
    """Loads commandline arguments and verifies input"""

    args = parse_args()
    Options.DEBUG = args.debug

    # Checks and changes

    if args.file or args.url:
        Options.INTERACTIVE = False
        if args.file:
            # Verification filename or path
            Options.FILE = get_input(RE_FILE, args.file)
            Options.URL = None
            Options.HEADERS = None
        elif args.url:
            # Verification url
            Options.URL = get_input(RE_URL, args.url)
            Options.FILE = None
    elif args.file and args.url:
        sys.exit("Error: You can either load a local json file or a remote one.")

    # Verify commandline arguments
    if args.header:
        try:
            temp_headers = literal_eval(args.header)
            for k, v in temp_headers.items():
                Options.HEADERS.update({k: v})
        except ValueError:
            print("Error: Invalid headers. Check for single and double quotes.\n")
            print("Trying default headers instead.")

    Options.OUTPUT = args.output if args.output else Options.OUTPUT
    # Making sure, that indent is off for csv
    if Options.OUTPUT.endswith(".csv"):
        Options.INDENT = ""

    # Setting the rest of the cli arguments if available
    Options.SYMBOL_ARRAY = args.array if args.array else Options.SYMBOL_ARRAY
    Options.SYMBOL_ARRAY_ITEM = args.arrayitem if args.arrayitem else Options.SYMBOL_ARRAY_ITEM
    Options.SYMBOL_OBJECT = args.object if args.object else Options.SYMBOL_OBJECT
    Options.INDENT = args.indent if args.indent else Options.INDENT
    Options.MASK = args.mask if args.mask else Options.MASK
    Options.TRIM = args.trim if args.trim else Options.TRIM
    Options.REQUEST_TIMEOUT = args.timeout if args.timeout else Options.REQUEST_TIMEOUT
    Options.CSV_DELIMITER = args.delimiter if args.delimiter else Options.CSV_DELIMITER

    # Get redacted keys
    if args.redacted:
        for a in args.redacted:
            Options.REDACTED.append(a)

    print("Success: Loading commandline arguments:")

def parse_args():
    """Loader for commanline arguments. Returns args."""
    parser = argparse.ArgumentParser(description="Get a summary of a local or remote json file.")
    # Base arguments
    parser.add_argument("-i", "--interactive", action="store_true", default="true",
                        help="Interactive version with user input. Default choice.")
    parser.add_argument("-f", "--file", type=str, default=None,
                        help="Enter the filename or path to a json file. Requires '--output." +
                        "Overrides interactive version.")
    parser.add_argument("-u", "--url", type=str, default=None,
                        help="Enter the url to a json file. Requires '--output'." +
                        "Overrides interactive version.\n" \
                        "If your API key is part of the url, you can include it." + 
                        "Otherwise use '--header' for header-data.")
    parser.add_argument("-H", "--header", type=str, default=None,
                        help="Enter HTTP headers in the format \"{ 'key1': 'value1'," +
                        "'key2': 'value2', ...}\"")
    parser.add_argument("-o", "--output", type=str, default=None,
                        help="Enter the filename or path your output file. Allowed formats are" +
                        ".txt, .csv and .md. Required by '--file' and '--url'.")
    # Optional arguments
    parser.add_argument("-d","--delimiter", type=str, default=None, help="Change the csv delimiter")
    parser.add_argument("-A", "--array", type=str, default=None,
                        help="Change the symbol for arrays. Default: '[]'")
    parser.add_argument("-a", "--arrayitem", type=str, default=None,
                        help="Change the symbol for arrays. Default: '[*]'")
    parser.add_argument("-O", "--object", type=str, default=None,
                        help="Change the symbol for object. Default: '{}'")
    parser.add_argument("-I", "--indent", type=str, default=None,
                        help="Change the type of indent. Default: '  '")
    parser.add_argument("-M", "--mask", type=int, default=None,
                        help="Mask the first n-characters from the example row.")
    parser.add_argument("-T", "--trim", type=int, default=None,
                        help="Trim example output to n-characters. Will add '...' if trimming." +
                        "Default 20. Set -1 for full lenght output")
    parser.add_argument("-R", "--redacted", type=str, nargs="*", default=None,
                        help="Enter keys you want to mask completely. I.E. for" +
                        "'results.[].user.password'" +
                        "enter 'password' to mask that entry.")
    parser.add_argument("-t", "--timeout", type=float, default=None,
                        help="Add a custom timeout for http requests")
    parser.add_argument("-D", "--debug", action="store_true", default=False,
                        help="Enable debug comments. Not fully implemented yet.")
    return parser.parse_args()

def load_from_file(file: str):
    """Loads and parses a local json file

    Args:
        file - str: String with filename or path
    Return:
        jsn: Json decoded object.
    Handles FILENOTFOUND and JSONDecodeError with sys.exit()"""
    if os.name != "nt":
        file = file.replace("\\","/")
    try:
        with open(file, "r", encoding="utf-8") as f:
            jsn = f.read()
            print("Success: File loaded")
    except FileNotFoundError:
        sys.exit(f"File not found in {file}")
    try:
        jsn = json.loads(jsn)
        print("Success: JSON decoded from file")
    except json.JSONDecodeError:
        sys.exit("Error: Couldn't parse json file")

    return jsn

def load_from_url(url):
    """HTTP request and json decoding

    Args:
        url - str: String with url
    Return:
        jsn: Json decoded object
    Handles HTTPError, ConnectionError, ConnectTimeout, ReadTimeout and 
    JSONDecodeError with None return -> sys.exit() in main()"""
    try:
        req = requests.get(url, headers = Options.HEADERS, timeout=Options.REQUEST_TIMEOUT)
        if req.status_code != 200:
            print(f"Error: Status {req.status_code}")
            return None

        print(f"Sucess: Loading Data from {Options.URL}")

    except requests.HTTPError as e:
        print(f"Error: {e.args[0]}")
        return None
    except (requests.ConnectTimeout, requests.ConnectionError, requests.ReadTimeout):
        print(f"Error: Timeout from {Options.URL}." +
              "Curent settin is {Options.REQUEST_TIMEOUT} seconds.\n" +
              "Maybe try to increase '--timeout' in the commandline options.")
        sys.exit("Exiting...")

    try:
        print("Success: Parsing json data")
        return req.json()
    except json.JSONDecodeError:
        print("Error: Couldn't parse json file\n")
        return None

def get_json_tree(data, path=""):
    """Recursion through JSON structure

    Args:
        data: Initially a json object. Later any type that is inside the jason values.
        path - str: Empty string in the beginng. Later a concacatinated path-structure
    Return:
        None: Function is only updating the Options.TREE dict"""

    Options.CNT += 1
    # Step 1. Preparing the input path
    dot = "." if path else ""
    current_type = type(data).__name__
    if isinstance(data, str):
        current_type = check_date_time(data)
    else:
        current_type = adjust_json_type(current_type)

    parent, path_parent = get_parent(path)

    # Lists / Arrays
    if isinstance(data, list):
        Options.TREE[path + dot + Options.SYMBOL_ARRAY] = {"type": current_type,
                                                    "size": len(data), "parent": parent}
        process_list_items(data, path, path_parent, dot)

    # Dicts / Json objects
    elif isinstance(data, dict):
        Options.TREE[path + dot + Options.SYMBOL_OBJECT] = {"type": current_type,
                                                    "size": len(data), "parent": parent}
        for k,v in data.items():
            get_json_tree(v, f"{path}{dot}{k}")

    # Endpoints / Leafs with actual data
    else:
        # Process and count existing entries
        if Options.TREE.get(path):

            count_items(path, current_type, data, parent)

        # Process new entries
        else:
            count_items(path, current_type, data, parent)

def count_items(path, item_type, content, parent):
    """Sub-function of get_json_tree() handling the counting logic
    
    Args:
        path - str: curren path of the recursion. Is key for Options.TREE
        item_type - str: Current dataype in the pipeline
        content: Current value of the json object
        parent str: Name of the parent object
    Return:
        None: Updates Options.TREE dict  
    """
    # Path exists in Tree

    if Options.TREE.get(path, None) and Options.TREE[path].get("type") not in ["array", "object"]:
        Options.TREE[path]["count"] += 1 # Add 1 to tree
        # Current Type matches existing type
        if Options.TREE[path]["type"] == item_type:
            if Options.ITEMS_COUNT.get(item_type, None):
                Options.ITEMS_COUNT[item_type] += 1 # Add 1 to item_count
            else:
                Options.ITEMS_COUNT[item_type] = 1  # Or create
        else:
            # type is different
            old_type = Options.TREE[path]["type"]
            old_example = Options.TREE[path]["example"]
            # Only change type and example if it was "null"
            Options.TREE[path]["type"] = item_type if old_type == "null" else old_type
            Options.TREE[path]["example"] = content if old_type == "null" else old_example
            Options.TREE[path]["consistent"] = False # Switch misex to true in any case
            # Item-count exists
            if Options.ITEMS_COUNT.get(item_type):
                Options.ITEMS_COUNT[item_type] += 1 # add 1
            else:
                Options.ITEMS_COUNT[item_type] = 1 # create new item
    else:
        Options.TREE[path] = {"type": item_type, "count":  1,
                              "example": content, "parent": parent, "consistent": True}
        if not Options.ITEMS_COUNT.get(item_type, None):
            Options.ITEMS_COUNT[item_type] = 1
        else:
            Options.ITEMS_COUNT[item_type] += 1

def list_json(tree):
    """Creates an aggregated list of dicts from the Options.TREE dict

    Args:
        tree - dict: The Options.TREE dict
    Return:
        json_summary - list: Contains the aggregated values"""
    json_summary = []
    # Note: Enumerate requires k and v in brackets
    for k, v in tree.items():
        elements = k.count(".")
        elements += 1 if k.count("[") > 1 else 0
        if v.get("size"):
            if v.get("type") == "list":
                symbol = Options.SYMBOL_ARRAY
            else:
                symbol = Options.SYMBOL_OBJECT
            json_summary.append({"name": k, "type": v["type"], "symbol": symbol,
                                 "size": v["size"], "parent": v["parent"]})
        else:
            elements += 1
            example = v.get("example", None)
            count = v.get("count", None)
            json_summary.append({"name": k, "type": v["type"],
                                 "consistent": v.get("consistent", None),
                                 "count": count, "example": example, "parent": v["parent"]})
    return json_summary

def get_summary_table(json_summary):
    """Creates the final summary table for csv or tabulate2 output
    
    Args:
        json_summary - list: The list of dicts created in reduce_json()
    Return:
        table - list: List from json_summary and Options.ITEM_COUNT
        
    Note that all the modifications INDENT, MASK, TRIM and REDACTED are handled here"""

    table = []
    header = ["NAME", "TYPE", "SIZE", "COUNT", "EXAMPLE", "CONSITENT", "PARENT"]
    table.append(header)
    sum_item_count = 0
    secondary_itemcount = {}
    is_consistent = True
    for entry in json_summary:
        name = entry.get("name")
        # Indent, if output is not csv
        name = Options.INDENT * name.count(".") + name
        entry_type = entry.get("type", "")
        size = entry.get("size", 0)
        count = entry.get("count", 0)

        # double checking
        if count is None:
            count = 0
        if size is None:
            size = 0

        example = entry.get("example", "N/A")
        # Masking, trimming and redacting of example cell
        if entry_type == "string":
            example = example.replace("\n","\\n")
            if Options.REDACTED:
                key = name.split(".")[-1]
                if example and key in Options.REDACTED:
                    example = "*" * len(example)
            if example:
                example = "*" * Options.MASK + example[Options.MASK:Options.TRIM] + (""
                            "..." if len(example) > Options.TRIM - (len(example) ) else "")

        consistent = entry.get("consistent", None)

        # Add row items count to secondary counter
        if count:
            if secondary_itemcount.get(entry_type):
                secondary_itemcount[entry_type] += count
            else:
                secondary_itemcount[entry_type] = count
        # create a marker for consistency check
        if not consistent and entry_type not in ["array", "object"]:
            is_consistent = False

        # Second counter for verification of Options.ITEMS_COUNT
        if isinstance(count, int):
            sum_item_count += count

        row = [name, entry_type, f"{size:,d}" if size > 0 else None,
               f"{count:,d}" if count > 0 else None, example, consistent,
               entry.get("parent", None)]
        table.append(row)

    # Append statistics to the table
    table = table_statistics(table, is_consistent, sum_item_count, secondary_itemcount)

    return table

def output(table):
    """Route to different output methods"""

    match Options.OUTPUT:
        case c if Options.OUTPUT.endswith(".csv"):
            output_csv(table)
        case c if Options.OUTPUT.endswith(".md"):
            output_text(table, TBLFMT_MD)
        case c if Options.OUTPUT.endswith(".txt"):
            output_text(table, TBLFMT_TXT)
        case _:
            print(tabulate(table, headers="firstrow",
                           tablefmt=TBLFMT_SCREEN, preserve_whitespace=True))
    debug(c)

def output_csv(table):
    """Output table to as csv file or exit on any exception"""

    try:
        with open(Options.OUTPUT, "w", encoding="utf-8") as file:
            writer = csv.writer(file, delimiter=Options.CSV_DELIMITER)
            for row in table:
                writer.writerow(row)
        print("Success: Writing csv file")
    except (PermissionError, OSError) as e:
        sys.exit(e)

def output_text(table, formatting):
    """Output table to as txt or md file or exit on any exception"""
    try:
        with open(Options.OUTPUT, "w", encoding="utf-8") as file:
            for row in tabulate(table, headers="firstrow",
                                tablefmt=formatting, preserve_whitespace=True):
                file.write(row)
        print("Success: Writing file")
    except (PermissionError, OSError) as e:
        sys.exit(e)

# Info


def debug(*args):
    """Print debug messages if a global variable 'DEBUG' is true.
    
    Args:
        *args
    Side effects:
        'DEBUG: arg[0] --- arg[...] --- arg[n] :::END'
    Return:
        None"""
    if Options.is_debug():
        print("DEBUG: ", end="")
        for a in args:

            print(a, end=" --- ")
        print("   :::End")

if __name__ == "__main__":
    main()
