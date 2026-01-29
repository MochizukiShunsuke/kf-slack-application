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
    """ファイルをバイナリとしてメモリ上にダウンロード"""
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
        logger.error(f"Failed to download file {file_id}: {e}")
        raise e

def read_text_from_docx_stream(file_stream: io.BytesIO) -> str:
    """.docxファイルのバイナリストリームからテキストを抽出する"""
    try:
        doc = Document(file_stream)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text.strip())
        return "\n".join(full_text)
    except Exception as e:
        logger.warning(f"Failed to read docx content: {e}")
        return ""

def list_files_in_folder(folder_id: str):
    """指定フォルダ内のファイル一覧(id, name)を取得する"""
    try:
        service = get_drive_service()
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query, 
            fields="files(id, name)",
            pageSize=100
        ).execute()
        return results.get('files', [])
    except Exception as e:
        logger.error(f"Failed to list files in folder {folder_id}: {e}")
        return []

def search_files_with_sort(query_str: str, limit=7):
    """
    クエリで検索し、ファイル名でソートして返す
    例: "01_...", "02_..." の順にするため
    """
    try:
        service = get_drive_service()
        results = service.files().list(
            q=query_str,
            fields="files(id, name, mimeType)",
            pageSize=50 
        ).execute()
        
        files = results.get('files', [])
        # ~$で始まる一時ファイルを除外し、名前順にソート
        valid_files = [f for f in files if not f['name'].startswith('~$')]
        sorted_files = sorted(valid_files, key=lambda x: x['name'])
        
        return sorted_files[:limit]
    except Exception as e:
        logger.error(f"Failed to search files: {e}")
        return []

def search_image_by_name(folder_id: str, member_name: str):
    """
    指定フォルダから「名前.jpg」「名前.png」などを探してダウンロードストリームを返す
    """
    try:
        service = get_drive_service()
        # 名前が含まれる画像ファイルを検索
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
    except Exception as e:
        logger.error(f"Failed to search image for {member_name}: {e}")
        return None

def export_google_doc_text(file_id: str) -> str:
    """Google Docをテキスト形式でエクスポート"""
    try:
        service = get_drive_service()
        request = service.files().export_media(fileId=file_id, mimeType='text/plain')
        file_stream = io.BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        return file_stream.getvalue().decode('utf-8')
    except Exception as e:
        logger.warning(f"Failed to export doc {file_id}: {e}")
        return ""