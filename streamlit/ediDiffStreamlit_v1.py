import streamlit as st
import difflib
def generate_side_by_side_diff (file1_content, file2_content):
    html_diff = difflib.HtmlDiff(tabsize=4, wrapcolumn=80)

    diff_html = html_diff.make_file(
        file1_content.splitlines(),
        file2_content.splitlines(),
        fromdesc="File 1",
        todesc="File 2"
    )
    return diff_html    


st.title("Azure Pipeline tester for EDI File compare")

file1 = st.file_uploader("Upload fist edi file", type=['edi','txt'])
file2 = st.file_uploader("Upload second edi file", type=['edi','txt'])

if file1 and file2:
    file1_content = file1.getvalue().decode("utf-8")
    file2_content = file2.getvalue().decode("utf-8")

    diff_html = generate_side_by_side_diff(file1_content, file2_content)

    st.subheader("Comparision Results")
    # st.markdown(diff_html, unsafe_allow_html=True)
    st.components.v1.html(diff_html, height=800, scrolling=True)

    diff_report = "\n".join(difflib.unified_diff(
        file1_content.splitlines(),
        file2_content.splitlines(),
        fromfile="File 1",
        tofile="File 2"
    ))

    st.download_button(
        label="Diff",data=diff_report,
        file_name="edi_diff_report.txt",
        mime="text/plain"
    )

    # st.markdown(""" 
    #   <style>
    #     div[data-testid="stMarkdown"] code {
    #         white-space: pre-wrap;
    #     }        
    #   </style>          
    # """, unsafe_allow_html=True)

    # with st.expander("Show Differences", expanded=True):
    #     display_diff(file1_content, file2_content)
