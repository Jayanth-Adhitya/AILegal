"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { negotiationApi, API_BASE_URL } from "@/lib/api";
import type { NegotiationMessage, WebSocketMessage } from "@/lib/types";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Loader2, AlertCircle, WifiOff } from "lucide-react";
import { MessageBubble } from "./MessageBubble";
import { TypingIndicator } from "./TypingIndicator";

// Helper function to get cookie value
function getCookie(name: string): string | undefined {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift();
  return undefined;
}

interface ChatInterfaceProps {
  negotiationId: string;
}

export function ChatInterface({ negotiationId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<NegotiationMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [otherUserTyping, setOtherUserTyping] = useState(false);
  const [connected, setConnected] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);

  // Load initial message history
  useEffect(() => {
    loadMessages();
  }, [negotiationId]);

  // Setup WebSocket connection
  useEffect(() => {
    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [negotiationId]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  const loadMessages = async () => {
    try {
      setLoading(true);
      const response = await negotiationApi.getMessages(negotiationId);
      setMessages(response.messages);

      // Mark messages as read
      const unreadIds = response.messages
        .filter((m) => !m.read_at && m.sender_type === "user")
        .map((m) => m.id);

      if (unreadIds.length > 0) {
        await negotiationApi.markMessagesRead(negotiationId, unreadIds);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load messages");
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = () => {
    const wsToken = getCookie("ws_token");
    console.log("Connecting WebSocket - WS Token exists:", !!wsToken);

    if (!wsToken) {
      console.error("No ws_token cookie found - please log in again");
      setError("Not authenticated - please log in again");
      return;
    }

    // Convert http/https to ws/wss
    const wsUrl = API_BASE_URL.replace("http", "ws");
    const fullWsUrl = `${wsUrl}/ws/negotiations/${negotiationId}?token=${wsToken}`;
    console.log("WebSocket URL:", fullWsUrl.replace(wsToken, "***"));

    const ws = new WebSocket(fullWsUrl);

    ws.onopen = () => {
      console.log("WebSocket connection opened");
      setConnected(true);
      setError(null);
      reconnectAttemptsRef.current = 0;
    };

    ws.onmessage = (event) => {
      const data: WebSocketMessage = JSON.parse(event.data);

      switch (data.type) {
        case "message":
          // Add new message
          const newMessage: NegotiationMessage = {
            id: data.id!,
            negotiation_id: data.negotiation_id!,
            sender_user_id: data.sender_user_id,
            sender_type: data.sender_type!,
            content: data.content!,
            message_type: data.message_type!,
            created_at: data.created_at!,
            read_at: data.read_at,
            sender: data.sender,
          };
          setMessages((prev) => [...prev, newMessage]);
          break;

        case "typing":
          setOtherUserTyping(data.is_typing || false);
          break;

        case "read":
          // Update read status for messages
          if (data.message_ids) {
            setMessages((prev) =>
              prev.map((msg) =>
                data.message_ids!.includes(msg.id)
                  ? { ...msg, read_at: new Date().toISOString() }
                  : msg
              )
            );
          }
          break;

        case "ack":
          // Message acknowledged
          setSending(false);
          break;

        case "error":
          setError(data.message || "An error occurred");
          setSending(false);
          break;

        case "user_joined":
        case "user_left":
          // Could show notifications here
          break;
      }
    };

    ws.onerror = (error) => {
      // WebSocket errors are often transient and followed by a close event
      // Don't show error to user yet - let onclose handler deal with it
      console.warn("WebSocket connection error occurred");
      setConnected(false);
    };

    ws.onclose = (event) => {
      console.log("WebSocket closed:", {
        code: event.code,
        reason: event.reason,
        wasClean: event.wasClean
      });
      setConnected(false);

      // Don't reconnect if authentication failed (code 1008)
      if (event.code === 1008) {
        console.error("Authentication failed:", event.reason);
        setError(`Authentication failed: ${event.reason}`);
        return;
      }

      // Clear any previous errors during reconnection attempts
      if (reconnectAttemptsRef.current < 5) {
        setError(null);
      }

      // Attempt to reconnect with exponential backoff
      if (reconnectAttemptsRef.current < 5) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1}/5)`);
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptsRef.current++;
          connectWebSocket();
        }, delay);
      } else {
        setError("Failed to connect after 5 attempts. Please refresh the page.");
      }
    };

    wsRef.current = ws;
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || sending) return;

    const content = inputValue.trim();
    setInputValue("");
    setSending(true);
    setError(null);

    // Stop typing indicator
    if (isTyping) {
      sendTypingIndicator(false);
      setIsTyping(false);
    }

    try {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        // Send via WebSocket
        wsRef.current.send(
          JSON.stringify({
            type: "message",
            content,
          })
        );
      } else {
        // Fallback to HTTP
        const message = await negotiationApi.sendMessage(negotiationId, content);
        setMessages((prev) => [...prev, message]);
        setSending(false);
      }
    } catch (err: any) {
      setError(err.message || "Failed to send message");
      setSending(false);
      // Restore input value on error
      setInputValue(content);
    }
  };

  const sendTypingIndicator = (typing: boolean) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "typing",
          is_typing: typing,
        })
      );
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);

    // Send typing indicator
    if (!isTyping) {
      setIsTyping(true);
      sendTypingIndicator(true);
    }

    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Set timeout to stop typing indicator
    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false);
      sendTypingIndicator(false);
    }, 2000);
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[600px]">
      {/* Connection Status */}
      {!connected && (
        <Alert variant="destructive" className="mb-4">
          <WifiOff className="h-4 w-4" />
          <AlertDescription>
            Disconnected. Attempting to reconnect...
          </AlertDescription>
        </Alert>
      )}

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Messages */}
      <ScrollArea className="flex-1 pr-4 mb-4">
        <div className="space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500">
              <Send className="h-12 w-12 mb-2 opacity-50" />
              <p>No messages yet. Start the conversation!</p>
            </div>
          ) : (
            messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))
          )}

          {/* Typing Indicator */}
          {otherUserTyping && <TypingIndicator />}

          {/* Scroll anchor */}
          <div ref={scrollRef} />
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="flex gap-2">
        <Input
          value={inputValue}
          onChange={handleInputChange}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          disabled={sending || !connected}
          className="flex-1"
        />
        <Button
          onClick={sendMessage}
          disabled={!inputValue.trim() || sending || !connected}
          size="icon"
        >
          {sending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}
