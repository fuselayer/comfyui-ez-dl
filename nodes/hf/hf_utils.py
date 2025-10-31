import os
from tqdm import tqdm
import requests
import re

def parse_hf_url(url):
    """
    Parses a Hugging Face URL to extract the repo_id and filename.
    Handles multiple formats:
    - https://huggingface.co/user/repo/blob/main/file.safetensors
    - https://huggingface.co/user/repo/resolve/main/file.safetensors
    - user/repo/blob/main/file.safetensors (shorthand)
    - user/repo/resolve/main/file.safetensors (shorthand)
    - user/repo (just repo, returns None for filename)
    """
    # Remove whitespace
    url = url.strip()
    
    # Try full URL format with domain
    match = re.search(r'huggingface\.co/([^/]+/[^/]+)/(?:blob|resolve)/main/(.+)', url)
    if match:
        repo_id = match.group(1)
        filename = match.group(2).split('?')[0]
        return repo_id, filename
    
    # Try shorthand format: user/repo/blob/main/file.safetensors
    match = re.search(r'^([^/]+/[^/]+)/(?:blob|resolve)/main/(.+)', url)
    if match:
        repo_id = match.group(1)
        filename = match.group(2).split('?')[0]
        return repo_id, filename
    
    # Try just repo format: user/repo
    match = re.search(r'^([^/]+/[^/]+)$', url)
    if match:
        repo_id = match.group(1)
        # Return None for filename - caller should handle this
        print(f"Warning: Only repo ID provided ({repo_id}), no specific file. Please specify a file.")
        return repo_id, None
    
    # If nothing matches, return None, None
    return None, None

def download_hf(repo_id, filename, save_path, overwrite=False, progress_callback=None):
    URL = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"
    
    # Get file size first
    response = requests.get(URL, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    # Create the full file path
    full_file_path = os.path.join(save_path, filename)
    
    chunk_size = 1024 * 1024  # 1MB chunks
    downloaded = 0

    with open(full_file_path, 'wb') as file:
        with tqdm(total=total_size, unit='iB', unit_scale=True, desc=filename, leave=True) as pbar:
            for data in response.iter_content(chunk_size=chunk_size):
                size = file.write(data)
                downloaded += size
                pbar.update(size)
                
                if progress_callback and total_size > 0:
                    progress = (downloaded / total_size) * 100.0
                    progress_callback.set_progress(progress)

    return True