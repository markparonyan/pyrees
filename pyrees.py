import ast
import io
import tokenize
import keyword

def conversion(measure_value, params):
    """Convert a measured value into a mark according to a conversion curve.
    
    Parameters:
      measure_value: The measured value (e.g. average line length).
      params: A tuple (max_mark, lo, lotol, hitol, hi) where:
          - max_mark: maximum mark for the measure.
          - lo: lower bound (below which mark = 0).
          - lotol: lower optimum value (mark becomes max_mark when reached).
          - hitol: upper optimum value.
          - hi: upper bound (above which mark = 0).
    
    Returns:
      A mark (between 0 and max_mark) for this measure.
    """
    max_mark, lo, lotol, hitol, hi = params
    if measure_value < lo or measure_value > hi:
        return 0
    elif lotol <= measure_value <= hitol:
        return max_mark
    elif lo <= measure_value < lotol:
        return max_mark * (measure_value - lo) / (lotol - lo)
    elif hitol < measure_value <= hi:
        return max_mark * (hi - measure_value) / (hi - hitol)
    else:
        return 0

def analyze_style(code):
    """Analyze the style of a Python program by Michael Rees algorithm.
    
    The following measures are calculated:
    
      1. Average significant line length (after stripping leading/trailing spaces).
      2. Percentage of lines containing comments (using tokenize to detect COMMENT tokens).
      3. Percentage of non-blank lines that are indented.
      4. Percentage of blank lines (lines that are empty or only whitespace).
      5. Embedded spaces: the overall percentage of spaces within stripped lines.
      6. Module (function) length: calculated as the average number of non-blank lines per module.
         A module here is defined as either a function (found via the AST) or the top‐level code.
      7. Variety of reserved words: the number of distinct Python keywords used.
      8. Average identifier length: average length of programmer-defined names (excluding keywords).
      
    Measures 9 (variety of identifiers) and 10 (labels/gotos) are not used in this implementation.
    
    Each measure is then converted to a mark via a parameterized conversion curve.
    The total style mark is the sum of the converted marks (with measure 10 subtracted).
    
    Parameters:
      code: A string containing the Python source code.
    
    Returns:
      A dictionary with raw measure values, the mark obtained for each measure,
      and the overall style mark (out of 100).
    """
    lines = code.splitlines()
    total_lines = len(lines)
    non_blank_lines = [line for line in lines if line.strip() != ""]
    n_non_blank = len(non_blank_lines)
    
    # Measure 1: Average line length (significant characters)
    if n_non_blank > 0:
        avg_line_length = sum(len(line.strip()) for line in non_blank_lines) / n_non_blank
    else:
        avg_line_length = 0

    # Use tokenize to get comment tokens and to later analyze names.
    comment_lines = set()
    try:
        tokens = list(tokenize.tokenize(io.BytesIO(code.encode('utf-8')).readline))
        for tok in tokens:
            if tok.type == tokenize.COMMENT:
                # Record the line number where the comment appears.
                comment_lines.add(tok.start[0])
    except Exception:
        tokens = []
    
    # Measure 2: Comment percentage (percentage of total lines that contain comments)
    comment_percentage = (len(comment_lines) / total_lines * 100) if total_lines > 0 else 0

    # Measure 3: Indentation percentage (of non-blank lines, those that start with whitespace)
    indented_lines = [line for line in non_blank_lines if line.startswith(" ") or line.startswith("\t")]
    indent_percentage = (len(indented_lines) / n_non_blank * 100) if n_non_blank > 0 else 0

    # Measure 4: Blank lines percentage
    blank_lines = [line for line in lines if line.strip() == ""]
    blank_percentage = (len(blank_lines) / total_lines * 100) if total_lines > 0 else 0

    # Measure 5: Embedded spaces percentage.
    # For each non-blank line (after stripping), count the spaces.
    total_embedded_spaces = sum(line.strip().count(" ") for line in non_blank_lines)
    total_chars = sum(len(line.strip()) for line in non_blank_lines)
    embedded_space_percentage = (total_embedded_spaces / total_chars * 100) if total_chars > 0 else 0

    # Measure 6: Module (function) length.
    # Count the number of function definitions using the AST.
    try:
        tree = ast.parse(code)
        func_defs = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        num_funcs = len(func_defs)
    except Exception as e:
        num_funcs = 0
    # Define "modules" as functions plus the top-level module.
    modules = num_funcs + 1
    module_length = (n_non_blank / modules) if modules > 0 else n_non_blank

    # Measure 7: Variety of reserved words.
    reserved_words_set = set(keyword.kwlist)
    used_reserved_words = set()
    for tok in tokens:
        if tok.type == tokenize.NAME and tok.string in reserved_words_set:
            used_reserved_words.add(tok.string)
    reserved_words_count = len(used_reserved_words)

    # Measure 8: Average identifier length (for programmer-defined identifiers, i.e. non-keyword names).
    identifiers = [tok.string for tok in tokens if tok.type == tokenize.NAME and tok.string not in reserved_words_set]
    avg_identifier_length = (sum(len(name) for name in identifiers) / len(identifiers)) if identifiers else 0


    # *** Conversion parameters ***
    # (Each tuple is: (max_mark, lo, lotol, hitol, hi))

    # 1. Average line length (ideal: between 50 and 70, bounds: 40 and 90, max mark = 15)
    p1 = (15, 40, 50, 70, 90)
    # 2. Comment percentage (ideal: 10%-20%, bounds: 5%-30%, max mark = 10)
    p2 = (10, 5, 10, 20, 30)
    # 3. Indentation percentage (ideal: 40%-60%, bounds: 30%-70%, max mark = 12)
    p3 = (12, 30, 40, 60, 70)
    # 4. Blank lines percentage (ideal: 5%-10%, bounds: 2%-15%, max mark = 5)
    p4 = (5, 2, 5, 10, 15)
    # 5. Embedded space percentage (ideal: 7%-12%, bounds: 5%-15%, max mark = 8)
    p5 = (8, 5, 7, 12, 15)
    # 6. Module length (average lines per module; ideal: between 10 and 20, bounds: 5 and 30, max mark = 20)
    p6 = (20, 5, 10, 20, 30)
    # 7. Variety of reserved words (ideal: between 8 and 15 distinct keywords, bounds: 5 and 20, max mark = 10)
    p7 = (10, 5, 8, 15, 20)
    # 8. Average identifier length (ideal: between 7 and 15, bounds: 5 and 20, max mark = 20)
    p8 = (20, 5, 7, 15, 20)
    
    # Compute the marks for each measure using the conversion function.
    m1 = conversion(avg_line_length, p1)
    m2 = conversion(comment_percentage, p2)
    m3 = conversion(indent_percentage, p3)
    m4 = conversion(blank_percentage, p4)
    m5 = conversion(embedded_space_percentage, p5)
    m6 = conversion(module_length, p6)
    m7 = conversion(reserved_words_count, p7)
    m8 = conversion(avg_identifier_length, p8)
    
    # The overall style mark is the sum of marks for measures 1-8 minus measure 10.
    total_mark = m1 + m2 + m3 + m4 + m5 + m6 + m7 + m8 

    # Compile the results in a dictionary.
    breakdown = {
        "raw_measures": {
            "avg_line_length": avg_line_length,
            "comment_percentage": comment_percentage,
            "indent_percentage": indent_percentage,
            "blank_percentage": blank_percentage,
            "embedded_space_percentage": embedded_space_percentage,
            "module_length": module_length,
            "reserved_words_count": reserved_words_count,
            "avg_identifier_length": avg_identifier_length,
        },
        "marks": {
            "avg_line_length": m1,
            "comment_percentage": m2,
            "indent_percentage": m3,
            "blank_percentage": m4,
            "embedded_space_percentage": m5,
            "module_length": m6,
            "reserved_words_count": m7,
            "avg_identifier_length": m8,
        },
        "total_mark": total_mark
    }
    return breakdown


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pyrees.py <python_source_file>")
    else:
        file_path = sys.argv[1]
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            result = analyze_style(code)
            print("Style Analysis Breakdown:")
            for key, value in result["raw_measures"].items():
                print(f"  {key:30s}: {value:.2f}")
            print("\nMarks for each measure:")
            for key, value in result["marks"].items():
                print(f"  {key:30s}: {value:.2f}")
            print(f"\nOverall Style Mark: {result['total_mark']:.2f} / 100")
        except Exception as e:
            print(f"Error reading or analyzing file: {e}")

