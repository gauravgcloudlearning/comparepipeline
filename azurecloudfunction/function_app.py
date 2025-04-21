import azure.functions as func
# from compare_multiple_edi_files import process_all_files
from azure.storage.blob import BlobServiceClient
import os
import uuid
import datetime
import json
import logging
import difflib

app = func.FunctionApp()

@app.function_name(name="EdiCompare")
@app.route(route="compare", auth_level=func.AuthLevel.ANONYMOUS)
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    connect_str = os.environ.get("BlobStorageConnectionString")
    if not connect_str:
        return func.HttpResponse(
            "Error : BlobStorageConnectionstring environment variable is not set.",
            status_code=500
        )

    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    # container setup
    from_container = blob_service_client.get_container_client("fromdata")
    to_container = blob_service_client.get_container_client("todata")
    results_container = blob_service_client.get_container_client("edicompareresults")

    try:
        process_all_files_azure(from_container, to_container, results_container)
        return func.HttpResponse("Processing completed", status_code=200)
    except Exception as e:
        return func.HttpResponse(f"Error processing files : {str(e)}", status_code=500)


def download_and_decode(blob_client):
    try:
        download_stream = blob_client.download_blob(max_consurrency=4)
        content = download_stream.readall()
        return content.decode('utf-8')
    except Exception as e:
        print(f"Download failed for {blob_client.blob_name}: {str(e)}")



def process_all_files_azure(from_container, to_container, results_container):
    # list all blobs in from container
    from_blobs = list(from_container.list_blobs(name_starts_with="edi"))
    for blob in from_blobs:
        # Extract UUID from filename       
        parts_from = blob.name.split('_')
        uuid_part = parts_from[1].split('.')[0]


        # # get matching toData blob
        to_blob_name = f"{parts_from[0]}bla_{uuid_part}.txt"
        to_blob = to_container.get_blob_client(to_blob_name)
        print(f" to_blob_name: {to_blob_name}")   
        print(f" blob.name: {blob.name}")

        if to_blob.exists():
            # download files
            from_blob_client = from_container.get_blob_client(blob.name)

            from_content = from_blob_client.download_blob().readall().decode()
            to_content = to_blob.download_blob().readall().decode()
            # from_content = download_and_decode(from_container.download_blob(blob.name))
            # to_content = download_and_decode(to_container.download_blob(to_blob_name))            
            print(f" from_content: {from_content}")   
            print(f" to_content : {to_content}")
            # Generate diff
            html_diff = difflib.HtmlDiff().make_file(
                from_content.splitlines(),
                to_content.splitlines(),
                fromdesc=blob,
                todesc=to_blob_name
            )
            print(html_diff) 
            # upload results
            report_name = f"{parts_from[0]}_{uuid_part}_report.html"
            results_container.upload_blob(
                name=report_name,
                data=html_diff
                # overrite=True
            )
