from .nodes.hf.hf_download import HFDownloader
from .nodes.auto.downloader import AutoModelDownloader
from .nodes.cai.cai_download import CivitAIDownloader
from .nodes.download_utils import DownloadManager
from server import PromptServer
from aiohttp import web
import os

print("=" * 60)
print("MODEL DOWNLOADER CUSTOM NODE LOADING")
print("=" * 60)

# Get the absolute path for debugging
current_file = os.path.abspath(__file__)
current_dir = os.path.dirname(current_file)
js_dir_abs = os.path.join(current_dir, "js")

print(f"Current file: {current_file}")
print(f"Current dir: {current_dir}")
print(f"JS dir (absolute): {js_dir_abs}")
print(f"JS dir exists: {os.path.exists(js_dir_abs)}")

if os.path.exists(js_dir_abs):
    print(f"JS files found: {os.listdir(js_dir_abs)}")

# Node mappings
NODE_CLASS_MAPPINGS = { 
    "HF Downloader": HFDownloader,
    "Auto Model Downloader": AutoModelDownloader,
    "CivitAI Downloader": CivitAIDownloader,
}

# Display names
NODE_DISPLAY_NAME_MAPPINGS = { 
    "HF Downloader": "HF Download",
    "Auto Model Downloader": "Auto Model Finder (Experimental)",
    "CivitAI Downloader": "CivitAI Download",
}

# Web directory for JavaScript files
WEB_DIRECTORY = "./js"

print(f"WEB_DIRECTORY set to: {WEB_DIRECTORY}")
print(f"NODE_CLASS_MAPPINGS: {list(NODE_CLASS_MAPPINGS.keys())}")
print("=" * 60)

@PromptServer.instance.routes.post("/model_downloader/cancel")
async def cancel_download_route(request):
    try:
        json_data = await request.json()
        node_id = json_data.get("node_id")
        
        if not node_id:
            return web.json_response({"status": "bad_request", "error": "node_id required"}, status=400)
        
        node_id_str = str(node_id)
        
        print(f"===== CANCEL REQUEST =====")
        print(f"Received node_id: {node_id_str} (original: {node_id}, type: {type(node_id)})")
        print(f"Active downloads: {list(DownloadManager.active_downloads.keys())}")
        
        if DownloadManager.cancel_download(node_id_str):
            print(f"Successfully cancelled download for node {node_id_str}")
            return web.json_response({"status": "cancelled"})
        else:
            print(f"No active download found for node {node_id_str}")
            return web.json_response({"status": "not_found", "error": "No active download found"}, status=404)
            
    except Exception as e:
        print(f"Error in cancel endpoint: {str(e)}")
        import traceback
        traceback.print_exc()
        return web.json_response({"status": "error", "error": str(e)}, status=500)

__all__ = [
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
    "WEB_DIRECTORY"
]