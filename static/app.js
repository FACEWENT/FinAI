async function send() {
    const input = document.getElementById("input");
    const text = input.value;
    if (!text) return;

    const messages = document.getElementById("messages");
    messages.innerHTML += `<div class="msg user">你：${text}</div>`;
    messages.scrollTop = messages.scrollHeight;
    input.value = "";

    const botDiv = document.createElement("div");
    botDiv.className = "msg bot";
    botDiv.textContent = "FinAI：";
    messages.appendChild(botDiv);
    messages.scrollTop = messages.scrollHeight;

    const url = `/analyze_sse?question=${encodeURIComponent(text)}`;
    const source = new EventSource(url);

    let buffer = "";
    let typing = false;

    function flushBuffer() {
        if (typing) return;
        typing = true;

        const chunkSize = 30;
        const chunkDelayMs = 120;

        const step = () => {
            if (buffer.length === 0) {
                typing = false;
                return;
            }
            const chunk = buffer.slice(0, chunkSize);
            buffer = buffer.slice(chunkSize);
            botDiv.textContent += chunk;
            messages.scrollTop = messages.scrollHeight;
            setTimeout(step, chunkDelayMs);
        };

        step();
    }

    source.addEventListener("status", (event) => {
        buffer += `${event.data}\n`;
        flushBuffer();
    });

    source.addEventListener("done", () => {
        source.close();
    });

    source.onmessage = (event) => {
        buffer += event.data;
        flushBuffer();
    };

    source.onerror = () => {
        buffer += "\n[连接中断，请稍后重试]";
        flushBuffer();
        source.close();
    };
}

function quickAsk(text) {
    const input = document.getElementById("input");
    input.value = text;
    send();
}
