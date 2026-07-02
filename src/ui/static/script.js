document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("command-input");
    const sendBtn = document.getElementById("send-btn");
    const outputArea = document.getElementById("output-area");
    const loadingOverlay = document.getElementById("loading");

    const modelSelect = document.getElementById("model");
    const depthInput = document.getElementById("depth");
    const collectionInput = document.getElementById("collection");

    const dispatchAgents = async () => {
        const objective = input.value.trim();
        if (!objective) return;

        input.value = "";
        loadingOverlay.classList.remove("hidden");
        
        if (outputArea.querySelector('.placeholder-text')) {
            outputArea.innerHTML = "";
        }
        
        const cmdEl = document.createElement("div");
        cmdEl.innerHTML = `<br><span style="color: #34d399; font-family: monospace;">SYS></span> ${objective}<br><br>`;
        outputArea.appendChild(cmdEl);
        outputArea.scrollTop = outputArea.scrollHeight;

        try {
            const response = await fetch("/api/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    objective: objective,
                    depth: parseInt(depthInput.value),
                    model: modelSelect.value
                })
            });

            const data = await response.json();
            
            if (data.status === "success") {
                const metaEl = document.createElement("div");
                metaEl.innerHTML = `<em style="color: #94a3b8; font-size: 0.9em;">Tasks Executed: ${data.tasks_executed} | Format: ${data.format}</em><br><br>`;
                outputArea.appendChild(metaEl);

                const resultEl = document.createElement("div");
                resultEl.classList.add("markdown-body");
                
                // If it's JSON-L, wrap it in a code block so marked.js renders it nicely
                let displayContent = data.content;
                if (data.format.includes("JSON")) {
                    displayContent = `\`\`\`json\n${displayContent}\n\`\`\``;
                }
                
                resultEl.innerHTML = marked.parse(displayContent);
                outputArea.appendChild(resultEl);
            } else {
                const errEl = document.createElement("div");
                errEl.style.color = "#ef4444";
                errEl.innerText = `Agent Error: ${data.message}`;
                outputArea.appendChild(errEl);
            }
        } catch (error) {
            const errEl = document.createElement("div");
            errEl.style.color = "#ef4444";
            errEl.innerText = `Network/Server Error: ${error.message}`;
            outputArea.appendChild(errEl);
        } finally {
            loadingOverlay.classList.add("hidden");
            outputArea.scrollTop = outputArea.scrollHeight;
        }
    };

    sendBtn.addEventListener("click", dispatchAgents);
    input.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            dispatchAgents();
        }
    });

    // History Logic
    const historyList = document.getElementById("history-list");
    const loadHistory = async () => {
        try {
            const res = await fetch("/api/history");
            const data = await res.json();
            historyList.innerHTML = "";
            
            if(data.processed && data.processed.length > 0) {
                historyList.innerHTML += "<li style='color:#34d399;font-weight:bold;'>Processed:</li>";
                data.processed.forEach(f => {
                    historyList.innerHTML += `<li style="cursor:pointer; margin-bottom:4px;" onclick="readHistory('${f}')">📄 ${f}</li>`;
                });
            }
            if(data.raw && data.raw.length > 0) {
                historyList.innerHTML += "<li style='color:#fbbf24;font-weight:bold;margin-top:10px;'>Raw Dumps:</li>";
                data.raw.forEach(f => {
                    historyList.innerHTML += `<li style="cursor:pointer; margin-bottom:4px;" onclick="readHistory('${f}')">🕷️ ${f}</li>`;
                });
            }
        } catch(e) {
            console.error("Failed to load history", e);
        }
    };

    window.readHistory = async (filename) => {
        try {
            const res = await fetch(`/api/history/read/${filename}`);
            const data = await res.json();
            outputArea.innerHTML = "";
            const resultEl = document.createElement("div");
            resultEl.classList.add("markdown-body");
            resultEl.innerHTML = marked.parse(`### Reading: ${filename}\n\n\`\`\`\n${data.content}\n\`\`\``);
            outputArea.appendChild(resultEl);
        } catch(e) {
            console.error("Failed to read file", e);
        }
    };

    document.getElementById("refresh-history-btn").addEventListener("click", loadHistory);
    document.getElementById("delete-raw-btn").addEventListener("click", async () => {
        await fetch("/api/history/delete/raw", { method: "DELETE" });
        loadHistory();
    });
    document.getElementById("delete-processed-btn").addEventListener("click", async () => {
        await fetch("/api/history/delete/processed", { method: "DELETE" });
        loadHistory();
    });

    // Memory Query Logic
    document.getElementById("memory-search-btn").addEventListener("click", async () => {
        const query = document.getElementById("memory-query").value.trim();
        const collection = document.getElementById("collection").value.trim();
        if(!query) return;
        
        outputArea.innerHTML = `<div style="color: #60a5fa;">Querying Memory DB for: "${query}"...</div>`;
        try {
            const res = await fetch("/api/memory/query", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: query, collection_name: collection })
            });
            const data = await res.json();
            
            if (data.status === "success") {
                outputArea.innerHTML = `<h3 style="color: #34d399;">Memory Results</h3>`;
                data.results.forEach((result, idx) => {
                    const resultEl = document.createElement("div");
                    resultEl.classList.add("markdown-body");
                    resultEl.style.border = "1px solid rgba(255,255,255,0.1)";
                    resultEl.style.padding = "10px";
                    resultEl.style.marginBottom = "10px";
                    resultEl.style.borderRadius = "8px";
                    resultEl.innerHTML = marked.parse(`**Match ${idx + 1}**\n\n${result}`);
                    outputArea.appendChild(resultEl);
                });
            } else {
                outputArea.innerHTML = `<div style="color: #ef4444;">Error: ${data.message}</div>`;
            }
        } catch(e) {
            outputArea.innerHTML = `<div style="color: #ef4444;">Error querying memory: ${e.message}</div>`;
        }
    });

    // Initial load
    loadHistory();
});
