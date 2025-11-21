"use client";

import React from "react";
import { Volume2, User, Bot } from "lucide-react";

interface MessageProps {
  message: {
    id: string;
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
  };
  onPlayAudio?: () => void;
}

const ChatMessage: React.FC<MessageProps> = ({ message, onPlayAudio }) => {
  const isUser = message.role === "user";

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} group`}>
      <div
        className={`flex max-w-[85%] items-start space-x-2 ${
          isUser ? "flex-row-reverse space-x-reverse" : ""
        }`}
      >
        {/* Avatar */}
        <div
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full overflow-hidden ${
            isUser ? "bg-gradient-to-r from-yellow-400 to-yellow-500" : "bg-white"
          }`}
        >
          {isUser ? (
            <User className="h-4 w-4 text-gray-900" />
          ) : (
            <img
              src="/assets/cirilla_bot/cirilla-mascot.png"
              alt="Cirilla AI"
              className="h-full w-full object-cover"
            />
          )}
        </div>

        {/* Message Content */}
        <div className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}>
          <div
            className={`rounded-lg px-4 py-2 ${
              isUser
                ? "bg-gradient-to-r from-yellow-400 to-yellow-500 text-gray-900"
                : "bg-white border border-gray-200 text-gray-800"
            }`}
          >
            <p className="whitespace-pre-wrap break-words text-sm">{message.content}</p>
          </div>

          {/* Timestamp and Actions */}
          <div
            className={`mt-1 flex items-center space-x-2 text-xs text-gray-500 ${
              isUser ? "flex-row-reverse space-x-reverse" : ""
            }`}
          >
            <span>{formatTime(message.timestamp)}</span>

            {/* TTS Button for assistant messages */}
            {!isUser && onPlayAudio && (
              <button
                onClick={onPlayAudio}
                className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-gray-100 rounded"
                aria-label="Play audio"
                title="Play audio"
              >
                <Volume2 className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;