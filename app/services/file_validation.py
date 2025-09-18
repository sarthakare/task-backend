# app/services/file_validation.py
try:
    import magic
except ImportError:
    # Fallback for systems without libmagic
    magic = None
import hashlib
import os
from typing import List, Tuple, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FileValidationService:
    """Advanced file validation service for security"""
    
    def __init__(self):
        # Dangerous file signatures (magic numbers)
        self.dangerous_signatures = {
            # Executable files
            b'\x4d\x5a': 'PE executable',  # Windows PE
            b'\x7f\x45\x4c\x46': 'ELF executable',  # Linux ELF
            b'\xfe\xed\xfa': 'Mach-O executable',  # macOS Mach-O
            b'\xce\xfa\xed\xfe': 'Mach-O executable',  # macOS Mach-O (64-bit)
            b'\xca\xfe\xba\xbe': 'Java class file',
            b'\xde\xad\xbe\xef': 'Mach-O fat binary',
            
            # Script files that could be dangerous
            b'#!/bin/bash': 'Bash script',
            b'#!/bin/sh': 'Shell script',
            b'#!/usr/bin/python': 'Python script',
            b'#!/usr/bin/env python': 'Python script',
            b'#!/usr/bin/perl': 'Perl script',
            b'#!/usr/bin/php': 'PHP script',
            b'<script': 'HTML with script',
            b'javascript:': 'JavaScript',
            b'vbscript:': 'VBScript',
            b'<iframe': 'HTML iframe',
            b'<object': 'HTML object',
            b'<embed': 'HTML embed',
            
            # Archive files that could contain executables
            b'PK\x03\x04': 'ZIP archive',
            b'PK\x05\x06': 'ZIP archive (empty)',
            b'PK\x07\x08': 'ZIP archive (spanned)',
            b'Rar!\x1a\x07': 'RAR archive',
            b'\x1f\x8b': 'GZIP archive',
            b'BZh': 'BZIP2 archive',
            b'\xfd7zXZ': 'XZ archive',
            
            # Database files
            b'SQLite format 3': 'SQLite database',
            b'\x00\x00\x00\x14\x66\x74\x79\x70': 'MP4 video',
            b'\x00\x00\x00\x20\x66\x74\x79\x70': 'MP4 video',
        }
        
        # Allowed MIME types
        self.allowed_mime_types = {
            # Documents
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'text/rtf',
            'application/vnd.oasis.opendocument.text',
            
            # Images
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/bmp',
            'image/svg+xml',
            'image/webp',
            
            # Spreadsheets
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/csv',
            'application/vnd.oasis.opendocument.spreadsheet',
            
            # Presentations
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.oasis.opendocument.presentation',
            
            # Archives
            'application/zip',
            'application/x-rar-compressed',
            'application/x-7z-compressed',
            'application/x-tar',
            'application/gzip',
            
            # Code files
            'text/x-python',
            'application/javascript',
            'text/html',
            'text/css',
            'application/json',
            'application/xml',
            'text/x-sql',
            
            # Media files
            'video/mp4',
            'video/avi',
            'video/quicktime',
            'video/x-ms-wmv',
            'audio/mpeg',
            'audio/wav',
            'audio/flac',
        }
        
        # Maximum file sizes by type (in bytes)
        self.max_sizes = {
            'image': 5 * 1024 * 1024,  # 5MB for images
            'document': 10 * 1024 * 1024,  # 10MB for documents
            'video': 50 * 1024 * 1024,  # 50MB for videos
            'audio': 20 * 1024 * 1024,  # 20MB for audio
            'archive': 25 * 1024 * 1024,  # 25MB for archives
            'default': 10 * 1024 * 1024,  # 10MB default
        }
    
    def validate_file_signature(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate file by checking its magic signature (relaxed for internal use)
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(file_path, 'rb') as f:
                # Read first 1024 bytes to check signature
                header = f.read(1024)
                
                # Only check for obvious executable files (PE, ELF, Mach-O)
                dangerous_executables = {
                    b'\x4d\x5a': 'PE executable',  # Windows PE
                    b'\x7f\x45\x4c\x46': 'ELF executable',  # Linux ELF
                    b'\xfe\xed\xfa': 'Mach-O executable',  # macOS Mach-O
                    b'\xce\xfa\xed\xfe': 'Mach-O executable',  # macOS Mach-O (64-bit)
                }
                
                for signature, description in dangerous_executables.items():
                    if header.startswith(signature):
                        return False, f"Executable file detected: {description}"
                
                # Allow script files for internal use
                # Allow all other file types
                return True, ""
                
        except Exception as e:
            logger.error(f"Error validating file signature for {file_path}: {str(e)}")
            return False, f"Error reading file: {str(e)}"
    
    def validate_mime_type(self, file_path: str, declared_mime_type: str) -> Tuple[bool, str]:
        """
        Validate MIME type using python-magic
        
        Args:
            file_path: Path to the file
            declared_mime_type: MIME type declared by the client
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if magic is None:
                # Fallback: only validate declared MIME type if magic is not available
                if declared_mime_type and declared_mime_type not in self.allowed_mime_types:
                    return False, f"File type '{declared_mime_type}' is not allowed"
                return True, ""
            
            # Get actual MIME type from file
            actual_mime_type = magic.from_file(file_path, mime=True)
            
            # Check if actual MIME type is allowed
            if actual_mime_type not in self.allowed_mime_types:
                return False, f"File type '{actual_mime_type}' is not allowed"
            
            # Check if declared and actual MIME types match
            if declared_mime_type and actual_mime_type != declared_mime_type:
                return False, f"MIME type mismatch: declared '{declared_mime_type}' but actual '{actual_mime_type}'"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating MIME type for {file_path}: {str(e)}")
            return False, f"Error validating file type: {str(e)}"
    
    def validate_file_size(self, file_path: str, mime_type: str) -> Tuple[bool, str]:
        """
        Validate file size based on file type
        
        Args:
            file_path: Path to the file
            mime_type: MIME type of the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            file_size = os.path.getsize(file_path)
            
            # Determine max size based on file type
            max_size = self.max_sizes['default']
            
            if mime_type.startswith('image/'):
                max_size = self.max_sizes['image']
            elif mime_type.startswith('video/'):
                max_size = self.max_sizes['video']
            elif mime_type.startswith('audio/'):
                max_size = self.max_sizes['audio']
            elif mime_type in ['application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed']:
                max_size = self.max_sizes['archive']
            elif any(doc_type in mime_type for doc_type in ['pdf', 'document', 'spreadsheet', 'presentation']):
                max_size = self.max_sizes['document']
            
            if file_size > max_size:
                return False, f"File size ({file_size / (1024*1024):.1f}MB) exceeds maximum allowed size ({max_size / (1024*1024):.1f}MB) for this file type"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating file size for {file_path}: {str(e)}")
            return False, f"Error checking file size: {str(e)}"
    
    def scan_for_malware_patterns(self, file_path: str) -> Tuple[bool, str]:
        """
        Comprehensive malware pattern scanning
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_safe, warning_message)
        """
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                
                # Check for suspicious patterns
                suspicious_patterns = [
                    # Code execution patterns
                    b'eval(',
                    b'exec(',
                    b'system(',
                    b'shell_exec(',
                    b'passthru(',
                    b'popen(',
                    b'proc_open(',
                    b'file_get_contents(',
                    b'file_put_contents(',
                    b'fopen(',
                    b'fwrite(',
                    b'include(',
                    b'require(',
                    b'require_once(',
                    b'include_once(',
                    
                    # Command execution
                    b'cmd.exe',
                    b'powershell',
                    b'bash',
                    b'sh',
                    b'/bin/sh',
                    b'/bin/bash',
                    b'wget',
                    b'curl',
                    b'nc ',
                    b'netcat',
                    b'telnet',
                    b'ssh',
                    b'scp',
                    b'ftp',
                    
                    # Web-based attacks
                    b'<iframe',
                    b'<script>',
                    b'<object>',
                    b'<embed>',
                    b'<applet>',
                    b'javascript:',
                    b'vbscript:',
                    b'onload=',
                    b'onerror=',
                    b'onclick=',
                    b'onmouseover=',
                    b'document.cookie',
                    b'document.write',
                    b'window.location',
                    b'XMLHttpRequest',
                    b'fetch(',
                    b'$.ajax',
                    b'$.post',
                    b'$.get',
                    
                    # SQL injection patterns
                    b'union select',
                    b'drop table',
                    b'delete from',
                    b'insert into',
                    b'update set',
                    b'alter table',
                    b'create table',
                    b'exec(',
                    b'execute(',
                    b'sp_executesql',
                    
                    # File system access
                    b'../',
                    b'..\\',
                    b'/etc/passwd',
                    b'/etc/shadow',
                    b'C:\\Windows\\System32',
                    b'/proc/',
                    b'/sys/',
                    b'/dev/',
                    
                    # Network patterns
                    b'http://',
                    b'https://',
                    b'ftp://',
                    b'file://',
                    b'data:',
                    b'javascript:',
                    b'vbscript:',
                    
                    # Encryption/obfuscation
                    b'base64_decode',
                    b'base64_encode',
                    b'str_rot13',
                    b'gzinflate',
                    b'gzuncompress',
                    b'gzdecode',
                    b'gzencode',
                    b'gzcompress',
                    b'gzdeflate',
                    b'gzfile',
                    b'readgzfile',
                    b'gzopen',
                    b'gzread',
                    b'gzwrite',
                    b'gzclose',
                    b'gzeof',
                    b'gzgetc',
                    b'gzgets',
                    b'gzgetss',
                    b'gzpassthru',
                    b'gzrewind',
                    b'gzseek',
                    b'gztell',
                    b'gzwrite',
                    
                    # Suspicious file extensions in content
                    b'.exe',
                    b'.bat',
                    b'.cmd',
                    b'.com',
                    b'.scr',
                    b'.pif',
                    b'.vbs',
                    b'.js',
                    b'.jar',
                    b'.class',
                    b'.php',
                    b'.asp',
                    b'.aspx',
                    b'.jsp',
                    b'.py',
                    b'.pl',
                    b'.sh',
                    b'.ps1',
                ]
                
                # Convert content to lowercase for case-insensitive matching
                content_lower = content.lower()
                
                for pattern in suspicious_patterns:
                    if pattern in content_lower:
                        return False, f"Suspicious content detected: {pattern.decode('utf-8', errors='ignore')}"
                
                # Check for high entropy (potential obfuscation)
                if self._calculate_entropy(content) > 7.5:
                    return False, "High entropy content detected (potential obfuscation)"
                
                # Check for suspicious file size patterns
                if len(content) < 10:  # Very small files might be suspicious
                    return False, "File too small (potential payload)"
                
                return True, ""
                
        except Exception as e:
            logger.error(f"Error scanning file for malware patterns: {str(e)}")
            return True, ""  # Don't block on scan errors
    
    def _calculate_entropy(self, data: bytes) -> float:
        """
        Calculate Shannon entropy of data
        
        Args:
            data: Binary data to analyze
            
        Returns:
            Entropy value (0-8, where 8 is maximum entropy)
        """
        if not data:
            return 0
        
        # Count byte frequencies
        byte_counts = [0] * 256
        for byte in data:
            byte_counts[byte] += 1
        
        # Calculate entropy
        entropy = 0
        data_len = len(data)
        for count in byte_counts:
            if count > 0:
                probability = count / data_len
                entropy -= probability * (probability.bit_length() - 1)
        
        return entropy
    
    def calculate_file_hash(self, file_path: str) -> str:
        """
        Calculate SHA-256 hash of the file
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA-256 hash of the file
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {str(e)}")
            return ""
    
    def comprehensive_validation(self, file_path: str, declared_mime_type: str) -> Tuple[bool, List[str]]:
        """
        Perform basic file validation for internal use (relaxed security)
        
        Args:
            file_path: Path to the file
            declared_mime_type: MIME type declared by the client
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Only validate file size for internal use
        is_valid, error = self.validate_file_size(file_path, declared_mime_type)
        if not is_valid:
            errors.append(f"Size validation failed: {error}")
        
        # Skip aggressive security scanning for internal use
        # Only check for obvious executable files
        is_valid, error = self.validate_file_signature(file_path)
        if not is_valid and "executable" in error.lower():
            errors.append(f"Signature validation failed: {error}")
        
        return len(errors) == 0, errors

# Global instance
file_validator = FileValidationService()
