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
});
