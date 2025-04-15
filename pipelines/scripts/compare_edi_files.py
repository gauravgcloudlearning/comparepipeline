import difflib
import sys
import os

def compare_edi_files(file1_path, file2_path, output_html_path):

    print(f"received parameters:*" )
    print(f"file_path : {file1_path}")
    print(f"file_path : {file2_path}")
    print(f"file_path : {output_html_path}")
  
    # if not os.path.exist(file1_path):
    #   raise FileNotFoundError(f"File file1_path not found: {file1_path})
    # if not os.path.exist(file2_path):
    #   raise FileNotFoundError(f"File file2_path not found: {file1_path})


   

    """ Compare 2 edi files and generate side by side HTML report """
    with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
        file1_lines = file1.readlines()
        file2_lines = file2.readlines()

        html_diff = difflib.HtmlDiff(tabsize=4, wrapcolumn=80)
        diff_html = html_diff.make_file(
          file1_lines,
          file2_lines,
          fromdesc="File1 ",
          todesc="File 2"
        )

        with open (output_html_path, 'w') as output_file:
          output_file.write(diff_html)
if __name__ == "__main__":
    if (len(sys.argv) != 4):
        print("Usage: python compare_edi_files.py <file1> <file2> <output_html>")
        sys.exit(1)
    file1_path = sys.argv[1]
    file2_path = sys.argv[2]
    output_html_path = sys.argv[3]
    compare_edi_files(file1_path, file2_path, output_html_path)
