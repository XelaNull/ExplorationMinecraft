# Python Compatibility

This project requires compatibility with both Python 2.7 and Python 3+. Here are key patterns and considerations for maintaining cross-version compatibility.

## Import Statements

```python
# Python 2 and 3 compatible imports
try:
    # Python 3
    from urllib.request import urlopen
    from urllib.parse import urlencode
except ImportError:
    # Python 2
    from urllib2 import urlopen
    from urllib import urlencode
```

## Print Statements

```python
# Always use print function, not statement
from __future__ import print_function

print("Hello world")  # Works in both Python 2.7 and 3+
```

## String Handling

```python
# String literals
from __future__ import unicode_literals

# Explicit byte strings
byte_str = b"byte string"

# Explicit unicode strings
unicode_str = u"unicode string"
```

## Division

```python
# Integer division
from __future__ import division

result = 5 / 2  # 2.5 in both Python 2.7 and 3+
floor_result = 5 // 2  # 2 in both Python 2.7 and 3+
```

## Exception Handling

```python
# Python 2 and 3 compatible exception handling
try:
    some_operation()
except Exception as e:  # not 'except Exception, e:'
    print("Error: {}".format(e))
```

## Iterators and Dictionaries

```python
# Use list() to materialize iterators in Python 3
items = list(some_dict.items())  # instead of some_dict.items() in Python 2

# Prefer .items() over .iteritems() with conditional logic
if hasattr(some_dict, 'iteritems'):
    # Python 2
    for key, value in some_dict.iteritems():
        pass
else:
    # Python 3
    for key, value in some_dict.items():
        pass
```

## File I/O

```python
# Binary mode explicitly for both versions
with open(filename, 'rb') as f:
    data = f.read()

# Text mode with encoding for both versions
import io
with io.open(filename, 'r', encoding='utf-8') as f:
    text = f.read()
```

## Standard Library Changes

Key modules with different locations:
- `ConfigParser` (Python 2) → `configparser` (Python 3)
- `Queue` (Python 2) → `queue` (Python 3)
- `StringIO` and `cStringIO` (Python 2) → `io.StringIO` (Python 3)
- `urllib`, `urllib2`, `urlparse` (Python 2) → `urllib.request`, `urllib.parse` (Python 3)

## Type Checking

```python
# Check for string types
import sys
PY2 = sys.version_info[0] == 2

if PY2:
    string_types = (str, unicode)
else:
    string_types = (str,)

# Usage
if isinstance(obj, string_types):
    # String handling code
```

## Six Library

Consider using the `six` library for more complex compatibility needs:

```python
import six

# String types
if isinstance(obj, six.string_types):
    pass

# Integer types
if isinstance(obj, six.integer_types):
    pass

# Iterators
for key, value in six.iteritems(some_dict):
    pass
```

## JSON Handling

```python
import json

# Encoding with proper string handling
json_str = json.dumps(data)

# Decoding with proper string handling
data = json.loads(json_str)
``` 