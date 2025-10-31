from ..base_downloader import BaseModelDownloader, get_model_dirs
from ..download_utils import DownloadManager, get_civitai_model_id_and_version
import requests

class CivitAIDownloader(BaseModelDownloader):
    base_url = 'https://civitai.com/api'
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {       
                "model_url": ("STRING", {"multiline": False, "default": "https://civitai.com/models/360292/epicrealism-new-era"}),
                "token_id": ("STRING", {"multiline": False, "default": "API_token_here"}),
                "save_dir": (get_model_dirs(),),
            },
            "optional": {
                "overwrite": ("BOOLEAN", {"default": True}),
                "save_dir_override": ("STRING", {"default": ""}),
            },
            "hidden": {
                "node_id": "UNIQUE_ID"
            }
        }
        
    FUNCTION = "download"
    
    def get_download_filename_url(self, model_id, version_id, token_id):
        """ 
        Find the model filename and URL from the CivitAI API.
        
        Logic:
        1. If version_id is provided, use that specific version
        2. If only model_id is provided, try as model ID first, then as version ID
        3. Returns filename and download URL
        """
        headers = {"Authorization": f"Bearer {token_id}"}
        
        # If we have a specific version_id from the URL
        if version_id:
            return self._get_version_details(version_id, headers)
        
        # Try as model ID first
        model_details_url = f'{self.base_url}/v1/models/{model_id}'
        response = requests.get(model_details_url, headers=headers)
        
        if response.status_code == 200:
            # Successfully got model details, find latest/specific version
            model_details = response.json()
            model_versions = model_details.get('modelVersions', [])
            
            if not model_versions:
                raise Exception(f"No versions found for model ID {model_id}")
            
            # Sort versions by creation date (newest first)
            model_versions.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
            latest_version = model_versions[0]
            
            return self._extract_file_info(latest_version)
        
        elif response.status_code == 404:
            # Not a model ID, try as version ID
            print(f"Model ID {model_id} not found, trying as version ID...")
            return self._get_version_details(model_id, headers)
        
        else:
            raise Exception(f"Failed to fetch model details. Status code: {response.status_code}")
    
    def _get_version_details(self, version_id, headers):
        """Get details for a specific model version."""
        version_url = f'{self.base_url}/v1/model-versions/{version_id}'
        response = requests.get(version_url, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch version {version_id}. Status code: {response.status_code}")
        
        version_details = response.json()
        return self._extract_file_info(version_details)
    
    def _extract_file_info(self, version_details):
        """Extract filename and download URL from version details."""
        files = version_details.get('files', [])
        
        if not files:
            version_id = version_details.get('id', 'unknown')
            raise Exception(f"No files found for version {version_id}")
        
        # Get the primary file (usually the first one, or look for primary=true)
        primary_file = None
        for file in files:
            if file.get('primary', False):
                primary_file = file
                break
        
        if not primary_file:
            primary_file = files[0]
        
        filename = primary_file['name']
        download_url = primary_file['downloadUrl']
        
        return filename, download_url
    
    def download(self, model_url, token_id, save_dir, node_id, overwrite=True, save_dir_override=""):
        self.node_id = node_id
        model_id, version_id = get_civitai_model_id_and_version(model_url)
        
        if not model_id:
            raise Exception("Invalid CivitAI URL. Could not find model ID or version ID.")
            
        filename, url = self.get_download_filename_url(model_id, version_id, token_id)
        
        # Use override if provided, otherwise use dropdown selection
        final_path = save_dir_override if save_dir_override else save_dir
        save_path = self.prepare_download_path(final_path, filename)
        
        return self.handle_download(
            DownloadManager.download_with_progress,
            url=url,
            save_path=save_path,
            filename=filename,
            overwrite=overwrite,
            progress_callback=self,
            params={'token': token_id}
        )