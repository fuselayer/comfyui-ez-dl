from server import PromptServer
import os

def get_base_dir():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    models_dir = os.path.join(base_dir, 'models')
    return models_dir

def get_model_dirs(recursive=True, max_depth=3):
    """
    Get model directories.
    If recursive=True, returns all subdirectories up to max_depth levels deep.
    Returns paths relative to the models directory (e.g., 'loras', 'loras/SDXL', 'loras/flux').
    """
    models_dir = get_base_dir()
    
    if not os.path.exists(models_dir):
        return ["models"]
    
    model_dirs = []
    
    def scan_directory(current_path, relative_path="", depth=0):
        if depth > max_depth:
            return
        
        try:
            items = os.listdir(current_path)
            for item in sorted(items):
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path) and not item.startswith('.'):
                    # Build relative path
                    if relative_path:
                        rel_path = os.path.join(relative_path, item)
                    else:
                        rel_path = item
                    
                    model_dirs.append(rel_path)
                    # Recursively scan subdirectories
                    scan_directory(item_path, rel_path, depth + 1)
        except (PermissionError, OSError):
            pass  # Skip directories we can't access
    
    scan_directory(models_dir)
    
    # Return sorted list, or default if empty
    return sorted(model_dirs) if model_dirs else ["models"]

class BaseModelDownloader:
    RETURN_TYPES = ()
    OUTPUT_NODE = True
    CATEGORY = "loaders"

    def __init__(self):
        self.status = "Idle"
        self.progress = 0.0
        self.node_id = None

    def set_progress(self, percentage):
        self.update_status(f"Downloading... {percentage:.1f}%", percentage)

    def update_status(self, status_text, progress=None):
        if progress is not None and hasattr(self, 'node_id'):
            PromptServer.instance.send_sync("progress", {
                "node": self.node_id,
                "value": progress,
                "max": 100
            })

    def prepare_download_path(self, local_path, filename):
        # Just create the base directory, don't include the filename
        full_path = os.path.join(get_base_dir(), local_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
        return full_path
    
    def handle_download(self, download_func, save_path, filename, overwrite=False, **kwargs):
        try:
            file_path = os.path.join(save_path, filename)
            if os.path.exists(file_path) and not overwrite:
                print(f"File already exists and overwrite is False: {file_path}")
                return {}
            
            kwargs['save_path'] = save_path
            kwargs['filename'] = filename  # CRITICAL: Pass filename to download function
            kwargs['node_id'] = self.node_id
            result = download_func(**kwargs)
            if result is None:
                return {}
            self.update_status("Complete!", 100)
            return {}
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            raise e