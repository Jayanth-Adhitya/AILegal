"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, AlertCircle, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Policy } from "@/lib/types";
import { policyApi } from "@/lib/api";
import ReactMarkdown from "react-markdown";

interface PolicyChatbotProps {
  policy?: Policy;  // Optional - if not provided, chat about all policies
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export function PolicyChatbot({ policy }: PolicyChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const suggestedQuestions = policy
    ? [
        "What are the key terms of this policy?",
        "Who does this policy apply to?",
        "What are the main obligations under this policy?",
        "Are there any important dates or deadlines?",
      ]
    : [
        "What policies do we have?",
        "Summarize our liability policies",
        "What are the key compliance requirements across our policies?",
        "Compare our IP and confidentiality policies",
      ];

  const handleSendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      // Use general chat if no specific policy, otherwise use policy-specific chat
      const data = policy
        ? await policyApi.sendChatMessage(
            policy.id,
            userMessage.content,
            messages.map((m) => ({
              role: m.role,
              content: m.content,
            }))
          )
        : await policyApi.sendGeneralChatMessage(
            userMessage.content,
            messages.map((m) => ({
              role: m.role,
              content: m.content,
            }))
          );

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      inputRef.current?.focus();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
    inputRef.current?.focus();
  };

  const isInputValid = input.trim().length > 0 && input.length <= 5000;

  return (
    <Card className="h-[calc(100vh-300px)] flex flex-col">
      <CardHeader className="border-b">
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-blue-600" />
          {policy ? `${policy.title} - Chat Assistant` : "Policy Chat Assistant"}
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-6">
              <div className="space-y-2">
                <Sparkles className="h-12 w-12 text-blue-600 mx-auto" />
                <h3 className="text-lg font-semibold text-gray-900">
                  {policy
                    ? "Ask me anything about this policy!"
                    : "Ask me anything about your policies!"}
                </h3>
                <p className="text-sm text-gray-600">
                  {policy
                    ? "I can help you understand the policy content, find specific information, and answer your questions."
                    : "I can help you understand your company policies, compare them, find specific information, and answer your questions."}
                </p>
              </div>

              <div className="w-full max-w-md space-y-2">
                <p className="text-xs font-medium text-gray-500 uppercase">
                  Suggested Questions
                </p>
                {suggestedQuestions.map((question, index) => (
                  <button
                    key={index}
                    onClick={() => handleSuggestedQuestion(question)}
                    className="w-full text-left px-4 py-2 text-sm bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${
                    message.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-4 py-2 ${
                      message.role === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 text-gray-900"
                    }`}
                  >
                    {message.role === "assistant" ? (
                      <div className="prose prose-sm max-w-none prose-p:my-2 prose-ul:my-2 prose-ol:my-2">
                        <ReactMarkdown>{message.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-lg px-4 py-2">
                    <Loader2 className="h-4 w-4 animate-spin text-gray-600" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="px-6 pb-2">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          </div>
        )}

        {/* Input Area */}
        <div className="border-t p-4">
          <div className="flex gap-2">
            <div className="flex-1">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type your question... (Press Enter to send, Shift+Enter for new line)"
                disabled={loading}
                className="w-full min-h-[60px] max-h-[200px] px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:cursor-not-allowed resize-none"
                rows={2}
              />
              <div className="flex justify-between items-center mt-1 px-1">
                <p className="text-xs text-gray-500">
                  {input.length} / 5000 characters
                </p>
                {input.length > 5000 && (
                  <p className="text-xs text-red-600">Character limit exceeded</p>
                )}
              </div>
            </div>
            <Button
              onClick={handleSendMessage}
              disabled={!isInputValid || loading}
              className="self-end"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Send className="h-4 w-4 mr-2" />
                  Send
                </>
              )}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
