## Search Example

### Run

```
# everything after `search.py` is the search string
$ python search.py hdbuy 4.99 2014-01-01 mar. 4, 2014 01:02:0 terminator 2
```

### Helper File
I have added in a helper file, `Sales1M_WasmFormatted.json` to emulate what the data looks like in wasm.
For example, having a date stored as a number instead of the string `"2014-01-01"`.

### Search Builder
The `search.py` file is where all the tokenizing and search logic occurs.
I have not yet done the actual searching, but the pre-analysis of the search terms
to see which fields can be searched. Here are some high-level notes:

- I've tried to add extensive comments throughout the Class to explain all the logic.
- The `self.COLUMN_METADATA` gives all the information about a field. Only 'type' and 'searchType' are required. Everything else can be discussed to clarify, but to start with, you can set everything except those two required fields to None. 
- We can skip searches entirely if we know from the pre-analysis of the search terms that there cannot be a match. For example, if I search for "hello" and there are only numeric fields, we don't even need to do a search in the first place. This is the method called `check_if_search_can_be_skipped()`.
- Terms will be formatted where possible. For example, if we have the date "mar. 2, 2014" as part of the search, we can pass that as a SerialNumber when comparing against the DATE field if an exact match. 
- As a corollary to formatting terms, we also have to match it back to the original term so we know whether the full search string was matched. For example, if the entire search string is "Mar. 2, 2014" and we match on the SerialNumber (12345 or whatever it is), then we need to know that that SerialNumber matches back against three search terms: "Mar", "2", and "2014" and therefore is a complete match. This information is available in `self.SEARCH_INFO`
- I wasn't sure what the exact SerialNumber date format we use is (for example, is "2014-01-01" represented as 41640 or 41640e3 or 41640e6 etc.). You'll make to review to make sure my utility function `excel_date()` is actually valid.
- Just to repeat, the actual searching has not been done yet in this script, only the pre-analysis of the search against the data.


Here is a video briefly showing some information about the search-analyzer: https://gyazo.com/1817569801acee591b9b255dda30245f
