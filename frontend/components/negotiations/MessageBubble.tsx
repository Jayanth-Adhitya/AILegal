"use client";

import { useAuth } from "@/contexts/AuthContext";
import type { NegotiationMessage } from "@/lib/types";
import { cn } from "@/lib/utils";
import { Check, CheckCheck } from "lucide-react";

interface MessageBubbleProps {
  message: NegotiationMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const { user } = useAuth();

  // System message (centered, gray)
  if (message.sender_type === "system") {
    return (
      <div className="flex justify-center">
        <div className="bg-gray-100 text-gray-600 px-4 py-2 rounded-lg text-sm italic max-w-md text-center">
          {message.content}
        </div>
      </div>
    );
  }

  // Check if message is from current user
  const isOwnMessage = message.sender_user_id === user?.id;

  // Format timestamp
  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className={cn("flex", isOwnMessage ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[70%] rounded-lg px-4 py-2",
          isOwnMessage
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-900"
        )}
      >
        {/* Sender name (for other user's messages) */}
        {!isOwnMessage && message.sender && (
          <div className="text-xs font-semibold mb-1 text-gray-600">
            {message.sender.company_name}
          </div>
        )}

        {/* Message content */}
        <div className="whitespace-pre-wrap break-words">{message.content}</div>

        {/* Timestamp and read status */}
        <div
          className={cn(
            "flex items-center gap-1 mt-1 text-xs",
            isOwnMessage ? "text-blue-100" : "text-gray-500"
          )}
        >
          <span>{formatTime(message.created_at)}</span>

          {/* Read indicators (for own messages) */}
          {isOwnMessage && (
            <span>
              {message.read_at ? (
                <CheckCheck className="h-3 w-3" />
              ) : (
                <Check className="h-3 w-3" />
              )}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
