"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { ArrowLeft, ArrowRight, HelpCircle } from "lucide-react";
import { useDraftPolicy, Question } from "@/contexts/DraftPolicyContext";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function Questionnaire() {
  const { questions, answers, currentQuestionIndex, answerQuestion, nextQuestion, previousQuestion } = useDraftPolicy();
  const [currentAnswer, setCurrentAnswer] = useState<string | string[]>("");
  const [validationError, setValidationError] = useState<string | null>(null);

  const currentQuestion = questions[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / questions.length) * 100;

  // Load existing answer when question changes
  useEffect(() => {
    if (currentQuestion) {
      const existingAnswer = answers.find((a) => a.question_id === currentQuestion.id);
      if (existingAnswer) {
        setCurrentAnswer(existingAnswer.value);
      } else {
        setCurrentAnswer(currentQuestion.type === "multiselect" ? [] : "");
      }
      setValidationError(null);
    }
  }, [currentQuestion, answers]);

  if (!currentQuestion) {
    return null;
  }

  const handleNext = () => {
    // Validate required fields
    if (currentQuestion.required) {
      if (Array.isArray(currentAnswer) && currentAnswer.length === 0) {
        setValidationError("This question is required");
        return;
      }
      if (typeof currentAnswer === "string" && !currentAnswer.trim()) {
        setValidationError("This question is required");
        return;
      }
    }

    // Save answer
    answerQuestion(currentQuestion.id, currentQuestion.text, currentAnswer);

    // Move to next
    nextQuestion();
  };

  const handlePrevious = () => {
    // Save current answer before going back
    if (currentAnswer) {
      answerQuestion(currentQuestion.id, currentQuestion.text, currentAnswer);
    }
    previousQuestion();
  };

  const handleMultiSelectChange = (value: string, checked: boolean) => {
    setValidationError(null);
    const current = Array.isArray(currentAnswer) ? currentAnswer : [];
    if (checked) {
      setCurrentAnswer([...current, value]);
    } else {
      setCurrentAnswer(current.filter((v) => v !== value));
    }
  };

  const renderQuestionInput = () => {
    // Log question type for debugging
    if (currentQuestion.type !== "text" && currentQuestion.type !== "select" &&
        currentQuestion.type !== "multiselect" && currentQuestion.type !== "number" &&
        currentQuestion.type !== "date") {
      console.warn(`Unknown question type: "${currentQuestion.type}" for question: "${currentQuestion.text}"`);
    }

    switch (currentQuestion.type) {
      case "text":
      case "number":
      case "date":
        if (currentQuestion.text.toLowerCase().includes("describe") ||
            currentQuestion.text.toLowerCase().includes("explain") ||
            currentQuestion.text.toLowerCase().includes("list") ||
            currentQuestion.text.toLowerCase().includes("identify") ||
            currentQuestion.text.toLowerCase().includes("provide") ||
            currentQuestion.text.toLowerCase().includes("detail")) {
          return (
            <Textarea
              value={currentAnswer as string}
              onChange={(e) => {
                setCurrentAnswer(e.target.value);
                setValidationError(null);
              }}
              placeholder={currentQuestion.placeholder || "Enter your answer..."}
              className="min-h-[120px] border-gray-300 focus:border-yellow-400 focus:ring-yellow-400"
            />
          );
        }
        return (
          <Input
            type={currentQuestion.type}
            value={currentAnswer as string}
            onChange={(e) => {
              setCurrentAnswer(e.target.value);
              setValidationError(null);
            }}
            placeholder={currentQuestion.placeholder || "Enter your answer..."}
            className="border-gray-300 focus:border-yellow-400 focus:ring-yellow-400"
          />
        );

      case "select":
        return (
          <Select
            value={Array.isArray(currentAnswer) ? "" : currentAnswer}
            onValueChange={(value) => {
              setCurrentAnswer(value);
              setValidationError(null);
            }}
          >
            <SelectTrigger className="border-gray-300 focus:border-yellow-400 focus:ring-yellow-400">
              <SelectValue placeholder="Select an option..." />
            </SelectTrigger>
            <SelectContent>
              {currentQuestion.options?.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case "multiselect":
        return (
          <div className="space-y-3">
            {currentQuestion.options?.map((option) => (
              <div key={option} className="flex items-center space-x-2">
                <Checkbox
                  id={`option-${option}`}
                  checked={Array.isArray(currentAnswer) && currentAnswer.includes(option)}
                  onCheckedChange={(checked) => handleMultiSelectChange(option, checked as boolean)}
                />
                <Label htmlFor={`option-${option}`} className="cursor-pointer">
                  {option}
                </Label>
              </div>
            ))}
          </div>
        );

      default:
        // Fallback: treat unknown types as text input with textarea
        return (
          <Textarea
            value={currentAnswer as string}
            onChange={(e) => {
              setCurrentAnswer(e.target.value);
              setValidationError(null);
            }}
            placeholder={currentQuestion.placeholder || "Enter your answer..."}
            className="min-h-[120px] border-gray-300 focus:border-yellow-400 focus:ring-yellow-400"
          />
        );
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      {/* Progress indicator */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">
            Question {currentQuestionIndex + 1} of {questions.length}
          </span>
          <span className="text-sm text-gray-500">{Math.round(progress)}% Complete</span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      {/* Question card */}
      <Card className="border-2 border-yellow-200/50 shadow-dual-sm">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-xl flex items-center gap-2">
                {currentQuestion.text}
                {currentQuestion.required && <span className="text-red-500">*</span>}
                {currentQuestion.help_text && (
                  <TooltipProvider>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <HelpCircle className="h-4 w-4 text-gray-400 cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent>
                        <p className="max-w-xs">{currentQuestion.help_text}</p>
                      </TooltipContent>
                    </Tooltip>
                  </TooltipProvider>
                )}
              </CardTitle>
              {currentQuestion.help_text && (
                <CardDescription className="mt-2">{currentQuestion.help_text}</CardDescription>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Question input */}
          {renderQuestionInput()}

          {/* Validation error */}
          {validationError && (
            <div className="text-sm text-red-600 flex items-center gap-2">
              <HelpCircle className="h-4 w-4" />
              {validationError}
            </div>
          )}

          {/* Navigation buttons */}
          <div className="flex justify-between gap-3 pt-4">
            <Button
              variant="outline"
              onClick={handlePrevious}
              disabled={currentQuestionIndex === 0}
              className="border-gray-300"
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Previous
            </Button>
            <Button
              onClick={handleNext}
              className="bg-gradient-to-r from-yellow-400 to-yellow-500 text-gray-900 hover:from-yellow-500 hover:to-yellow-600 shadow-dual-sm"
            >
              {currentQuestionIndex === questions.length - 1 ? "Continue to Notes" : "Next"}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
