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

async function generateReportPdf() {
    const input = document.getElementById("input");
    const text = input.value;
    if (!text) {
        alert("请先输入研究报告主题");
        return;
    }

    const messages = document.getElementById("messages");
    messages.innerHTML += `<div class="msg user">你：${text}</div>`;
    messages.innerHTML += `<div class="msg bot">FinAI：正在生成研究报告PDF...</div>`;
    messages.scrollTop = messages.scrollHeight;

    const textResp = await fetch("/report_bundle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text })
    });

    if (!textResp.ok) {
        messages.innerHTML += `<div class="msg bot">FinAI：生成失败，请稍后重试。</div>`;
        return;
    }

    const data = await textResp.json();
    messages.innerHTML += `<div class="msg bot">FinAI：${data.result}</div>`;
    messages.scrollTop = messages.scrollHeight;

    if (!data.pdf_base64) {
        messages.innerHTML += `<div class="msg bot">FinAI：PDF 生成失败，请稍后重试。</div>`;
        return;
    }

    const byteChars = atob(data.pdf_base64);
    const byteNumbers = new Array(byteChars.length);
    for (let i = 0; i < byteChars.length; i++) {
        byteNumbers[i] = byteChars.charCodeAt(i);
    }
    const blob = new Blob([new Uint8Array(byteNumbers)], { type: "application/pdf" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "research_report.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
}
