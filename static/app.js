async function send() {
    const input = document.getElementById("input");
    const text = input.value;
    if (!text) return;

    const messages = document.getElementById("messages");
    messages.innerHTML += `<div class="msg user">你：${text}</div>`;
    input.value = "";

    const resp = await fetch("/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text })
    });

    const data = await resp.json();
    messages.innerHTML += `<div class="msg bot">FinAI：${data.result}</div>`;
}
