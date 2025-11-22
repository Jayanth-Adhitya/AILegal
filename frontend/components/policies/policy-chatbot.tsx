"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, AlertCircle, Sparkles, MessageSquare, PenTool } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Policy } from "@/lib/types";
import { policyApi } from "@/lib/api";
import ReactMarkdown from "react-markdown";
import { DraftPolicyProvider } from "@/contexts/DraftPolicyContext";
import { PolicyTypeSelector } from "./policy-type-selector";
import { Questionnaire } from "./questionnaire";
import { AdditionalNotesStep } from "./additional-notes-step";
import { PolicyPreview } from "./policy-preview";
import { useDraftPolicy } from "@/contexts/DraftPolicyContext";

interface PolicyChatbotProps {
  policy?: Policy;  // Optional - if not provided, chat about all policies
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

function DraftingWizardContent() {
  const { currentStep, error, reset } = useDraftPolicy();

  // Success state
  if (currentStep === "saved") {
    return (
      <div className="max-w-2xl mx-auto py-8">
        <Card className="border-2 border-green-200/50 bg-green-50/30">
          <CardContent className="pt-12 pb-12 text-center">
            <div className="flex justify-center mb-6">
              <div className="p-4 bg-gradient-to-r from-green-500 to-green-600 rounded-full">
                <Sparkles className="h-12 w-12 text-white" />
              </div>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-3">Policy Saved Successfully!</h2>
            <p className="text-lg text-gray-600 mb-6">
              Your policy has been saved and is now available in your policy library.
            </p>
            <Button
              onClick={reset}
              className="bg-gradient-to-r from-yellow-400 to-yellow-500 text-gray-900 hover:from-yellow-500 hover:to-yellow-600 shadow-dual-sm"
            >
              <Sparkles className="mr-2 h-4 w-4" />
              Draft Another Policy
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-3xl mx-auto">
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button onClick={reset} variant="outline">
          Start Over
        </Button>
      </div>
    );
  }

  // Render appropriate step
  switch (currentStep) {
    case "select-type":
      return <PolicyTypeSelector />;
    case "questions":
      return <Questionnaire />;
    case "notes":
      return <AdditionalNotesStep />;
    case "preview":
      return <PolicyPreview />;
    default:
      return <PolicyTypeSelector />;
  }
}

function PolicyChatbotInner({ policy }: PolicyChatbotProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showWizard, setShowWizard] = useState(false);
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
    <div className="space-y-6">
      {/* Conditional Rendering - Show Wizard or Chat */}
      {showWizard ? (
        <div className="space-y-4">
          <Button
            onClick={() => setShowWizard(false)}
            variant="outline"
            className="mb-4"
          >
            <MessageSquare className="mr-2 h-4 w-4" />
            Back to Chat
          </Button>
          <DraftingWizardContent />
        </div>
      ) : (
        <Card className="flex flex-col">
          <CardHeader className="border-b">
            <CardTitle>
              {policy ? `${policy.title} - Cirilla AI` : "Cirilla AI - Policy Assistant"}
            </CardTitle>
          </CardHeader>

      <CardContent className="p-6 overflow-hidden">
        {/* Messages Area */}
        <div className="space-y-4">
          {messages.length === 0 ? (
            <div className="flex items-center gap-8 w-full">
              {/* Left side - Cirilla Image */}
              <div className="flex-shrink-0 relative h-56 w-56">
                <img
                  src="/assets/cirilla_bot/cirilla-bot-analyze.png"
                  alt="Cirilla AI"
                  className="h-56 w-56 object-contain"
                  style={{
                    maskImage: 'linear-gradient(to bottom, black 70%, transparent 100%)',
                    WebkitMaskImage: 'linear-gradient(to bottom, black 70%, transparent 100%)'
                  }}
                />
              </div>

              {/* Right side - Content */}
              <div className="flex-1 space-y-5">
                <div className="space-y-2">
                  <h3 className="text-xl font-semibold text-gray-900">
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

                <div className="space-y-2.5">
                  <p className="text-xs font-medium text-gray-500 uppercase">
                    Suggested Questions
                  </p>
                  <div className="grid grid-cols-1 gap-2.5">
                    {suggestedQuestions.map((question, index) => (
                      <button
                        key={index}
                        onClick={() => handleSuggestedQuestion(question)}
                        className="w-full text-left px-4 py-3 text-sm bg-gray-50 hover:bg-yellow-50 hover:border-yellow-200 border border-gray-200 rounded-lg transition-colors"
                      >
                        {question}
                      </button>
                    ))}
                    {/* Draft Policy Button */}
                    {!policy && (
                      <button
                        onClick={() => setShowWizard(true)}
                        className="w-full text-left px-4 py-3 text-sm bg-gradient-to-r from-yellow-400 to-yellow-500 text-gray-900 hover:from-yellow-500 hover:to-yellow-600 border border-yellow-300 rounded-lg transition-colors font-medium flex items-center gap-2"
                      >
                        <Sparkles className="h-4 w-4" />
                        Draft a New Policy
                      </button>
                    )}
                  </div>
                </div>
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
                        ? "bg-gradient-to-r from-yellow-400 to-yellow-500 text-gray-900"
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

      </CardContent>

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
                className="w-full min-h-[60px] max-h-[200px] px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-yellow-400 disabled:bg-gray-50 disabled:cursor-not-allowed resize-none"
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
        </Card>
      )}
    </div>
  );
}

export function PolicyChatbot(props: PolicyChatbotProps) {
  return (
    <DraftPolicyProvider>
      <PolicyChatbotInner {...props} />
    </DraftPolicyProvider>
  );
}
