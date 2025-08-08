import React, { useState, useRef } from "react";
import styles from "./ChatTools.module.css";

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
            // Extract tool name from the backend message
            // Format: "Tool result: <tool_name>: <result>"
            const match = data.data.match(/Tool result: ([^:]+): (.+)/);
            const toolName = match ? match[1] : "Unknown tool";
            const result = match ? match[2] : data.data;
            setMessages((msgs) => [...msgs, { sender: "tool_result", text: result, tool: toolName }]);
          } else {
            botMsg += data.data;
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
    <div className={styles.chatContainer}>
      <div className={styles.messages}>
        {messages.map((msg, i) => (
          <div key={i} className={styles.messageRow}>
            {msg.sender === "user" ? (
              <div className={styles.userMessage}>{msg.text}</div>
            ) : msg.sender === "tool_result" ? (
              <div className={styles.toolMessage}>
                Tool result{msg.tool ? ` (${msg.tool})` : ""}: {msg.text}
              </div>
            ) : (
              <div className={styles.botMessage}>{msg.text}</div>
            )}
          </div>
        ))}
      </div>
      <form onSubmit={handleSend} className={styles.formRow}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          required
          className={styles.input}
        />
        <button type="submit" disabled={loading} className={styles.button}>
          Send
        </button>
      </form>
    </div>
  );
}

export default ChatTools;
