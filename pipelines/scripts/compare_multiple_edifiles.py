import os
import difflib




def compare_edi_files(file1_path, file2_path, output_html_path):
    """Compare two EDI files and generate a side by side HTML report """
    try:        
      with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
        file1_lines = file1.readlines()
        file2_lines = file2.readlines()

        html_diff = difflib.HtmlDiff(tabsize=4, wrapcolumn=80)
        diff_html = html_diff.make_file(
          file1_lines,
          file2_lines,
          fromdesc=os.path.basename(file1_path),
          todesc=os.path.basename(file2_path)
        )

        with open (output_html_path, 'w') as output_file:
          output_file.write(diff_html)
          print(f"Successfully wrote output to : {output_html_path}")
    except Exception as e:
        print(f"Error in comparing EDI files: {str(e)}")
        raise


def process_all_files(from_dir, to_dir, output_dir):
    """ Compare all EDI files in fromData with matching UUIDs in toData. """
    try :
        print(f"Processing files in directories:")
        print(f"From directory: {from_dir}")
        print(f"To directory: {to_dir}")
        print(f"Output directory: {output_dir}")    

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        
            # Iterate through files in fromData
            for from_file in os.listdir(from_dir):
                if "_" in from_file and from_file.endswith(".txt"):
                    uuid = from_file.split("_")[1].split(".")[0] # Extract UUID
                    matching_to_file = f"{from_file.split('_')[0]}bla_{uuid}.txt"
                    
                    from_file_path = os.path.join(from_dir, from_file)
                    to_file_path = os.path.join(to_dir, matching_to_file)

                    if os.path.exists(to_file_path):
                        output_html_name = f"{from_file.split('_')[0]}_{uuid}_report.html"
                        output_html_path = os.path.join(output_dir, output_html_name)
                        # compare files and genereate report 
                        compare_edi_files(from_file_path, to_file_path, output_html_path)
                    else:
                        print(f"No matching files found for UUID '{uuid}' in toData.")
    except Exception as e:
        print(f"Error in process_all_files : {str(e)}")
        raise

if __name__ == "__main__":
    from_dir = "edicompare/fromData"
    to_dir = "edicompare/toData"
    output_dir = "edicompareresults"

    process_all_files(from_dir, to_dir, output_dir)
