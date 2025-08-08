import React, { useState, useRef } from "react";

function ChatTools() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const eventSourceRef = useRef(null);

  const handleSend = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    setMessages((msgs) => [...msgs, { sender: "user", text: input }]);
    setLoading(true);
    let botMsg = "";
    let botMsgIndex = null;
    eventSourceRef.current = new EventSource(`/stream-tool?prompt=${encodeURIComponent(input)}`);
    eventSourceRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.data) {
          if (data.data.startsWith("Tool result:")) {
            setMessages((msgs) => [...msgs, { sender: "tool_result", text: data.data }]);
          } else {
            botMsg += data.data;
            setMessages((msgs) => {
              // Append to last bot message or add new
              const last = msgs[msgs.length - 1];
              if (last && last.sender === "bot" && botMsgIndex === msgs.length - 1) {
                // Update last bot message
                const updated = [...msgs];
                updated[botMsgIndex] = { sender: "bot", text: botMsg };
                return updated;
              } else {
                // Add new bot message
                botMsgIndex = msgs.length;
                return [...msgs, { sender: "bot", text: botMsg }];
              }
            });
          }
        }
      } catch {
        botMsg += event.data;
        setMessages((msgs) => {
          const last = msgs[msgs.length - 1];
          if (last && last.sender === "bot" && botMsgIndex === msgs.length - 1) {
            const updated = [...msgs];
            updated[botMsgIndex] = { sender: "bot", text: botMsg };
            return updated;
          } else {
            botMsgIndex = msgs.length;
            return [...msgs, { sender: "bot", text: botMsg }];
          }
        });
      }
    };
    eventSourceRef.current.onerror = () => {
      setLoading(false);
      eventSourceRef.current.close();
    };
    setInput("");
  };

  return (
    <div style={{ maxWidth: 600, margin: "40px auto", background: "#fff", borderRadius: 8, boxShadow: "0 2px 8px rgba(0,0,0,0.1)", padding: 24 }}>
      <div style={{ minHeight: 200, marginBottom: 16, padding: 8, background: "#fafafa", borderRadius: 4, border: "1px solid #eee" }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ marginBottom: 8 }}>
            <span style={{ color: msg.sender === "user" ? "#0078d4" : msg.sender === "tool_result" ? "#008000" : "#333", fontWeight: msg.sender === "user" || msg.sender === "tool_result" ? "bold" : "normal" }}>
              {msg.sender === "user" ? "You" : msg.sender === "tool_result" ? "Tool result" : "Bot"}:
            </span> {msg.text}
          </div>
        ))}
      </div>
      <form onSubmit={handleSend} style={{ display: "flex", gap: 8 }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          required
          style={{ flex: 1, padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
        />
        <button type="submit" disabled={loading} style={{ padding: "8px 16px", borderRadius: 4, border: "none", background: "#0078d4", color: "#fff", cursor: "pointer" }}>
          Send
        </button>
      </form>
    </div>
  );
}

export default ChatTools;
