"use client";

import React, { useState } from "react";
import { MessageCircle, X } from "lucide-react";
import ChatPanel from "./ChatPanel";

interface ChatbotFloatingButtonProps {
  jobId: string;
}

const ChatbotFloatingButton: React.FC<ChatbotFloatingButtonProps> = ({ jobId }) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={toggleChat}
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-r from-yellow-400 to-yellow-500 text-gray-900 shadow-dual-md transition-all duration-300 hover:from-yellow-500 hover:to-yellow-600 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:ring-offset-2"
        aria-label={isOpen ? "Close chat" : "Open chat"}
      >
        {isOpen ? (
          <X className="h-6 w-6" />
        ) : (
          <MessageCircle className="h-6 w-6" />
        )}
      </button>

      {/* Chat Panel */}
      {isOpen && (
        <div className="fixed bottom-24 right-6 z-40">
          <ChatPanel jobId={jobId} onClose={() => setIsOpen(false)} />
        </div>
      )}

      {/* Backdrop for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black bg-opacity-25 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
};

export default ChatbotFloatingButton;