"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Mic, MicOff, X, Volume2 } from "lucide-react";
import ChatMessage from "./ChatMessage";
import VoiceRecorder from "./VoiceRecorder";
import { chatApi, voiceApi } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

interface ChatPanelProps {
  jobId: string;
  onClose?: () => void;
}

const ChatPanel: React.FC<ChatPanelProps> = ({ jobId, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hi there! I've reviewed your contract analysis. What would you like to know about it?",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      // Prepare chat history
      const history = messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      // Send message and handle streaming response
      const response = await chatApi.sendMessage(jobId, inputValue, history);

      let assistantContent = "";
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Process SSE stream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));

                if (data.content) {
                  assistantContent += data.content;
                  setMessages((prev) => {
                    const newMessages = [...prev];
                    const lastMessage = newMessages[newMessages.length - 1];
                    if (lastMessage.role === "assistant") {
                      lastMessage.content = assistantContent;
                    }
                    return newMessages;
                  });
                }

                if (data.done) {
                  break;
                }

                if (data.error) {
                  console.error("Chat error:", data.error);
                  setMessages((prev) => {
                    const newMessages = [...prev];
                    const lastMessage = newMessages[newMessages.length - 1];
                    if (lastMessage.role === "assistant") {
                      lastMessage.content = "Sorry, I encountered an error processing your request.";
                    }
                    return newMessages;
                  });
                  break;
                }
              } catch (e) {
                console.error("Error parsing SSE data:", e);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          role: "assistant",
          content: "Sorry, I couldn't process your request. Please try again.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleTranscription = (text: string) => {
    setInputValue(text);
    inputRef.current?.focus();
  };

  const playAudio = async (text: string) => {
    try {
      const audioBlob = await voiceApi.textToSpeech(text);
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      audio.play();

      // Clean up URL after playing
      audio.onended = () => URL.revokeObjectURL(audioUrl);
    } catch (error) {
      console.error("Error playing audio:", error);
    }
  };

  return (
    <div className="flex h-[600px] w-[400px] flex-col overflow-hidden rounded-lg bg-white shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between border-b bg-blue-600 p-4 text-white">
        <div>
          <h3 className="text-lg font-semibold">Contract Assistant</h3>
          <p className="text-sm opacity-90">Ask about your contract analysis</p>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="rounded-full p-1 hover:bg-blue-700"
            aria-label="Close chat"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto bg-gray-50 p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              onPlayAudio={() => playAudio(message.content)}
            />
          ))}
          {isLoading && (
            <div className="flex items-center space-x-2 text-gray-500">
              <div className="flex space-x-1">
                <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.3s]"></div>
                <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400 [animation-delay:-0.15s]"></div>
                <div className="h-2 w-2 animate-bounce rounded-full bg-gray-400"></div>
              </div>
              <span className="text-sm">Assistant is typing...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t bg-white p-4">
        <div className="flex items-center space-x-2">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your question..."
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            disabled={isLoading}
          />

          <VoiceRecorder
            onTranscription={handleTranscription}
            isRecording={isRecording}
            setIsRecording={setIsRecording}
          />

          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="rounded-lg bg-blue-600 p-2 text-white transition-colors hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            aria-label="Send message"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatPanel;