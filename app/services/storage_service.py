import os
from fastapi import UploadFile
from supabase import create_client, Client

class StorageService:
    """Service to handle file uploads to Supabase Storage."""
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        # If credentials are not set, provide a dummy client for local development
        if supabase_url and supabase_key and "your-supabase" not in supabase_key:
            self.client: Client = create_client(supabase_url, supabase_key)
            self.bucket_name = "knowledge_base"
        else:
            self.client = None

    async def upload_file(self, file: UploadFile, path: str) -> str:
        """Uploads a file to Supabase storage and returns the public URL."""
        if not self.client:
            # Fallback for local development if Supabase is not configured
            # In a real scenario, you'd save it locally
            return f"local://{path}"

        # Read file content
        content = await file.read()
        
        # Upload to Supabase
        res = self.client.storage.from_(self.bucket_name).upload(
            file=content,
            path=path,
            file_options={"content-type": file.content_type}
        )
        
        # Reset file pointer if someone else needs to read it
        await file.seek(0)
        
        # Get public URL
        return self.client.storage.from_(self.bucket_name).get_public_url(path)

    async def download_file(self, path: str) -> bytes:
        """Downloads a file from Supabase storage."""
        if not self.client:
            return b""
        
        res = self.client.storage.from_(self.bucket_name).download(path)
        return res
