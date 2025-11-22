"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";

// Types
export interface Question {
  id: string;
  text: string;
  type: "text" | "select" | "multiselect" | "number" | "date";
  options?: string[];
  required: boolean;
  help_text?: string;
  placeholder?: string;
}

export interface Answer {
  question_id: string;
  question_text: string;
  value: string | string[];
}

export interface PolicySection {
  section_number: string;
  section_title: string;
  section_content: string;
}

export interface GeneratedPolicy {
  title: string;
  content: string;
  sections: PolicySection[];
  metadata: Record<string, any>;
  version: string;
}

export type DraftStep = "select-type" | "questions" | "notes" | "preview" | "saved";

interface DraftPolicyState {
  // Current step in the flow
  currentStep: DraftStep;

  // Policy type selection
  selectedPolicyType: string | null;
  selectedPolicyTypeName: string | null;

  // Questions and answers
  questions: Question[];
  answers: Answer[];
  currentQuestionIndex: number;

  // Additional notes
  additionalNotes: string;

  // Generated policy
  generatedPolicy: GeneratedPolicy | null;

  // Status
  loading: boolean;
  error: string | null;

  // Actions
  selectPolicyType: (policyTypeId: string, policyTypeName: string) => void;
  setQuestions: (questions: Question[]) => void;
  answerQuestion: (questionId: string, questionText: string, value: string | string[]) => void;
  nextQuestion: () => void;
  previousQuestion: () => void;
  setAdditionalNotes: (notes: string) => void;
  setGeneratedPolicy: (policy: GeneratedPolicy) => void;
  savePolicy: () => Promise<void>;
  reset: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setCurrentStep: (step: DraftStep) => void;
}

const DraftPolicyContext = createContext<DraftPolicyState | undefined>(undefined);

const STORAGE_KEY = "draft-policy-state";

interface DraftPolicyProviderProps {
  children: ReactNode;
}

export function DraftPolicyProvider({ children }: DraftPolicyProviderProps) {
  const [currentStep, setCurrentStep] = useState<DraftStep>("select-type");
  const [selectedPolicyType, setSelectedPolicyType] = useState<string | null>(null);
  const [selectedPolicyTypeName, setSelectedPolicyTypeName] = useState<string | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Answer[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [additionalNotes, setAdditionalNotes] = useState("");
  const [generatedPolicy, setGeneratedPolicy] = useState<GeneratedPolicy | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load state from localStorage on mount
  useEffect(() => {
    const savedState = localStorage.getItem(STORAGE_KEY);
    if (savedState) {
      try {
        const parsed = JSON.parse(savedState);
        setCurrentStep(parsed.currentStep || "select-type");
        setSelectedPolicyType(parsed.selectedPolicyType || null);
        setSelectedPolicyTypeName(parsed.selectedPolicyTypeName || null);
        setQuestions(parsed.questions || []);
        setAnswers(parsed.answers || []);
        setCurrentQuestionIndex(parsed.currentQuestionIndex || 0);
        setAdditionalNotes(parsed.additionalNotes || "");
        setGeneratedPolicy(parsed.generatedPolicy || null);
      } catch (e) {
        console.error("Failed to load draft state from localStorage:", e);
      }
    }
  }, []);

  // Save state to localStorage whenever it changes
  useEffect(() => {
    const state = {
      currentStep,
      selectedPolicyType,
      selectedPolicyTypeName,
      questions,
      answers,
      currentQuestionIndex,
      additionalNotes,
      generatedPolicy,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [
    currentStep,
    selectedPolicyType,
    selectedPolicyTypeName,
    questions,
    answers,
    currentQuestionIndex,
    additionalNotes,
    generatedPolicy,
  ]);

  const selectPolicyType = (policyTypeId: string, policyTypeName: string) => {
    setSelectedPolicyType(policyTypeId);
    setSelectedPolicyTypeName(policyTypeName);
    setCurrentStep("questions");
  };

  const answerQuestion = (questionId: string, questionText: string, value: string | string[]) => {
    setAnswers((prev) => {
      const existing = prev.findIndex((a) => a.question_id === questionId);
      if (existing >= 0) {
        const updated = [...prev];
        updated[existing] = { question_id: questionId, question_text: questionText, value };
        return updated;
      }
      return [...prev, { question_id: questionId, question_text: questionText, value }];
    });
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex((prev) => prev + 1);
    } else {
      // All questions answered, move to notes step
      setCurrentStep("notes");
    }
  };

  const previousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex((prev) => prev - 1);
    }
  };

  const savePolicy = async () => {
    // This will be implemented when we integrate with the API
    // For now, just move to saved step
    setCurrentStep("saved");
  };

  const reset = () => {
    setCurrentStep("select-type");
    setSelectedPolicyType(null);
    setSelectedPolicyTypeName(null);
    setQuestions([]);
    setAnswers([]);
    setCurrentQuestionIndex(0);
    setAdditionalNotes("");
    setGeneratedPolicy(null);
    setLoading(false);
    setError(null);
    localStorage.removeItem(STORAGE_KEY);
  };

  const value: DraftPolicyState = {
    currentStep,
    selectedPolicyType,
    selectedPolicyTypeName,
    questions,
    answers,
    currentQuestionIndex,
    additionalNotes,
    generatedPolicy,
    loading,
    error,
    selectPolicyType,
    setQuestions,
    answerQuestion,
    nextQuestion,
    previousQuestion,
    setAdditionalNotes,
    setGeneratedPolicy,
    savePolicy,
    reset,
    setLoading,
    setError,
    setCurrentStep,
  };

  return <DraftPolicyContext.Provider value={value}>{children}</DraftPolicyContext.Provider>;
}

export function useDraftPolicy() {
  const context = useContext(DraftPolicyContext);
  if (context === undefined) {
    throw new Error("useDraftPolicy must be used within a DraftPolicyProvider");
  }
  return context;
}
