"use client";

import React, { useRef, useState, useEffect } from "react";
import { Mic, MicOff, Loader2 } from "lucide-react";
import { voiceApi } from "@/lib/api";

interface VoiceRecorderProps {
  onTranscription: (text: string) => void;
  isRecording: boolean;
  setIsRecording: (value: boolean) => void;
}

const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
  onTranscription,
  isRecording,
  setIsRecording,
}) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (isRecording) {
      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => {
          if (prev >= 59) {
            // Auto-stop after 60 seconds
            stopRecording();
            return 0;
          }
          return prev + 1;
        });
      }, 1000);
    } else {
      // Clear timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
      setRecordingTime(0);
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isRecording]);

  const startRecording = async () => {
    try {
      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm",
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      // Handle data available
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      // Handle recording stop
      mediaRecorder.onstop = async () => {
        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());

        // Create blob from chunks
        const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });

        // Process the audio
        await processAudio(audioBlob);
      };

      // Start recording
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Error starting recording:", error);
      alert("Unable to access microphone. Please check your permissions.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processAudio = async (audioBlob: Blob) => {
    setIsProcessing(true);

    try {
      // Convert to form data
      const formData = new FormData();
      formData.append("file", audioBlob, "recording.webm");
      formData.append("language", "en");
      formData.append("model", "whisper-large-v3-turbo");

      // Send to STT API
      const result = await voiceApi.speechToText(formData);

      if (result.transcription) {
        onTranscription(result.transcription);
      }
    } catch (error) {
      console.error("Error processing audio:", error);
      alert("Failed to transcribe audio. Please try again.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleToggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="relative">
      <button
        onClick={handleToggleRecording}
        disabled={isProcessing}
        className={`relative rounded-lg p-2 transition-all ${
          isRecording
            ? "bg-red-600 text-white animate-pulse hover:bg-red-700"
            : isProcessing
            ? "bg-gray-400 text-white cursor-not-allowed"
            : "bg-gray-200 text-gray-700 hover:bg-gray-300"
        }`}
        aria-label={isRecording ? "Stop recording" : "Start recording"}
        title={isRecording ? "Stop recording" : "Start voice recording"}
      >
        {isProcessing ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : isRecording ? (
          <>
            <MicOff className="h-5 w-5" />
            {/* Recording indicator */}
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
            </span>
          </>
        ) : (
          <Mic className="h-5 w-5" />
        )}
      </button>

      {/* Recording timer */}
      {isRecording && (
        <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
          {formatTime(recordingTime)}
        </div>
      )}
    </div>
  );
};

export default VoiceRecorder;