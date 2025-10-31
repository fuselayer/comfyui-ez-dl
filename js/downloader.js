import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

console.log("===========================================");
console.log("MODEL DOWNLOADER JS FILE IS LOADING!");
console.log("===========================================");

const extension = {
    name: "ComfyUI-Model-Downloader",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        console.log(">>> beforeRegisterNodeDef called!");
        console.log(">>> nodeData.name:", nodeData.name);
        console.log(">>> nodeData:", nodeData);
        
        if (nodeData.name === 'HF Downloader' || nodeData.name === 'Auto Model Downloader' || nodeData.name === 'CivitAI Downloader') {
            console.log(">>> MATCHED NODE TYPE:", nodeData.name);
            
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                console.log(">>> onNodeCreated - Node ID:", this.id, "Type:", this.type);
                
                if (onNodeCreated) {
                    onNodeCreated.apply(this, arguments);
                }

                // URL validation
                if (this.type === 'HF Downloader' || this.type === 'CivitAI Downloader') {
                    console.log(">>> Adding URL validation");
                    const widget = this.widgets.find(w => w.name === 'model_url');
                    if (widget && widget.inputEl) {
                        const validateUrl = () => {
                            const url = widget.value;
                            const civitaiPattern = /^https?:\/\/(www\.)?civitai\.com\/models\/(\d+)/;
                            const huggingfacePattern = /^https?:\/\/huggingface\.co\/([^\/]+\/[^\/]+)/;
                            if (civitaiPattern.test(url) || huggingfacePattern.test(url)) {
                                widget.inputEl.style.backgroundColor = '#224422';
                            } else {
                                widget.inputEl.style.backgroundColor = '#442222';
                            }
                        };
                        widget.inputEl.addEventListener('input', validateUrl);
                        validateUrl();
                    }
                }

                // CRITICAL FIX: Capture node reference in closure
                const node = this;
                
                // CANCEL BUTTON
                console.log(">>> Adding CANCEL BUTTON to node", node.id);
                console.log(">>> Widgets before adding cancel:", this.widgets?.map(w => w.name));
                
                const cancelButton = this.addWidget("button", "cancel_download", "Cancel Download", () => {
                    console.log(">>> CANCEL CLICKED! Node ID:", node.id);
                    
                    // Visual feedback
                    cancelButton.name = "Cancelling...";
                    node.setDirtyCanvas(true, true);
                    
                    api.fetchApi("/model_downloader/cancel", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ node_id: String(node.id) })
                    })
                    .then(r => r.json())
                    .then(data => {
                        console.log(">>> Cancel response:", data);
                        if (data.status === "cancelled") {
                            cancelButton.name = "Download Cancelled";
                        } else if (data.status === "not_found") {
                            cancelButton.name = "No Active Download";
                        }
                        node.setDirtyCanvas(true, true);
                        
                        // Reset button text after 2 seconds
                        setTimeout(() => {
                            cancelButton.name = "Cancel Download";
                            node.setDirtyCanvas(true, true);
                        }, 2000);
                    })
                    .catch(err => {
                        console.error(">>> Cancel error:", err);
                        cancelButton.name = "Cancel Failed";
                        node.setDirtyCanvas(true, true);
                        
                        setTimeout(() => {
                            cancelButton.name = "Cancel Download";
                            node.setDirtyCanvas(true, true);
                        }, 2000);
                    });
                });
                
                cancelButton.serialize = false;
                console.log(">>> Cancel button added:", cancelButton);
                console.log(">>> Widgets after adding cancel:", this.widgets?.map(w => w.name));
            };

            // Add setProgress method to show download progress
            nodeType.prototype.setProgress = function (progress) {
                console.log(">>> setProgress called:", progress);
                this.progress = progress; // Expects 0.0-1.0 for ComfyUI core rendering
                this.setDirtyCanvas(true, true);
            };
        }
    },
    
    async setup() {
        console.log(">>> Extension setup() called");
        
        api.addEventListener("progress", ({ detail }) => {
            console.log(">>> Progress event:", detail);
            if (!detail.node) return;
            
            const node = app.graph.getNodeById(detail.node);
            if (!node || !["HF Downloader", "Auto Model Downloader", "CivitAI Downloader"].includes(node.type)) return;
            
            if (detail.value === undefined || detail.max === undefined || detail.max === 0) return;
            
            const progress = detail.value / detail.max; // 0.0 to 1.0, not 0 to 100
            console.log(">>> Calling setProgress with:", progress);
            if (node.setProgress) {
                node.setProgress(progress);
            }
        });
    }
};

console.log(">>> About to register extension:", extension.name);
app.registerExtension(extension);
console.log(">>> Extension registered successfully!");