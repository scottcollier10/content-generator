# application/services/brand_context.py
import os
import io
from abc import ABC, abstractmethod
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from models import BrandContext
from utils import get_app_logger

logger = get_app_logger(__name__)


def categorize_file_content(filename: str, content: str, context: BrandContext) -> None:
    """Categorize file content into appropriate brand context fields."""
    lower_name = filename.lower()

    if any(kw in lower_name for kw in ["voice", "tone"]):
        context.voice_tone += content + "\n\n"

    if any(kw in lower_name for kw in ["position", "messaging", "value_prop"]):
        context.positioning += content + "\n\n"

    if any(kw in lower_name for kw in ["audience", "persona", "icp", "segment"]):
        context.target_audience += content + "\n\n"

    if any(kw in lower_name for kw in ["copy", "example", "case", "campaign", "landing"]):
        context.example_copy += content + "\n\n"

    context.files_processed.append(filename)


class BrandContextProvider(ABC):
    """Abstract interface for brand context sources."""

    @abstractmethod
    def get_brand_context(self) -> BrandContext:
        """Fetch and return brand context."""
        raise NotImplementedError


class GoogleDriveBrandContext(BrandContextProvider):
    """Fetches brand context from Google Drive folder."""

    SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

    def __init__(self, folder_id: str, service_account_path: Optional[str] = None):
        self.folder_id = folder_id
        self.service_account_path = service_account_path or os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_JSON"
        )
        self._service = None

    def _get_service(self):
        """Get or create Google Drive service."""
        if self._service is None:
            credentials = service_account.Credentials.from_service_account_file(
                self.service_account_path,
                scopes=self.SCOPES,
            )
            self._service = build("drive", "v3", credentials=credentials)
        return self._service

    def _list_files(self) -> list[dict]:
        """List files in the brand folder."""
        service = self._get_service()
        results = service.files().list(
            q=f"'{self.folder_id}' in parents and trashed = false",
            fields="files(id, name, mimeType)",
        ).execute()
        return results.get("files", [])

    def _download_file(self, file_id: str, mime_type: str) -> str:
        """Download file content as text."""
        service = self._get_service()

        # For Google Docs, export as plain text
        if mime_type == "application/vnd.google-apps.document":
            request = service.files().export_media(
                fileId=file_id,
                mimeType="text/plain",
            )
        else:
            request = service.files().get_media(fileId=file_id)

        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        buffer.seek(0)
        try:
            return buffer.read().decode("utf-8")
        except UnicodeDecodeError:
            return buffer.read().decode("latin-1")

    def get_brand_context(self) -> BrandContext:
        """Fetch brand context from Google Drive."""
        context = BrandContext()

        try:
            files = self._list_files()
            logger.info(f"Found {len(files)} files in brand folder")

            for file_info in files:
                try:
                    content = self._download_file(
                        file_info["id"],
                        file_info["mimeType"],
                    )
                    categorize_file_content(file_info["name"], content, context)
                except Exception as e:
                    logger.warning(f"Failed to process {file_info['name']}: {e}")

            # Clean up whitespace
            context.voice_tone = context.voice_tone.strip() or "Not specified"
            context.positioning = context.positioning.strip() or "Not specified"
            context.target_audience = context.target_audience.strip() or "Not specified"
            context.example_copy = context.example_copy.strip() or "Not specified"

        except Exception as e:
            logger.error(f"Failed to fetch brand context: {e}")

        return context
