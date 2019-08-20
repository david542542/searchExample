import csv
from dateutil.parser import *
import datetime as dt
import os
import json
import time
import re
from helpers import set_default, write_data, unique_everseen


DATA_TYPE_STRING = 0
DATA_TYPE_INTEGER = 1
DATA_TYPE_DECIMAL = 2
DATA_TYPE_DATE = 3
DATA_TYPE_DATETIME = 4
DATA_TYPE_TIME = 5
DATA_TYPE_BOOLEAN = 6

SEARCH_TYPE_OFF = 0
SEARCH_TYPE_EXACT = 1
SEARCH_TYPE_STARTSWITH = 2
SEARCH_TYPE_EDGE = 3
SEARCH_TYPE_CONTAINS = 4

POSSIBLE_BOOLEAN_TRUE_VALUES = ['y', 'yes', 't', 'true', '1', 'on']
POSSIBLE_BOOLEAN_FALSE_VALUES = ['n', 'no', 'f', 'false', '0', 'off']
POSSIBLE_BOOLEAN_VALUES = POSSIBLE_BOOLEAN_TRUE_VALUES + POSSIBLE_BOOLEAN_FALSE_VALUES
POSSIBLE_MONTH_STARTSWITH = set(['j', 'ja', 'jan', 'f', 'fe', 'feb', 'm', 'ma', 'mar', 'a', 'ap', 'apr', 'm', 'ma', 'may', 'j', 'ju', 'jun', 'j', 'ju', 'jul', 'a', 'au', 'aug', 's', 'se', 'sep', 'o', 'oc', 'oct', 'n', 'no', 'nov', 'd', 'de', 'dec'])
PUNCTUATIONS = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'

ACCEPTABLE_REGEX_DATETIME_PATTERNS = [
    r'\d{4}\-\d{1,2}\-\d{1,2}\s\d{1,2}\:\d{1,2}\:\d{1,2}\.?\d{0,10}', # 2014-01-01 01:02:03
]
ACCEPTABLE_REGEX_DATE_PATTERNS = [
    r'\d{4}\-\d{1,2}\-\d{1,2}', # 2014-01-01
    r'\d{1,2}\/\d{1,2}\/\d{2,4}', # 01/23/24
    r'[a-zA-Z]{1,3}\.?\s\d{1,2}\,?\s\d{2,4}', # Mar 1, 2014
]
ACCEPTABLE_REGEX_TIME_PATTERNS = [
    r'\d{1,2}:\d{1,2}:\d{1,2}\.?\d{0,10}' # 01:02:03
]

TIME_FORMAT_1 = '%H:%M:%S' # 01:02:03
TIME_FORMAT_2 = '%-H:%M %p' # 1:02 am
DATE_FORMAT_1 = '%Y-%M-%D' # 2014-01-01
DATE_FORMAT_2 = '%m/%d/%y' # 01/01/14
DATE_FORMAT_3 = '%b %d %Y' # Jan 1 2014
DATETIME_FORMAT_1 = '%Y-%M-%d %H:%M:%S'
DT_FORMATS = [TIME_FORMAT_1, TIME_FORMAT_2, DATE_FORMAT_1, DATE_FORMAT_2, DATE_FORMAT_3, DATETIME_FORMAT_1]

def excel_date(date):
    """
    Note: make sure this is the correct length --
          it's possible our DATE/TIME type is longer, such as 1e6
    
    Also, make sure it's correct for all three types -- TIMESTAMP, TIME, AND DATE
    """
    if isinstance(date, (str, unicode)):
        date = parse(date)
    temp = dt.datetime(1899, 12, 30)    # Note, not 31st Dec but 30th!
    delta = date - temp
    return int(float(delta.days) + (float(delta.seconds) / 86400))
    

class Search:
    
    def __init__(self):
        self.orignal_search_term = None
        self.matches_at_index = set() # These are all the search matches by row index
        
        self.SEARCH_INFO = {
            'OriginalSearch': '',
            'TokenizedSearch': [],
            'MissingTokens': [],
            'Parsed': [
                
            ],
            'NumResults': 0,
            'FirstTenResults': []
        }
        
        # An example of `Parsed` obj would be: 
        '''
        {
            'Field': 'Date',
            'searchType': SEARCH_TYPE_EDGE,
            'dataType': DATA_TYPE_DATE,
            'searchAs': 40922,
            'Tokens': ['mar', '4', '2014'],
            '_AllowIncompleteMatch': None
        }
        '''
        
        self.COLUMN_INFO = {
            'id': {
                'type': DATA_TYPE_INTEGER,
                'searchType': SEARCH_TYPE_EXACT,
                'dateTypeFormat': None,
                'minLength': None,
                'maxLength': None,
                'minValue': None,
                'maxValue': None,
                'isAllLower': None,
                'isAllUpper': None,
                'containsNumericStart': None,
                'containsMultipleWords': None,
                'index': 0,
            },
            'date': {
                'type': DATA_TYPE_DATE,
                'searchType': SEARCH_TYPE_EXACT,
                'dateTypeFormat': None,
                'minLength': None,
                'maxLength': None,
                'minValue': None,
                'maxValue': None,
                'isAllLower': None,
                'isAllUpper': None,
                'containsNumericStart': None,
                'containsMultipleWords': None,
                'index': 1,
            },
            'instance_id': {
                'type': DATA_TYPE_INTEGER,
                'searchType': SEARCH_TYPE_EXACT,
                'dateTypeFormat': None,
                'minLength': None,
                'maxLength': None,
                'minValue': None,
                'maxValue': None,
                'isAllLower': None,
                'isAllUpper': None,
                'containsNumericStart': None,
                'containsMultipleWords': None,
                'index': 2,
            },
            'territory_id': {
                'type': DATA_TYPE_STRING,
                'searchType': SEARCH_TYPE_EDGE,
                'dateTypeFormat': None,
                'minLength': None,
                'maxLength': None,
                'minValue': None,
                'maxValue': None,
                'isAllLower': None,
                'isAllUpper': None,
                'containsNumericStart': None,
                'containsMultipleWords': None,
                'index': 3,
            },
            'code':  {
                'type': DATA_TYPE_STRING,
                'searchType': SEARCH_TYPE_EDGE,
                'dateTypeFormat': None,
                'minLength': None,
                'maxLength': None,
                'minValue': None,
                'maxValue': None,
                'isAllLower': None,
                'isAllUpper': None,
                'containsNumericStart': None,
                'containsMultipleWords': None,
                'index': 4,
            },
            'price': {
                'type': DATA_TYPE_DECIMAL,
                'searchType': SEARCH_TYPE_EXACT,
                'dateTypeFormat': None,
                'minLength': None,
                'maxLength': None,
                'minValue': None,
                'maxValue': None,
                'isAllLower': None,
                'isAllUpper': None,
                'containsNumericStart': None,
                'containsMultipleWords': None,
                'index': 5,
            },
            'currency_code_id': {
                'type': DATA_TYPE_STRING,
                'searchType': SEARCH_TYPE_EDGE,
                'dateTypeFormat': None,
                'minLength': None,
                'maxLength': None,
                'minValue': None,
                'maxValue': None,
                'isAllLower': None,
                'isAllUpper': None,
                'containsNumericStart': None,
                'containsMultipleWords': None,
                'index': 6,
            },
            'price_in_usd': {
                'type': DATA_TYPE_DECIMAL,
                'searchType': SEARCH_TYPE_EXACT,
                'dateTypeFormat': None,
                'minLength': None,
                'maxLength': None,
                'minValue': None,
                'maxValue': None,
                'isAllLower': None,
                'isAllUpper': None,
                'containsNumericStart': None,
                'containsMultipleWords': None,
                'index': 7,
            },
        }
        # Load the Wasm-like data for testing.
        self.data = []
        if not os.path.exists('Sales1M_WasmFormatted.json'):
            self.data = _write_data()
        self.data = json.loads(open('Sales1M_WasmFormatted.json').read())
        

    def tokenize(self, v, MIN_LENGTH=1, MAX_LENGTH=100):
        """
        Tokenize terms.
        
        For example:
        
           INPUT ==> "US Terminator 2 us 4.99 2014-01-01 01:02:03"
           OUTPUT ==> ["us", "terminator", "2", "us", "4.99", "2014-01-01", "01:02:03"]
        
        Note that it might seem like we can remove duplicate terms.
        However, take the location "Bora Bora" -- it we made the terms unique,
        ["bora"], we would fail on an exact match.
        
        Instead, what we need to do is not search the exact term twice, which would
        be column-specific. For example, the term "bora" would only be searched one time
        against a column, though the term "bora bora" could also be searched against
        a column that has `containsMultipleWords`=True.
        
        """
        
        # This is the most basic tokenizer possible, we can always add on to this later.
        
        terms = []
        for term in v.split():
            term = term.strip().strip(PUNCTUATIONS).replace("'", '').replace(',', '').lower()
            if (MIN_LENGTH <= len(term) <= MAX_LENGTH):
                terms.append(term)
                
        terms = list(unique_everseen(terms)) # remove duplicates, but keep order of terms
        return terms


    def build_search_info(self, q):
        """
        This method will do two things:
        
        (1) It will build multi-word search terms to search against two types of fields:


            - STRING fields with `containsMultipleWords`=True and `searchType`=EXACT_SEARCH_TYPE
              Example: 
                 "John Smith" matching exactly against a field called `name`.


            - DATE/DATETIME fields with `searchType`=EXACT_SEARCH_TYPE
              Example:
                 "Mar 1, 2014" matching exactly against a field called `date`.
        
            
            Note that we do not need to care about searching multiple words under any other
                 conditions because:
            
                 (a) Other types cannot have multiple words in it, such as a number,
                     which might have a value like 1 or 101.29.
        
                 (b) Non-exact matches (edge, contains) will search **within** that value
                     for that match and not just the entire value itself.


        (2) It will build single-term search terms to search against acceptable fields based on
            various attributes in the COLUMN_METADATA, such as:
        
            - type                     (all types)
            - searchType               (all types)
            - minValue, maxValue       (numeric, date/time types)
            - minLength, maxLength     (string type)
            - isAllLower, isAllUpper   (string type)
            - containsNumericStart     (string type)
            - containsMultipleWords    (string type)

        
        Additionally, it is important to understand that a string field can contains ANY
        type. Take the following two examples:
        
          `start_date`
          Mar 1, 2019
          NOW
        
        In the above, a term `NOW` has been used to denote something such as SQL's NOW() function.
        However, our parser has not been able to detect this and so has determined this as a string field,
        Even though it is 'meant to be' a date field. 
        
        This means that any type can be within the STRING field, either due to incorrect parsing, mixed-type,
        Or various othe reasons. Because of this, we will have a metadata field which will indicate whether
        the string field `containsDate`, `containsDecimal`, etc.
        
        Additionally, take the following example:
        
          `title`
          Terminator 2
          Once on Mar 1, 2014 at 01:02:03 I had 42.01 dollars. It is True!
          Another title
        
        We can see in the example above for various values in a field with containsMultipleWords=True,
        that we can have any type contained in that field, and so it's of no use to filter out any terms
        that may not seem (at first glance) to fit the string pattern.
        

        """
        terms = self.SEARCH_INFO['TokenizedSearch'] = self.tokenize(q)
        terms_as_cleaned_string = ' '.join(terms)

        
        # PART 1. Build multi-word patterns on string & date/time fields with SEARCH_TYPE_EXACT
        #         And we handle all the date-time stuff here as well.
        for field, field_info in self.COLUMN_INFO.items():
            
            
            if (field_info['searchType'] == SEARCH_TYPE_EXACT):
                
                # (a) String
                if (field_info.get('containsMultipleWords') is True):
                    term = terms_as_cleaned_string
                    search_against_obj = {
                        'Tokens': set(tokens),
                        'Field': field,
                        'searchType': SEARCH_TYPE_EXACT,
                        'dataType': SEARCH_TYPE_STRING,
                        'searchAs': term,
                        'dateTypeFormat': None,
                        '_AllowIncompleteMatch': False
                    }
                    if search_against_obj not in self.SEARCH_INFO['Parsed']: 
                        self.SEARCH_INFO['Parsed'].append(search_against_obj)
                    
                    
                # (b) Date/Time
                elif (field_info['type'] in (DATA_TYPE_DATE, DATA_TYPE_DATETIME, DATA_TYPE_TIME)):
                    regex_pattern = ACCEPTABLE_REGEX_DATETIME_PATTERNS if (field_info['type'] == DATA_TYPE_DATETIME) else ACCEPTABLE_REGEX_TIME_PATTERNS if (field_info['type'] == DATA_TYPE_TIME) else ACCEPTABLE_REGEX_DATE_PATTERNS
                    dt_regex = re.compile( '|'.join( regex_pattern) )
                    all_terms = re.findall(dt_regex, terms_as_cleaned_string)
                    for term in all_terms:
                        mapped_terms = term.split()
                        # Because it's exact, we can convert it into serialTime and do a straight match!
                        search_against_obj = {
                            'Tokens': set(mapped_terms),
                            'Field': field,
                            'searchType': SEARCH_TYPE_EXACT,
                            'dataType': field_info['type'],
                            'searchAs': excel_date(term),
                            'dateTypeFormat': field_info['dateTypeFormat'],
                            '_AllowIncompleteMatch': False
                        }
                        if search_against_obj not in self.SEARCH_INFO['Parsed']: 
                            self.SEARCH_INFO['Parsed'].append(search_against_obj)


        # PART 2. Build single-word patterns based on acceptable fields, order does not matter now
        terms = set(terms)

        for num, term in enumerate(terms):
            
            
            # Let's get basic information on the term in question
            # So that we can skip columns that are not of that type
            term_is_string, term_is_decimal, term_is_integer = False, False, False
            try:
                float(term)
            except:
                term_is_string = True
            else:
                term_is_integer = float(term) == int(float(term))
                term_is_decimal = not term_is_integer
                term_is_string = term[0] == '0' # Allow a leading 0 item, such as "0005" to be treated as both a string a number
                                                # Depending on the column it is compared against
                
                
            valid_fields_to_search_against = []
            for field, field_info in self.COLUMN_INFO.items():
                
                # print 'Term: %s | IsString: %s | IsInteger: %s | IsDecimal: %s' % (term, term_is_string, term_is_integer, term_is_decimal)


                # (1) SEARCH OFF SKIPS
                # Skip the field if it's turned off entirely
                if field_info['searchType'] == SEARCH_TYPE_OFF:
                    continue


                # (2) MULTI-WORD SKIPS
                # Skip the field if it's already been covered in the multi-word search previously
                # For example: if the term "Terminator 2" has already been added to a `title` field,
                #              we do not need to add it a second time as "Terminator" and "2"
                if (field_info['searchType'] == SEARCH_TYPE_EXACT) and ((field_info.get('containsMultipleWords') is True) or (field_info['type'] in (DATA_TYPE_DATE, DATA_TYPE_DATETIME))):
                    continue
                    
                
                # (3) NUMERIC SKIPS
                # 1) Skip the field if it's numeric and the term is not a number
                #    Example: "hello" should skip the field `price` (int)
                # 2) Skip the field if it's > MAX_NUMBER or < MIN_NUMBER
                #    Example: 123455 will never match a field that is a TINYINT(1)
                # 3) Skip the field if the field is an integer and there is a non-zero decimal place in it
                if field_info['type'] in (DATA_TYPE_INTEGER, DATA_TYPE_DECIMAL):
                    if term_is_string:
                        continue
                    elif (field_info['maxValue'] is not None and (float(term) > field_info['maxValue'])) or (field_info['minValue'] is not None and float(term) < field_info['minValue']):
                        continue
                    elif (field_info['type'] == DATA_TYPE_INTEGER) and (float(term) != int(float(term))):
                        continue
                        

                # (4) BOOLEAN SKIPS
                # Just allow an exact match on boolean values regardless of the search type
                # For example, if someone enters in "rue", it won't match on True/true
                if (field_info['type'] == DATA_TYPE_BOOLEAN) and (term not in POSSIBLE_BOOLEAN_VALUES):
                    continue


                # (5) DATE/TIME SKIPS
                # Allow it to search if it's number between length 1 and 4, or it's part of the date-prefix, such as "Mar", "May", etc.
                if (field_info['type'] == DATA_TYPE_TIME) and not re.match(r'^\d{0,2}:?\d{0,2}:?\d{0,2}\.?\d{0,10}$', term):
                    continue
                if field_info['type'] in (DATA_TYPE_DATE, DATA_TYPE_DATETIME) and (term not in POSSIBLE_MONTH_STARTSWITH) and (re.sub(r'\s|:|-|\.', term).isdigit()):
                    continue
                
                
                # (6) STRING SKIPS
                # - First, if it's a CONTAINS search it could contain anything, so we cannot ignore anything.
                #   For example: "hello171.02Mar" contains a string, contains a number, contains a date pattern, etc.
                # - We can store metadata on whether the string field (without multiple words) startswith a numericValue.
                #   For example, if the string fields only values are ['yes', 'no'], then if there's an integer term we can skip that field.
                if (field_info['type'] == DATA_TYPE_STRING) and field_info['searchType'] != SEARCH_TYPE_CONTAINS:
                    if (term[0].isdigit()) and (field_info['containsNumericStart'] is False):
                        continue
                    if (field_info['maxLength'] is not None and (len(term) > field_info['maxLength']) or (field_info['minLength'] is not None and len(term) < field_info['minLength'])):
                        continue

                
                # Insert the term as follows:
                # As a cased-String if that field is a stringType and is allUpper or allLower
                # As a number if the field is of a numericType
                # Otherwise insert the term as a string
                if field_info['type'] == DATA_TYPE_STRING:
                    formatted_term = term.upper() if field_info.get('isAllLower') else term.lower() if field_info.get('isAllLower') else term
                elif field_info['type'] in (DATA_TYPE_INTEGER, DATA_TYPE_DECIMAL):
                    formatted_term = term if (field_info['searchType'] != SEARCH_TYPE_EXACT) else float(term) if term_is_decimal else int(term)
                elif field_info['type'] in (DATA_TYPE_DATE, DATA_TYPE_DATETIME, DATA_TYPE_TIME):
                    # full patterns are searched at the beginning, so can just keep things as a string
                    formatted_term = term
                elif field_info['type'] == DATA_TYPE_BOOLEAN:
                    formatted_term = True if term in POSSIBLE_BOOLEAN_TRUE_VALUES else False
                else:
                    formatted_term = term
                    
                search_against_obj = {
                    'Tokens': set([term,]),
                    'Field': field,
                    'searchType': field_info['searchType'],
                    'dataType': field_info['type'],
                    'searchAs': formatted_term,
                    'dateTypeFormat': field_info['dateTypeFormat'],
                    '_AllowIncompleteMatch': False,
                }
                
                # If the containsMultipleWords field has not been set yet (i.e., it is None)
                # Then we must treat a SEARCH_TYPE_EXACT search as a SEARCH_TYPE_EDGE because
                # We've broken up all keywords.
                # EXAMPLE:
                #     Search ==> "Terminator 2"
                #     Tokenized As: ['Terminator', '2']
                #     When we search these words individually, both "Terminator" and "2"
                #     Will fail when doing an exact match against "Terminator 2".
                #     Thus, with an unknown "containsMultipleWords", we must downgrade an Exact string search.
                if (field_info['searchType'] == SEARCH_TYPE_EXACT) and (field_info['type'] == DATA_TYPE_STRING) and (field_info['containsMultipleWords'] is None):
                    search_against_obj['_AllowIncompleteMatch'] = True
                
                
                if search_against_obj not in self.SEARCH_INFO['Parsed']: 
                    self.SEARCH_INFO['Parsed'].append(search_against_obj)


        # Do basic sorting of the Search terms:
        # First by matchType (EXACT will be faster than CONTAINS)
        # Second, by number of terms it contains, in case we can knock out multiple terms at once.
        self.SEARCH_INFO['Parsed'] = sorted(self.SEARCH_INFO['Parsed'], key=lambda x: (x['searchType'], -len(x['Tokens'])))
        return self.SEARCH_INFO
        

    def check_if_search_can_be_skipped(self):
        """
        If it would be possible to get a match based on our parsing info, then
        there is no need to search.
        
        An example of this would be:
        
            - We have two numeric fields and one string field.
            - Sometimes types in "searchasdfoh", which is longer than the maxCharLength of 
              the string field and will not match either numeric fields. Thus, no need to search.
        """
        tokens_in_raw_search = set(self.SEARCH_INFO['TokenizedSearch'])
        tokens_from_parsing = set()
        for token_list in [item['Tokens'] for item in self.SEARCH_INFO['Parsed']]:
            for token in token_list:
                tokens_from_parsing.add(token)

        missing_tokens = tokens_in_raw_search - tokens_from_parsing
        self.SEARCH_INFO['MissingTokens'] = missing_tokens
        # print 'TokensFromSearch: %s | TokensFromParsing: %s | MissingTokens: %s' % (tokens_in_raw_search, tokens_from_parsing, missing_tokens)
        return len(missing_tokens) > 0



    def format_dt_value(self, v, dt, df):
        
        if dt not in (DATE_TYPE_DATE, DATA_TYPE_DATETIME, DATA_TYPE_TIME):
            raise TypeError()
            
        if df not in DT_FORMATS:
            df = TIME_FORMAT_1 if dt == DATE_TYPE_TIME else DATETIME_FORMAT_1 if  dt == DATE_TYPE_DATETIME else DATE_FORMAT_1

         
        if dt == DATA_TYPE_TIME:
            base_dt = datetime.datetime(1900, 1, 1) # gives an error because before 1900
        else:
            base_dt = datetime.datetime(1899, 12, 30) + datetime.timedelta(days=v)
            
        formatted_string = (base_dt + datetime.timedelta(days=v)).strftime(df).lower()

        return formatted_string
            
        

    def search_all(self):
        
        matches_at_index = set()
        
        term_objs = self.SEARCH_INFO['Parsed']
        original_search_string = self.SEARCH_INFO['OriginalSearch'].lower()
        matches_needed = len(self.SEARCH_INFO['TokenizedSearch'])
        
        for idx, row in enumerate(self.data):
            
            if idx % 25000 == 0: print idx
            
            # Debugging
            if idx == 100000: break # UNCOMMENT FOR TESTING (for quicker testing)
            # if 3753 not in row: continue # to test an exact row match
            
            has_row_match = False
            fields_with_partial_matches = {}
            field_to_cast_value = {}
            matched_terms = set()
            skip_columns = set()   # If that column is already matched to a term
                                   # And not a multi-word column, don't allow it to be searched for another term

            for term_obj in term_objs:

                term = term_obj['searchAs']
                search_type = term_obj['searchType']
                data_type = term_obj['dataType']
                field = term_obj['Field']
                tokens = term_obj['Tokens']
                date_type_format = term_obj.get('dateTypeFormat')
                field_value = row[self.COLUMN_INFO[field]['index']]
                has_term_match = False
                
                
                if field in skip_columns:
                    continue

                if search_type == SEARCH_TYPE_EXACT:

                    if term == field_value:
                        [matched_terms.add(token) for token in tokens]
                        has_term_match = True

                    if (not has_term_match) and (term_obj['_AllowIncompleteMatch'] is True): # treat as an edgesearch
                        if not any([self.COLUMN_INFO[field]['isAllUpper'], self.COLUMN_INFO[field]['isAllLower']]):
                            field_value = field_value.lower()
                        if re.search(r'\b%s' % term, field_value):
                            fields_with_partial_matches.append(field)
                            [matched_terms.add(token) for token in tokens]
                            has_term_match = True

                else:
                    

                    # Almost no performance loss when comparing two numbers, so why not try on an exact match to start
                    if isinstance(term, (int)) and (term == field_value):
                        [matched_terms.add(token) for token in tokens]
                        has_term_match = True

                    if not has_term_match:
                        
                        # Cast the value to a string if it's not already
                        # We store a lookup for the row so, for example
                        # We don't cast a date to a string 100 times if

                        # Dates must be cast to a string based on their dataTypeFormat,
                        # So, for example, we can compare "mar" against "mar 1, 2014".
                        # Or, we can compare "2014-01" against "2014-01-01".
                        if field not in field_to_cast_value:
                        
                            if data_type in (DATA_TYPE_DATE, DATA_TYPE_DATETIME, DATA_TYPE_TIME):
                                field_value = self.format_dt_value(v=field_value, dt=data_type, df=date_type_format)
                            elif (data_type == DATA_TYPE_STRING) and not any([self.COLUMN_INFO[field]['isAllUpper'], self.COLUMN_INFO[field]['isAllLower']]):
                                field_value = field_value.lower() # compare against lower since the searchTerm will be lowered
                            else:
                                field_value = field_value
                                
                            field_to_cast_value[field] = field_value
                        
                        field_value = field_to_cast_value[field]
                            

                        if search_type == SEARCH_TYPE_STARTSWITH:
                            if field_value.startswith(term):
                                [matched_terms.add(token) for token in tokens]
                                has_term_match = True

                        elif search_type == SEARCH_TYPE_EDGE:
                            if re.search(r'\b%s' % term, field_value):
                                [matched_terms.add(token) for token in tokens]
                                has_term_match = True

                        elif field_value == SEARCH_TYPE_CONTAINS:
                            if term in field_value:
                                [matched_terms.add(token) for token in tokens]
                                has_term_match = True

                if has_term_match:
                    
                    # Break out of the `row` loop if we have a full match
                    if len(matched_terms) == matches_needed:
                        has_row_match = True
                        break

                    # Add in that column to skip if it's not a multi-word column
                    if (data_type != DATA_TYPE_STRING) or (self.COLUMN_INFO[field]['containsMultipleWords'] is False):
                        skip_columns.add(field)


            if has_row_match:

                if not fields_with_partial_matches:
                    matches_at_index.add(idx)
                else:
                    # This is simple, we can just do a reverse search
                    # -- Take the field's value and search against the raw search string
                    is_ok = True
                    for field in fields_with_partial_matches:
                        # make sure all terms match
                        if row[field].lower() not in original_search_string:
                            is_ok = False
                            break
                    if is_ok:
                        matches_at_index.add(idx)


        self.matches_at_index = matches_at_index
        self.SEARCH_INFO['NumResults'] = len(matches_at_index)
        self.SEARCH_INFO['FirstTenResults'] = [self.data[idx] for idx in sorted(matches_at_index)[:10]]
        return


    def search(self, q):
        self.SEARCH_INFO['OriginalSearch'] = q
        self.build_search_info(q)
        
        # Don't search if we don't need to
        if self.check_if_search_can_be_skipped():
            print 'Skipping search due to missing tokens: %s' % str(self.SEARCH_INFO['MissingTokens'])

        self.search_all()


if __name__ == '__main__':
    from sys import argv
    q = ' '.join(argv[1:])
    print "Initializing Data..."
    s = Search()
    t0 = time.time()
    s.search(q)
    print json.dumps(s.SEARCH_INFO, indent=4, sort_keys=True, default=set_default)
    print "\nFound %s matches." % s.SEARCH_INFO['NumResults'],
    if s.SEARCH_INFO['NumResults']:
        print "First %s result%s:\n%s" % (min(10, s.SEARCH_INFO['NumResults']), 's' if s.SEARCH_INFO['NumResults'] > 1 else '', s.SEARCH_INFO['FirstTenResults']),
    print '\nRan search in %.4f' % (time.time() - t0)





