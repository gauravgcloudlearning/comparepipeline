import azure.functions as func
import logging
import json
import html
from dictdiffer import diff
from azure.storage.blob import BlobServiceClient
import os

app = func.FunctionApp()

def pretty_format_json(obj, indent=0, indent_size=2):
    """Pretty format JSON with proper indentation."""
    if obj is None:
        return "null"
    
    indent_str = " " * indent
    next_indent = indent + indent_size
    next_indent_str = " " * next_indent
    
    if isinstance(obj, dict):
        if not obj:  # Empty dict
          
            return "{}"
        
        result = "{\n"
        items = list(obj.items())
        
        for i, (key, value) in enumerate(items):
            result += f"{next_indent_str}\"{key}\": {pretty_format_json(value, next_indent, indent_size)}"
            if i < len(items) - 1:
              
                result += ","
            result += "\n"
            
        result += f"{indent_str}}}"
        return result
        
    elif isinstance(obj, list):
        if not obj:  # Empty list
            return "[]"
          
        result = "[\n"
        for i, item in enumerate(obj):
            result += f"{next_indent_str}{pretty_format_json(item, next_indent, indent_size)}"
            if i < len(obj) - 1:
                result += ","
            result += "\n"
           
        result += f"{indent_str}]"
        return result
        
    elif isinstance(obj, str):
        # Escape special characters in string
        escaped = json.dumps(obj)
        return escaped
        
    else:
        # For numbers, booleans, etc.
        return json.dumps(obj)

def color_diff_pretty(obj1, obj2, difference, path=None, indent=0, indent_size=2):
    """Generate color-coded pretty-printed JSON comparison."""

    path = path or []
    indent_str = " " * indent
    next_indent = indent + indent_size
    next_indent_str = " " * next_indent
    
    # Handle cases where one object is None (completely added or removed)
    if obj1 is None:
        pretty_obj2 = pretty_format_json(obj2, indent, indent_size)
        return "null", f'<span style="background-color: lightgreen;">{html.escape(pretty_obj2)}</span>'
   
    elif obj2 is None:
        pretty_obj1 = pretty_format_json(obj1, indent, indent_size)
        return f'<span style="background-color: lightsalmon;">{html.escape(pretty_obj1)}</span>', "null"
    
    if isinstance(obj1, dict) and isinstance(obj2, dict):
        keys1 = set(obj1.keys())
        keys2 = set(obj2.keys())
        all_keys = sorted(list(keys1.union(keys2)))
        
        html1 = "{\n"
        html2 = "{\n"
        
        for i, key in enumerate(all_keys):
            # Key only in obj1 (deleted)
            if key in keys1 and key not in keys2:
                pretty_val = pretty_format_json(obj1[key], next_indent, indent_size)
                html1 += f'{next_indent_str}<span style="background-color: lightsalmon;">"{html.escape(str(key))}": {html.escape(pretty_val)}</span>'
                if i < len(all_keys) - 1:
                    html1 += ","
                html1 += "\n"
                continue
                
            # Key only in obj2 (added)
            if key not in keys1 and key in keys2:
                pretty_val = pretty_format_json(obj2[key], next_indent, indent_size)
                html2 += f'{next_indent_str}<span style="background-color: lightgreen;">"{html.escape(str(key))}": {html.escape(pretty_val)}</span>'
                if i < len(all_keys) - 1:
                    html2 += ","
                html2 += "\n"
                continue
            
            # Key in both dictionaries
            val1 = obj1.get(key)
            val2 = obj2.get(key)
            current_path = path + [key]
            
            # Check if this exact path is in the differences
            path_in_diff = False
            for d_type, d_path, *_ in difference:
                if d_path == current_path or (isinstance(d_path, list) and d_path[:len(current_path)] == current_path):
                    path_in_diff = True
                    break
            
            # Recursive call for nested structures
            if isinstance(val1, (dict, list)) and isinstance(val2, (dict, list)):
                s1, s2 = color_diff_pretty(val1, val2, difference, current_path, next_indent, indent_size)
                html1 += f'{next_indent_str}"{html.escape(str(key))}": {s1}'
                html2 += f'{next_indent_str}"{html.escape(str(key))}": {s2}'
            else:
                # Simple values
                if val1 == val2:
                    # Values are identical
                    pretty_val = html.escape(json.dumps(val1))
                    html1 += f'{next_indent_str}"{html.escape(str(key))}": {pretty_val}'
                    html2 += f'{next_indent_str}"{html.escape(str(key))}": {pretty_val}'
                else:
                    # Values differ
                    html1 += f'{next_indent_str}"{html.escape(str(key))}": <span style="background-color: lightyellow;">{html.escape(json.dumps(val1))}</span>'
                    html2 += f'{next_indent_str}"{html.escape(str(key))}": <span style="background-color: lightyellow;">{html.escape(json.dumps(val2))}</span>'
            
            if i < len(all_keys) - 1 and key in keys1:
                html1 += ","
            if i < len(all_keys) - 1 and key in keys2:
                html2 += ","
                
        html1 += "\n"
        html2 += "\n"
                
        html1 += f"{indent_str}}}"
        html2 += f"{indent_str}}}"
        return html1, html2

    elif isinstance(obj1, list) and isinstance(obj2, list):
        len1 = len(obj1)
        len2 = len(obj2)
        max_len = max(len1, len2)
        
        html1 = "[\n"
        html2 = "[\n"
        
        for i in range(max_len):
            if i < len1 and i < len2:
                # Element exists in both lists
                val1 = obj1[i]
                val2 = obj2[i]
                current_path = path + [i]
                
                if isinstance(val1, (dict, list)) and isinstance(val2, (dict, list)):
                    s1, s2 = color_diff_pretty(val1, val2, difference, current_path, next_indent, indent_size)
                    html1 += f"{next_indent_str}{s1}"
                    html2 += f"{next_indent_str}{s2}"
                elif val1 == val2:
                    # Values are identical
                    pretty_val = html.escape(json.dumps(val1))
                    html1 += f"{next_indent_str}{pretty_val}"
                    html2 += f"{next_indent_str}{pretty_val}"
                else:
                    # Values differ
                    html1 += f'{next_indent_str}<span style="background-color: lightyellow;">{html.escape(json.dumps(val1))}</span>'
                    html2 += f'{next_indent_str}<span style="background-color: lightyellow;">{html.escape(json.dumps(val2))}</span>'
            elif i < len1:
                # Element only in obj1 (deleted)
                pretty_val = pretty_format_json(obj1[i], next_indent, indent_size)
                html1 += f'{next_indent_str}<span style="background-color: lightsalmon;">{html.escape(pretty_val)}</span>'
                # No corresponding element in html2
            else:
                # Element only in obj2 (added)
                pretty_val = pretty_format_json(obj2[i], next_indent, indent_size)
                html2 += f'{next_indent_str}<span style="background-color: lightgreen;">{html.escape(pretty_val)}</span>'
                # No corresponding element in html1
                
            if i < max_len - 1:
                if i < len1 - 1:
                    html1 += ","
                if i < len2 - 1:
                    html2 += ","
                    
            html1 += "\n"
            html2 += "\n"
                    
        html1 += f"{indent_str}]"
        html2 += f"{indent_str}]"
        return html1, html2
    else:
        # Simple values
        if obj1 == obj2:
            pretty_val = html.escape(json.dumps(obj1))
            return pretty_val, pretty_val
        else:
            return f'<span style="background-color: lightyellow;">{html.escape(json.dumps(obj1))}</span>', f'<span style="background-color: lightyellow;">{html.escape(json.dumps(obj2))}</span>'

def compare_json_colored(file1, file2):
    try:
        data1 = json.load(file1)
        data2 = json.load(file2)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON file: {str(e)}")
    difference = list(diff(data1, data2))
    colored_json1, colored_json2 = color_diff_pretty(data1, data2, difference)

    html_output = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>JSON Comparison (Colored Diff)</title>
        <style>
            body {{ font-family: monospace; display: flex; margin: 0; padding: 0; }}
            .container {{ flex: 1; padding: 20px; border: 1px solid #ccc; margin: 10px; overflow: auto; }}
            h2 {{ text-align: center; font-family: sans-serif; }}
            pre {{ white-space: pre-wrap; font-size: 14px; line-height: 1.5; }}
            .legend {{ display: flex; justify-content: center; margin-bottom: 15px; font-family: sans-serif; }}
            .legend-item {{ margin: 0 10px; padding: 2px 8px; border-radius: 3px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>File 1</h2>
            <div class="legend">
                <span class="legend-item" style="background-color: lightsalmon;">Removed</span>
                <span class="legend-item" style="background-color: lightyellow;">Changed</span>
            </div>
            <pre>{colored_json1}</pre>
        </div>
        <div class="container">
            <h2>File 2</h2>
            <div class="legend">
                <span class="legend-item" style="background-color: lightgreen;">Added</span>
                <span class="legend-item" style="background-color: lightyellow;">Changed</span>
            </div>
            <pre>{colored_json2}</pre>
        </div>
    </body>
    </html>
    """
    return html_output

@app.function_name(name="JsonCompare")
@app.route(route="compare_json", auth_level=func.AuthLevel.ANONYMOUS)
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    connect_str = os.environ.get("BlobStorageConnectionString")
    if not connect_str:
        return func.HttpResponse(
            "Error: BlobStorageConnectionString environment variable is not set.",
            status_code=500
        )

    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    from_container = blob_service_client.get_container_client("fromdata")
    to_container = blob_service_client.get_container_client("todata")
    results_container = blob_service_client.get_container_client("jsoncompareresults")  #Ensure correct container name

    try:
        process_json_files_azure(from_container, to_container, results_container)
        return func.HttpResponse("JSON comparison completed", status_code=200)
    except Exception as e:
        logging.error(f"Error processing files: {str(e)}")
        return func.HttpResponse(f"Error processing files: {str(e)}", status_code=500)

def process_json_files_azure(from_container, to_container, results_container):
    from_blobs = list(from_container.list_blobs(name_starts_with="file"))  # List all blobs in from container

    for from_blob in from_blobs:
        try:
            # Extract UUID from filename
            parts_from = from_blob.name.split('_')
            if len(parts_from) < 2:
                logging.warning(f"Skipping file {from_blob.name}: Filename does not contain expected '_' separator.")
                continue

            uuid_part = parts_from[1].split('.')[0]
            base_name = parts_from[0]

            # Construct the matching 'toData' blob name
            to_blob_name = f"{base_name}bla_{uuid_part}.json"  #Expect .json extension
            to_blob_client = to_container.get_blob_client(to_blob_name)

            if to_blob_client.exists():
                # Download file contents
                from_content = from_container.get_blob_client(from_blob.name).download_blob().readall()
                to_content = to_container.get_blob_client(to_blob_name).download_blob().readall()

                # Decode content
                from_content_str = from_content.decode('utf-8')
                to_content_str = to_content.decode('utf-8')

                # Perform JSON comparison and generate HTML report
                html_report = compare_json_colored(file1=io.StringIO(from_content_str), file2=io.StringIO(to_content_str))

                # Upload the HTML report
                report_blob_name = f"{base_name}_{uuid_part}_report.html"
                results_container.upload_blob(name=report_blob_name, data=html_report, content_type="text/html")

                logging.info(f"Comparison report generated for {from_blob.name} and {to_blob_name} -> {report_blob_name}")

            else:
                logging.warning(f"No matching file found in 'toData' for {from_blob.name} (expected: {to_blob_name})")

        except
