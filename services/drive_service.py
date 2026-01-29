import io
import logging
import google.auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from docx import Document

logger = logging.getLogger(__name__)

def get_drive_service():
    """Drive APIクライアントを構築"""
    creds, _ = google.auth.default()
    return build('drive', 'v3', credentials=creds)

def download_file_to_stream(file_id: str) -> io.BytesIO:
    print("drive_service.download_file_to_stream...")
    try:
        service = get_drive_service()
        request = service.files().get_media(fileId=file_id)
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        file_stream.seek(0)
        return file_stream
    except Exception as e:
        logger.exception("Download File To Stream Error")
        raise e

def read_text_from_docx_stream(file_stream: io.BytesIO) -> str:
    print("drive_service.read_text_from_docx_stream...")
    try:
        doc = Document(file_stream)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text.strip())
        return "\n".join(full_text)
    except Exception:
        logger.exception("Read Text From Docx Stream Error")
        return ""

def list_files_in_folder(folder_id: str):
    print("drive_service.list_files_in_folder...")
    try:
        service = get_drive_service()
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query, 
            fields="files(id, name)",
            pageSize=100
        ).execute()
        return results.get('files', [])
    except Exception:
        logger.exception("List Files In Folder Error")
        return []

def search_files_with_sort(query_str: str, limit=7):
    print("drive_service.search_files_with_sort...")
    try:
        service = get_drive_service()
        results = service.files().list(
            q=query_str,
            fields="files(id, name, mimeType)",
            pageSize=50 
        ).execute()
        
        files = results.get('files', [])
        valid_files = [f for f in files if not f['name'].startswith('~$')]
        sorted_files = sorted(valid_files, key=lambda x: x['name'])
        
        return sorted_files[:limit]
    except Exception:
        logger.exception("Search Files With Sort Error")
        return []

def search_image_by_name(folder_id: str, member_name: str):
    print("drive_service.search_image_by_name...")
    try:
        service = get_drive_service()
        query = f"'{folder_id}' in parents and name contains '{member_name}' and mimeType contains 'image/' and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name)",
            pageSize=1
        ).execute()
        
        files = results.get('files', [])
        if not files:
            return None
            
        return download_file_to_stream(files[0]['id'])
    except Exception:
        logger.exception("Search Image By Name Error")
        return None

def export_google_doc_text(file_id: str) -> str:
    print("drive_service.export_google_doc_text...")
    try:
        service = get_drive_service()
        request = service.files().export_media(fileId=file_id, mimeType='text/plain')
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        return file_stream.getvalue().decode('utf-8')
    except Exception:
        logger.exception("Export Google Doc Text Error")
        return ""
    
def find_folder_by_name(parent_id: str, folder_name: str):
    try:
        service = get_drive_service()
        query = f"'{parent_id}' in parents and name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name)",
            pageSize=1
        ).execute()
        
        files = results.get('files', [])
        if files:
            return files[0]['id']
        return None
    except Exception:
        logger.exception("Find Folder By Name Error")
        return None