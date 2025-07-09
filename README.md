# JSummary

## Description:

This is the final project for HarvardX CS50P course [CS50’s Introduction to Programming with Python](https://github.com/vasilisa-che/CS50P-Final-Project)

JSON is a great format for data exchange. However, with greater complexity or size, it can be difficult to keep track of all available keys, objects, arrays and types. A key that contains 'null' a haundred timese might suddenly contain a string. Item 356 suddenly contain a new object. And so on and so forth.  

This is where JSummary comes into play. The program iterates over your complete json file (or API request) and prints out a summary of all available paths, including type of data, count of items or size of objects and a example of content. Additionaly there is a consistency check (for types) and a parent column, that comes in handy, when the output list is quite long. JSummary can output either to file (csv, text or markdown) or termnal. Input is either interactive of straight from the commandline with lots of extra options.


## Installation

After downloading this repo, you need to install the required libraries first. The software only uses tabulate2 (with support for whitespace preservation) and requests. Install with: 

```bash
pip install -r requirements.txt
```
More info on [tabulate2](https://github.com/RaSan147/python-tabulate)

Then run the interactive version:
```bash
python jsummary.py 
```
Or read through all available commandline options:
```bash
python jsummary.py -h
```
Jsummary officially supports Python3.10+.

## Usage

### Interactive

After running `jsummary.py` you will have these options:
```
Import Json from (f)ile, (u)rl or (q)uit:
```
After choosing option `u`, next you are prompted for a url.
```
Import Json from (f)ile, (u)rl or (q)uit: u
User input or 'CTRL-D' to exit
Enter URL ('https://example.com/endpoint'): https://some.website.com/some/api/regions
```
If you have an API key is your url, you need enter it here as well. If you need header authentication, this can be done next.

__IMPORTANT:__ When entering a key : value pair during the header input, you need to leave a whitespace before and after the `:`, else the program will not recognize it. After successful input, you will see a list of all headers you entered so far.
```
Current headers:
        Accept: application/json
```

If you don't need headers or are done with your input, press `CTRL-D` to continue.

Next you can decide for an fileoutput (enter filename or path/filename) or press `CTRL-D` again for terminal output.
Fileoutput supports markdown `.md` (prints a markdown table), test `.txt` (pretty ascii table) and of course CSV.

After deciding for terminal output, you see something like this:
```
Success: Loading user input:
         FILE: None
         HEADERS: {'Accept': 'application/json'}
         INTERACTIVE: True
         OUTPUT: screen
         URL: https://some.website.com/some/api/regions

Sucess: Loading Data from https://some.website.com/some/api/regions
Success: Parsing json data
Sucess: Outputting table to screen
```
And of course the summary:
```
Name                                                  Type         Size    Count  Example                                        Consistent    Parent
{}                                                    object          1           N/A
  data.[]                                             array           1           N/A
    data.[].{}                                        object          3           N/A                                                          data
    data.[].from                                      date-time                1  2025-07-06T15:00Z                              True          data
    data.[].to                                        date-time                1  2025-07-06T15:30Z                              True          data
      data.[].regions.[]                              array          18           N/A                                                          data
        data.[].regions.[].{}                         object          5           N/A                                                          regions
        data.[].regions.[].regionid                   number                  18  1                                              True          regions
        data.[].regions.[].dnoregion                  string                  18  Scottish Hydro Electric Power Distribution...  True          regions
        data.[].regions.[].shortname                  string                  18  North Scotland                                 True          regions
          data.[].regions.[].intensity.{}             object          2           N/A                                                          regions
          data.[].regions.[].intensity.forecast       number                  18  0                                              True          intensity
          data.[].regions.[].intensity.index          string                  18  very low                                       True          intensity
          data.[].regions.[].generationmix.[]         array           9           N/A                                                          regions
            data.[].regions.[].generationmix.[].{}    object          2           N/A                                                          generationmix
            data.[].regions.[].generationmix.[].fuel  string                 162  biomass                                        True          generationmix
            data.[].regions.[].generationmix.[].perc  number                 162  0                                              True          generationmix

Sum of string:                                                               216
Sum of number:                                                               198
Sum of date-time:                                                              2

Sum of all items:                                                            416

Success: Summary complete.
```
You also get a hint, how to repeat this request from the commanline.
```
The commandline prompt for your request is:
        python jspn_summary.py -u https://api.carbonintensity.org.uk/regional
```
More on reading the table, in the next section.

### Commandline

The commandline options are:
```
Get a summary of a local or remote json file.

options:
  -h, --help            show this help message and exit
  -i, --interactive     Interactive version with user input. Default choice.
  -f FILE, --file FILE  Enter the filename or path to a json file. Requires '--output'. Overrides interactive version.
  -u URL, --url URL     Enter the url to a json file. Requires '--output'. Overrides interactive version. If your API key is part of the url, you can include it. Otherwise use '--header' for header-data.
  -H HEADER, --header HEADER
                        Enter HTTP headers in the format "{ 'key1': 'value1', 'key2': 'value2', ...}"
  -o OUTPUT, --output OUTPUT
                        Enter the filename or path your output file. Allowed formats are .txt, .csv and .md. Required by '--file' and '--url'.
  -d DELIMITER, --delimiter DELIMITER
                        Change the csv delimiter
  -A ARRAY, --array ARRAY
                        Change the symbol for arrays. Default: '[]'
  -a ARRAYITEM, --arrayitem ARRAYITEM
                        Change the symbol for arrays. Default: '[*]'
  -O OBJECT, --object OBJECT
                        Change the symbol for object. Default: '{}'
  -I INDENT, --indent INDENT
                        Change the type of indent. Default: ' '
  -M MASK, --mask MASK  Mask the first n-characters from the example row.
  -T TRIM, --trim TRIM  Trim example output to n-characters. Will add '...' if trimming. Default 20. Set -1 for full lenght output
  -R [REDACTED ...], --redacted [REDACTED ...]
                        Enter keys you want to mask completely. I.E. for 'results.[].user.password' enter 'password' to mask that entry.
  -t TIMEOUT, --timeout TIMEOUT
                        Add a custom timeout for http requests
  -D, --debug           Enable debug comments. Not fully implemented yet.
```

Note that indentation is deativated when the output is CSV.

## Table columsn and summary rows

### Columns

__NAME:__ Here you can see a path-structure of the json data, where \[] stands for an array, \[*] for direct array-data-values, \{} for a nested object and the actual keys, containing data. The symbols can be changed in the commandline arguments.

__TYPE:__ Type of data or object as a string. Besides the generic json types, JSummary detects 'date', 'date-time', and 'time' which otherwise would be of type 'string' as well.  

__SIZE:__ The size of arrays or objects. Since all the data is flattened, you can see how many entries are inside an array or how many keys are inside an object.  

__COUNT:__ The number of times a certain key is present. Lets say that in 100 data entries a certain key is only present in 10 of them. This is what you can read here.  

__EXAMPLE:__ A sample of the data, which is present in that key. By default the first sample is taken from the data. However, if that sample happens to be 'null', it will be overwritten (as well with the type) by the first _real_ value thats inside the json data. Note that examples can be masked (i.E. '***a Croft) and trimmed (i.E. 'https://www.example.com/very/lon...') and even redacted for certain key-names.  

__CONSISTENT:__ In a perfet world you can read 'True' everywhere. In case there is some _mixed_ types in a cretain key, you will read 'False' here. This can be ok, when there is a 'null' vs. _real_ data issue, but it could also meant, that there are some 1 vs "1" issues or worse. There is another check for that later.  

__Parent:__ Here you can read the parent of the key. This is helpful, when you got a very long list of entries. Also you can use this as filter, when you load the csv into your favourite spreadsheet app.

### Rows

Below the actual json summary you have some extra rows with with counters for each datatypes (descending by count) and a total sum of items. If there is some inconsistency (one or many 'False' entries in the column), there will be additional info, whether the mismatch is likely to result from 'null' values or if there might be a real type mismatch in your data.

## How it works

Lets assume a very simple json file:
```json
{
    "results": [
        {
            "id": 1,
            "name": "foo doe",
            "age": 20,
            "registered": null,
            "friends": ["bar", "baz"]
        },
        {
            "id": 2,
            "name": "bar doe",
            "age": 25,
            "registered": true,
            "profile": {
                "username": "bar99-ftw",
                "password": "insucurePWD",
                "last_login": "2025-07-06 10:45"
            },
            "friends": ["foo", "baz"]
        },
        {
            "id": 3,
            "name": "baz doe",
            "age": 19,
            "registered": true,
            "profile": {
                "username": "foo01",
                "password": "5l1ghtlyB377#r",
                "2fa_enabled": true,
                "last_login": "2025-07-06 10:45"
            }
        }
    ]
}
```

Lets run this with following command.
```
python project.py  -f foo1.json --mask 3 --redacted password username 
```

I put an extra comment-column to the markdown table:

| Name                                 | Type      |   Size |   Count | Example                                    | Consistent   | Parent   | Comment |
| :----------------------------------- | :-------- | -----: | ------: | :----------------------------------------- | :----------- | :------- | :---|
| {}                                   | object    |      1 |         | N/A                                        |              |          | |
|   results.[]                         | array     |      3 |         | N/A                                        |              |          | Array contains 3 datasets |
|     results.[].{}                    | object    |      5 |         | N/A                                        |              | results  | There are 4 keys and 1 array in each dataset|
|     results.[].id                    | number    |        |       3 | 1                                          | True         | results  | First sample is picked as example |
|     results.[].name                  | string    |        |       3 | *** doe                                    | True         | results  | Firs 3 characters are masked for strings |
|     results.[].age                   | number    |        |       3 | 20                                         | True         | results  | Not 3 booleans, but 3 entries for that key! |
|     results.[].registered            | boolean   |        |       3 | True                                       | False        | results  | Correctly sampled as boolean. Not consisten because of null |
|       results.[].friends.[]          | array     |      2 |         | N/A                                        |              | results  | Size is 2 because it's missing in results\[2] |
|       results.[].friends.[][*]       | string    |        |       4 | ***                                        | True         | friends  | Notation is \[*] for array values without a key |
|       results.[].profile.{}          | object    |      4 |         | N/A                                        |              | results  | \{} notation for nested object
|       results.[].profile.username    | string    |        |       2 | *********                                  | True         | profile  | Redacted username with --redacted option |
|       results.[].profile.password    | string    |        |       2 | ***********                                | True         | profile  | Redacted password as well |
|       results.[].profile.last_login  | date-time |        |       2 | 2025-07-06 10:45                           | True         | profile  | Typed as date-time |
|       results.[].profile.2fa_enabled | boolean   |        |       1 | True                                       | True         | profile  | Detected additional key, but count is less than other entries from that nested object |
|                                      |           |        |         |                                            |              |          |
| Sum of string:                       |           |        |      11 |                                            |              |          |
| Sum of number:                       |           |        |       6 |                                            |              |          |
| Sum of boolean:                      |           |        |       3 |                                            |              |          | Actual boolean count|
| Sum of date-time:                    |           |        |       2 |                                            |              |          |
| Sum of null:                         |           |        |       1 |                                            |              |          | null is not present above, but listed here |
|                                      |           |        |         |                                            |              |          |
| Sum of all items:                    |           |        |      23 |                                            |              |          |
| INFO:                                |           |        |         | Inconsistent data detected.                |              |          | Info notice with analysis |
|                                      |           |        |         | Most likely from occasional 'null' values. |              |          |

Now lets bring in some more inconsitency. Someone decided to use strings as id to have some leading zeros. Someone else wrote "yes" instead of `true`.

```json
{
    "results": [
        {
            "id": "0001",
            "name": "foo doe",
            "age": 20,
            "registered": null,
            "friends": ["bar", "baz"]
        },
        {
            "id": 2,
            "name": "bar doe",
            "age": 25,
            "registered": true,
            "profile": {
                "username": "bar99-ftw",
                "password": "insucurePWD",
                "last_login": "2025-07-06 10:45"
            },
            "friends": ["foo", "baz"]
        },
        {
            "id": 3,
            "name": "baz doe",
            "age": 19,
            "registered": "yes",
            "profile": {
                "username": "foo01",
                "password": "5l1ghtlyB377#r",
                "2fa_enabled": true,
                "last_login": "2025-07-06 10:45"
            }
        }
    ]
}
```

| Name                                 | Type      |   Size |   Count | Example                                       | Consistent   | Parent   | Comment |
| :----------------------------------- | :-------- | -----: | ------: | :-------------------------------------------- | :----------- | :------- | :---|
| {}                                   | object    |      1 |         | N/A                                           |              |          |
|   results.[]                         | array     |      3 |         | N/A                                           |              |          |
|     results.[].{}                    | object    |      5 |         | N/A                                           |              | results  |
|     results.[].id                    | string    |        |       3 | ***1                                          | False        | results  | Key is now typed as string |
|     results.[].name                  | string    |        |       3 | *** doe                                       | True         | results  |
|     results.[].age                   | number    |        |       3 | 20                                            | True         | results  |
|     results.[].registered            | boolean   |        |       3 | True                                          | False        | results  | Stil boolean, cause this was the first sample.|
|       results.[].friends.[]          | array     |      2 |         | N/A                                           |              | results  |
|       results.[].friends.[][*]       | string    |        |       4 | ***                                           | True         | friends  |
|       results.[].profile.{}          | object    |      4 |         | N/A                                           |              | results  |
|       results.[].profile.username    | string    |        |       2 | *********                                     | True         | profile  |
|       results.[].profile.password    | string    |        |       2 | ***********                                   | True         | profile  |
|       results.[].profile.last_login  | date-time |        |       2 | 2025-07-06 10:45                              | True         | profile  |
|       results.[].profile.2fa_enabled | boolean   |        |       1 | True                                          | True         | profile  |
|                                      |           |        |         |                                               |              |          |
| Sum of string:                       |           |        |      13 |                                               |              |          | Strings increased (id and registered)|
| Sum of number:                       |           |        |       5 |                                               |              |          | One less because of id |
| Sum of boolean:                      |           |        |       2 |                                               |              |          | One less because of registered|
| Sum of date-time:                    |           |        |       2 |                                               |              |          |
| Sum of null:                         |           |        |       1 |                                               |              |          | 
|                                      |           |        |         |                                               |              |          |
| Sum of all items:                    |           |        |      23 |                                               |              |          |
| WARNING:                             |           |        |         | Inconsistent data detected.                   |              |          | Info got raise to warning |
|                                      |           |        |         | Most likely due to mixed types in json values |              |          |

Note that this consistency check might not work, when some other mismatches might compensate the offset. Its always safe to check keys that are marked as `False` in the columns.

## Limitations

There is a certain type of json structure, where both keys and values are stored inside a wrapper object. This is mostly the case in custom reports that some cloud services provide for their customers.  
Those wrappers might look like this.
```json
[
    {
        "attribute_id": "name",
        "attribute_type": "string",
        "value": "alice"
    },
    {
        "attribute_id": "age",
        "attribute_type": "number",
        "value": 23
    },
    {
        "attribute_id": "newsletter",
        "attribute_type": "boolean",
        "value": true
    }
]
```
In such cases Jsummary will not work as intended and give you meaningless results, because same keys store different values and types.

