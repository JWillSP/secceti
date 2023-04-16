import os
import re


def make_windows_filename_safe(filename):
  # Windows does not allow the following characters in filenames
  illegal_chars = r'[<>:"/\|?*]'
  # Replace illegal characters with underscores
  safe_filename = re.sub(illegal_chars, '_', filename)
  # Trim any trailing dots and spaces
  safe_filename = safe_filename.rstrip('. ')
  # Trim any leading or trailing whitespace
  safe_filename = safe_filename.strip()
  # Truncate the filename to 255 characters (Windows limit)
  safe_filename = safe_filename[:255]
  return safe_filename
