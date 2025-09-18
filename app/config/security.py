# app/config/security.py
# Security configuration for file uploads and system security

import os
from typing import Dict, List, Set

class SecurityConfig:
    """Security configuration for the application"""
    
    # File upload security settings
    FILE_UPLOAD = {
        'max_file_size': int(os.getenv('MAX_FILE_SIZE', 10 * 1024 * 1024)),  # 10MB
        'max_files_per_upload': int(os.getenv('MAX_FILES_PER_UPLOAD', 10)),
        'allowed_extensions': {
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
            # Media
            '.mp4', '.avi', '.mov', '.wmv', '.mp3', '.wav', '.flac'
        },
        'blocked_extensions': {
            '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js',
            '.jar', '.class', '.php', '.asp', '.aspx', '.jsp', '.py', '.pl',
            '.sh', '.ps1', '.dll', '.sys', '.drv', '.ocx', '.cpl', '.msi'
        },
        'scan_content': os.getenv('SCAN_FILE_CONTENT', 'true').lower() == 'true',
        'quarantine_suspicious': os.getenv('QUARANTINE_SUSPICIOUS', 'true').lower() == 'true'
    }
    
    # Rate limiting settings
    RATE_LIMITS = {
        'uploads_per_minute': int(os.getenv('UPLOADS_PER_MINUTE', 10)),
        'uploads_per_hour': int(os.getenv('UPLOADS_PER_HOUR', 50)),
        'uploads_per_day': int(os.getenv('UPLOADS_PER_DAY', 200)),
        'total_size_per_hour': int(os.getenv('TOTAL_SIZE_PER_HOUR', 100 * 1024 * 1024)),  # 100MB
        'total_size_per_day': int(os.getenv('TOTAL_SIZE_PER_DAY', 500 * 1024 * 1024)),   # 500MB
    }
    
    # Security headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    }
    
    # File storage security
    STORAGE = {
        'upload_dir': os.getenv('UPLOAD_DIR', 'uploads'),
        'quarantine_dir': os.getenv('QUARANTINE_DIR', 'quarantine'),
        'temp_dir': os.getenv('TEMP_DIR', 'temp'),
        'scan_uploads': os.getenv('SCAN_UPLOADS', 'true').lower() == 'true',
        'virus_scan': os.getenv('VIRUS_SCAN', 'false').lower() == 'true',
        'virus_scan_command': os.getenv('VIRUS_SCAN_COMMAND', 'clamscan'),
    }
    
    # Logging and monitoring
    MONITORING = {
        'log_suspicious_uploads': os.getenv('LOG_SUSPICIOUS_UPLOADS', 'true').lower() == 'true',
        'alert_on_malware': os.getenv('ALERT_ON_MALWARE', 'true').lower() == 'true',
        'max_log_size': int(os.getenv('MAX_LOG_SIZE', 10 * 1024 * 1024)),  # 10MB
        'log_retention_days': int(os.getenv('LOG_RETENTION_DAYS', 30)),
    }
    
    @classmethod
    def get_allowed_mime_types(cls) -> Set[str]:
        """Get allowed MIME types based on allowed extensions"""
        mime_map = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.rtf': 'text/rtf',
            '.odt': 'application/vnd.oasis.opendocument.text',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.svg': 'image/svg+xml',
            '.webp': 'image/webp',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.csv': 'text/csv',
            '.ods': 'application/vnd.oasis.opendocument.spreadsheet',
            '.ppt': 'application/vnd.ms-powerpoint',
            '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            '.odp': 'application/vnd.oasis.opendocument.presentation',
            '.zip': 'application/zip',
            '.rar': 'application/x-rar-compressed',
            '.7z': 'application/x-7z-compressed',
            '.tar': 'application/x-tar',
            '.gz': 'application/gzip',
            '.py': 'text/x-python',
            '.js': 'application/javascript',
            '.html': 'text/html',
            '.css': 'text/css',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.sql': 'text/x-sql',
            '.mp4': 'video/mp4',
            '.avi': 'video/avi',
            '.mov': 'video/quicktime',
            '.wmv': 'video/x-ms-wmv',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.flac': 'audio/flac',
        }
        
        return {mime_map[ext] for ext in cls.FILE_UPLOAD['allowed_extensions'] if ext in mime_map}
    
    @classmethod
    def is_extension_allowed(cls, extension: str) -> bool:
        """Check if file extension is allowed"""
        return extension.lower() in cls.FILE_UPLOAD['allowed_extensions']
    
    @classmethod
    def is_extension_blocked(cls, extension: str) -> bool:
        """Check if file extension is blocked"""
        return extension.lower() in cls.FILE_UPLOAD['blocked_extensions']
    
    @classmethod
    def get_quarantine_path(cls, filename: str) -> str:
        """Get quarantine path for suspicious files"""
        import os
        quarantine_dir = os.path.join(cls.STORAGE['upload_dir'], cls.STORAGE['quarantine_dir'])
        os.makedirs(quarantine_dir, exist_ok=True)
        return os.path.join(quarantine_dir, filename)
