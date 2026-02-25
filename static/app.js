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

    const textResp = await fetch("/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text, pdf_urls: collectPdfUrls() })
    });

    if (!textResp.ok) {
        messages.innerHTML += `<div class="msg bot">FinAI：生成失败，请稍后重试。</div>`;
        return;
    }

    const data = await textResp.json();
    if (data.report) {
        messages.innerHTML += `<div class="msg bot">FinAI：${data.report}</div>`;
    }
    messages.scrollTop = messages.scrollHeight;

    const pdfResp = await fetch("/research_pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text, pdf_urls: collectPdfUrls() })
    });

    if (!pdfResp.ok) {
        messages.innerHTML += `<div class="msg bot">FinAI：PDF 生成失败，请稍后重试。</div>`;
        return;
    }

    const blob = await pdfResp.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "research_report.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
}

let lineChartInstance = null;
let barChartInstance = null;

function renderCharts(chart) {
    if (!chart || !chart.line || !chart.line.labels || chart.line.labels.length === 0) {
        return;
    }

    const lineCtx = document.getElementById("lineChart").getContext("2d");
    const barCtx = document.getElementById("barChart").getContext("2d");

    if (lineChartInstance) lineChartInstance.destroy();
    if (barChartInstance) barChartInstance.destroy();

    lineChartInstance = new Chart(lineCtx, {
        type: "line",
        data: {
            labels: chart.line.labels,
            datasets: [{
                label: `${chart.symbol} 价格`,
                data: chart.line.values,
                borderColor: "#6df3c7",
                backgroundColor: "rgba(109, 243, 199, 0.2)",
                tension: 0.2
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } }
        }
    });

    const bars = chart.bars || {};
    barChartInstance = new Chart(barCtx, {
        type: "bar",
        data: {
            labels: ["市值", "24H成交量"],
            datasets: [{
                label: `${chart.symbol} 指标`,
                data: [bars.marketCapUsd || 0, bars.volumeUsd24Hr || 0],
                backgroundColor: ["rgba(122, 162, 255, 0.6)", "rgba(255, 184, 107, 0.6)"]
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: true } }
        }
    });
}

function collectPdfUrls() {
    const area = document.getElementById("pdf-urls");
    const raw = area ? area.value : "";
    return raw.split(/\s+/).filter(Boolean);
}

async function runResearch() {
    const input = document.getElementById("input");
    const text = input.value;
    if (!text) {
        alert("请先输入研究主题");
        return;
    }

    const messages = document.getElementById("messages");
    messages.innerHTML += `<div class="msg user">你：${text}</div>`;
    messages.innerHTML += `<div class="msg bot">FinAI：研究助理正在工作...</div>`;
    messages.scrollTop = messages.scrollHeight;

    const resp = await fetch("/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text, pdf_urls: collectPdfUrls() })
    });

    if (!resp.ok) {
        messages.innerHTML += `<div class="msg bot">FinAI：研究失败，请稍后重试。</div>`;
        return;
    }

    const data = await resp.json();
    if (data.report) {
        messages.innerHTML += `<div class="msg bot">FinAI：${data.report}</div>`;
    }

    if (data.sources && data.sources.length > 0) {
        const items = data.sources.map(s => `<div>• ${s.title} - ${s.url}</div>`).join("");
        messages.innerHTML += `<div class="msg bot">FinAI：来源<br/>${items}</div>`;
    }

    messages.scrollTop = messages.scrollHeight;
    renderCharts(data.chart || {});
}
