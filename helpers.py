### Note: these functions can basically be ignored.
### They are helper functions to more easily work with and print the data.

def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError
    

def write_data():
    """
    Ignore this function -- it's just a helper to add in data.
    """
    # To be used to dump the Sales1M.csv file into the data struct
    # Similar to what WASM uses. For example:
    
    # Before: ['64333', '3/9/18', '264879', 'NE', 'HDBUY', '9.99', 'USD', '9.99']
    # After:  [134981, 43168.0, 312583, 'AZ', 'SDRENT', 3.99, 'USD', 3.99]
    data = []
    with open('Sales1M.csv') as csvfile:
        reader = csv.reader(csvfile)
        for num, row in enumerate(reader):
            if num % 1000 == 0: print num
            if num == 0:
                header = row
                continue
            raw_data = zip(header,row)
            formatted_row = []
            # format the data 
            for field, value in raw_data:
                if (not value) or value.lower() in ('nil', 'null'):
                    value = None
                elif self.COLUMN_INFO[field]['type'] == DATA_TYPE_STRING:
                    value = value
                elif self.COLUMN_INFO[field]['type'] == DATA_TYPE_DECIMAL:
                    value = float(value) if value else None
                elif self.COLUMN_INFO[field]['type'] == DATA_TYPE_INTEGER:
                    value = int(value) if value else None
                elif self.COLUMN_INFO[field]['type'] == DATA_TYPE_BOOLEAN:
                    value = None if not value else False if value.lower() in ['f', 'false', 'off', '0'] else True
                elif self.COLUMN_INFO[field]['type'] in (DATA_TYPE_DATE, DATA_TYPE_DATETIME, DATA_TYPE_TIME):
                    value = excel_date(parse(value)) if value else None
            
                formatted_row.append(value)
            data.append(formatted_row)
            
    json.dumps('Sales1M_WasmFormatted.json','w').write(formatted_rows)


def filterfalse(predicate, iterable):
    # filterfalse(lambda x: x%2, range(10)) --> 0 2 4 6 8
    if predicate is None:
        predicate = bool
    for x in iterable:
        if not predicate(x):
            yield x


def unique_everseen(iterable, key=None):
    "List unique elements, preserving order. Remember all elements ever seen."
    # https://docs.python.org/3/library/itertools.html
    # unique_everseen('AAAABBBCCDAABBB') --> A B C D
    # unique_everseen('ABBCcAD', str.lower) --> A B C D
    seen = set()
    seen_add = seen.add
    if key is None:
        for element in filterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen_add(k)
                yield element
                
