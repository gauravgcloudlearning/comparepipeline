import streamlit as st
import json
import html
from dictdiffer import diff

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
    except json.JSONDecodeError:
        return "Error: Invalid JSON file(s)."

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

st.title("JSON Comparison Tool with Pretty Printing")
st.write("Upload two JSON files to see color-coded differences between them.")

col1, col2 = st.columns(2)
with col1:
    uploaded_file1 = st.file_uploader("Upload First JSON File", type=["json"], key="file1")
with col2:
    uploaded_file2 = st.file_uploader("Upload Second JSON File", type=["json"], key="file2")

indent_size = st.slider("Indentation Size", min_value=1, max_value=8, value=2, step=1)

if uploaded_file1 and uploaded_file2:
    try:
        # Reset file pointers
        uploaded_file1.seek(0)
        uploaded_file2.seek(0)
        
        html_output = compare_json_colored(uploaded_file1, uploaded_file2)
        
        st.subheader("Side-by-Side Comparison with Color Coding")
        st.write("- Green: Added in File 2")
        st.write("- Red/Salmon: Removed (only in File 1)")
        st.write("- Yellow: Changed values")
        
        st.components.v1.html(html_output, height=800, scrolling=True)
        
        st.download_button(
            label="Download Comparison as HTML",
            data=html_output,
            file_name="json_comparison.html",
            mime="text/html",
        )
    except Exception as e:
        st.error(f"Error comparing files: {str(e)}")
else:
    st.info("Please upload two JSON files to compare.")
