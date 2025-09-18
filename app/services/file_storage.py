# app/services/file_storage.py
import os
import uuid
import shutil
import mimetypes
import time
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.models.task import TaskAttachment
from app.schemas.task import TaskAttachmentCreate
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class FileStorageService:
    """Service for handling file uploads, storage, and retrieval"""
    
    def __init__(self, upload_dir: str = "uploads", max_file_size: int = 10 * 1024 * 1024):  # 10MB default
        self.upload_dir = Path(upload_dir)
        self.max_file_size = max_file_size
        self.allowed_extensions = {
            # Documents
            '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
            # Spreadsheets
            '.xls', '.xlsx', '.csv', '.ods',
            # Presentations
            '.ppt', '.pptx', '.odp',
            # Archives
            '.zip', '.rar', '.7z', '.tar', '.gz',
            # Code files
            '.py', '.js', '.html', '.css', '.json', '.xml', '.sql',
            # Other
            '.mp4', '.avi', '.mov', '.wmv', '.mp3', '.wav', '.flac'
        }
        
        # Rate limiting and quota settings
        self.rate_limits = {
            'uploads_per_minute': 10,  # Max uploads per minute per user
            'uploads_per_hour': 50,    # Max uploads per hour per user
            'uploads_per_day': 200,    # Max uploads per day per user
            'total_size_per_hour': 100 * 1024 * 1024,  # 100MB per hour per user
            'total_size_per_day': 500 * 1024 * 1024,   # 500MB per day per user
        }
        
        # Track uploads per user
        self.user_uploads = defaultdict(lambda: {
            'uploads': deque(),
            'size_uploads': deque(),
            'last_cleanup': time.time()
        })
        
        # Create upload directory if it doesn't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for organization
        (self.upload_dir / "tasks").mkdir(exist_ok=True)
        (self.upload_dir / "temp").mkdir(exist_ok=True)
    
    def _cleanup_old_uploads(self, user_id: int):
        """Clean up old upload records for a user"""
        current_time = time.time()
        user_data = self.user_uploads[user_id]
        
        # Clean up upload count records older than 1 day
        while user_data['uploads'] and current_time - user_data['uploads'][0] > 86400:  # 1 day
            user_data['uploads'].popleft()
        
        # Clean up size records older than 1 day
        while user_data['size_uploads'] and current_time - user_data['size_uploads'][0][0] > 86400:  # 1 day
            user_data['size_uploads'].popleft()
        
        user_data['last_cleanup'] = current_time
    
    def _check_rate_limits(self, user_id: int, file_size: int) -> Tuple[bool, str]:
        """Check if user has exceeded rate limits"""
        current_time = time.time()
        user_data = self.user_uploads[user_id]
        
        # Clean up old records
        if current_time - user_data['last_cleanup'] > 300:  # Clean up every 5 minutes
            self._cleanup_old_uploads(user_id)
        
        # Check upload count limits
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        day_ago = current_time - 86400
        
        # Count uploads in different time windows
        uploads_last_minute = sum(1 for t in user_data['uploads'] if t > minute_ago)
        uploads_last_hour = sum(1 for t in user_data['uploads'] if t > hour_ago)
        uploads_last_day = sum(1 for t in user_data['uploads'] if t > day_ago)
        
        # Check upload count limits
        if uploads_last_minute >= self.rate_limits['uploads_per_minute']:
            return False, f"Upload rate limit exceeded: {self.rate_limits['uploads_per_minute']} uploads per minute"
        
        if uploads_last_hour >= self.rate_limits['uploads_per_hour']:
            return False, f"Upload rate limit exceeded: {self.rate_limits['uploads_per_hour']} uploads per hour"
        
        if uploads_last_day >= self.rate_limits['uploads_per_day']:
            return False, f"Upload rate limit exceeded: {self.rate_limits['uploads_per_day']} uploads per day"
        
        # Check size limits
        size_last_hour = sum(size for t, size in user_data['size_uploads'] if t > hour_ago)
        size_last_day = sum(size for t, size in user_data['size_uploads'] if t > day_ago)
        
        if size_last_hour + file_size > self.rate_limits['total_size_per_hour']:
            return False, f"Size limit exceeded: {self.rate_limits['total_size_per_hour'] // (1024*1024)}MB per hour"
        
        if size_last_day + file_size > self.rate_limits['total_size_per_day']:
            return False, f"Size limit exceeded: {self.rate_limits['total_size_per_day'] // (1024*1024)}MB per day"
        
        return True, ""
    
    def _record_upload(self, user_id: int, file_size: int):
        """Record an upload for rate limiting"""
        current_time = time.time()
        user_data = self.user_uploads[user_id]
        
        # Record upload time
        user_data['uploads'].append(current_time)
        
        # Record upload size
        user_data['size_uploads'].append((current_time, file_size))
    
    def validate_file(self, file: UploadFile) -> Tuple[bool, str]:
        """
        Validate uploaded file for security and size constraints
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check file size
            if hasattr(file, 'size') and file.size and file.size > self.max_file_size:
                return False, f"File size exceeds maximum allowed size of {self.max_file_size / (1024*1024):.1f}MB"
            
            # Check if file has a name
            if not file.filename:
                return False, "File must have a filename"
            
            # Get file extension
            file_ext = Path(file.filename).suffix.lower()
            
            # Check allowed extensions
            if file_ext not in self.allowed_extensions:
                return False, f"File type '{file_ext}' is not allowed. Allowed types: {', '.join(sorted(self.allowed_extensions))}"
            
            # Check for dangerous file names
            dangerous_patterns = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
            if any(pattern in file.filename for pattern in dangerous_patterns):
                return False, "Filename contains invalid characters"
            
            # Check MIME type
            mime_type, _ = mimetypes.guess_type(file.filename)
            if not mime_type:
                return False, "Unable to determine file type"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating file {file.filename}: {str(e)}")
            return False, f"Error validating file: {str(e)}"
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate a unique filename to prevent conflicts
        
        Args:
            original_filename: Original filename
            
        Returns:
            Unique filename with UUID prefix
        """
        file_ext = Path(original_filename).suffix
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{file_ext}"
    
    def save_file(self, file: UploadFile, task_id: int, user_id: int) -> Tuple[str, str, int]:
        """
        Save uploaded file to disk
        
        Args:
            file: FastAPI UploadFile object
            task_id: ID of the task this file belongs to
            user_id: ID of the user uploading the file
            
        Returns:
            Tuple of (file_path, filename, file_size)
        """
        try:
            # Validate file first
            is_valid, error_msg = self.validate_file(file)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
            
            # Check rate limits
            file_size = getattr(file, 'size', 0) or 0
            if file_size == 0:
                # If size is not available, we'll check after saving
                file_size = self.max_file_size  # Use max size for rate limit check
            
            rate_ok, rate_error = self._check_rate_limits(user_id, file_size)
            if not rate_ok:
                raise HTTPException(status_code=429, detail=rate_error)
            
            # Generate unique filename
            unique_filename = self.generate_unique_filename(file.filename)
            
            # Create task-specific directory
            task_dir = self.upload_dir / "tasks" / str(task_id)
            task_dir.mkdir(parents=True, exist_ok=True)
            
            # Full file path
            file_path = task_dir / unique_filename
            
            # Save file to disk
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Get file size
            file_size = file_path.stat().st_size
            
            # Double-check file size after saving
            if file_size > self.max_file_size:
                # Remove the file if it's too large
                file_path.unlink()
                raise HTTPException(
                    status_code=400, 
                    detail=f"File size exceeds maximum allowed size of {self.max_file_size / (1024*1024):.1f}MB"
                )
            
            # Record the upload for rate limiting
            self._record_upload(user_id, file_size)
            
            logger.info(f"File saved successfully: {file_path}")
            return str(file_path), unique_filename, file_size
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from disk
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if file was deleted successfully, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.info(f"File deleted successfully: {file_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False
    
    def get_file_path(self, task_id: int, filename: str) -> Optional[str]:
        """
        Get the full path to a file
        
        Args:
            task_id: ID of the task
            filename: Name of the file
            
        Returns:
            Full path to the file if it exists, None otherwise
        """
        file_path = self.upload_dir / "tasks" / str(task_id) / filename
        return str(file_path) if file_path.exists() else None
    
    def get_file_info(self, file_path: str) -> Optional[dict]:
        """
        Get file information
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file information or None if file doesn't exist
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return None
            
            stat = path.stat()
            mime_type, _ = mimetypes.guess_type(str(path))
            
            return {
                "size": stat.st_size,
                "mime_type": mime_type or "application/octet-stream",
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime
            }
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {str(e)}")
            return None
    
    def cleanup_orphaned_files(self, db: Session) -> int:
        """
        Clean up files that are no longer referenced in the database
        
        Args:
            db: Database session
            
        Returns:
            Number of files cleaned up
        """
        try:
            # Get all file paths from database
            db_files = db.query(TaskAttachment.file_path).all()
            db_file_paths = {row[0] for row in db_files}
            
            # Get all files in upload directory
            upload_files = set()
            for task_dir in (self.upload_dir / "tasks").iterdir():
                if task_dir.is_dir():
                    for file_path in task_dir.iterdir():
                        if file_path.is_file():
                            upload_files.add(str(file_path))
            
            # Find orphaned files
            orphaned_files = upload_files - db_file_paths
            
            # Delete orphaned files
            deleted_count = 0
            for file_path in orphaned_files:
                if self.delete_file(file_path):
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} orphaned files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            return 0
    
    def get_storage_stats(self) -> dict:
        """
        Get storage statistics
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            total_size = 0
            file_count = 0
            
            for task_dir in (self.upload_dir / "tasks").iterdir():
                if task_dir.is_dir():
                    for file_path in task_dir.iterdir():
                        if file_path.is_file():
                            total_size += file_path.stat().st_size
                            file_count += 1
            
            return {
                "total_files": file_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "upload_directory": str(self.upload_dir)
            }
        except Exception as e:
            logger.error(f"Error getting storage stats: {str(e)}")
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0,
                "upload_directory": str(self.upload_dir),
                "error": str(e)
            }

# Global instance
file_storage = FileStorageService()
