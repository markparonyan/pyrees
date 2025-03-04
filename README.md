# pyrees - code quality checker
Long time ago, Michael Rees [published](https://dl.acm.org/doi/abs/10.1145/948086.948088) a method of evaluating the elegance and prettiness of Pascal programs. 
This is an implementation of this algorithm in Python for Python programs.

## Usage
`python pyrees.py <python_source_file>`

## Example
```
$ python pyrees.py pyrees.py
Style Analysis Breakdown:
  avg_line_length               : 42.99
  comment_percentage            : 12.81
  indent_percentage             : 96.00
  blank_percentage              : 13.79
  embedded_space_percentage     : 12.40
  module_length                 : 58.33
  reserved_words_count          : 15.00
  avg_identifier_length         : 7.07

Marks for each measure:
  avg_line_length               : 4.49
  comment_percentage            : 10.00
  indent_percentage             : 0.00
  blank_percentage              : 1.21
  embedded_space_percentage     : 6.93
  module_length                 : 0.00
  reserved_words_count          : 10.00
  avg_identifier_length         : 20.00

Overall Style Mark: 52.63 / 100
```
