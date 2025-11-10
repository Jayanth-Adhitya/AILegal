"use client";

import React, { useState, useRef, useEffect } from "react";
import { Play, Pause, Volume2, VolumeX } from "lucide-react";

interface AudioPlayerProps {
  audioUrl: string;
  autoPlay?: boolean;
  onEnded?: () => void;
}

const AudioPlayer: React.FC<AudioPlayerProps> = ({
  audioUrl,
  autoPlay = false,
  onEnded,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [isMuted, setIsMuted] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    const audio = new Audio(audioUrl);
    audioRef.current = audio;

    // Set up event listeners
    audio.addEventListener("loadedmetadata", () => {
      setDuration(audio.duration);
    });

    audio.addEventListener("timeupdate", () => {
      setCurrentTime(audio.currentTime);
    });

    audio.addEventListener("ended", () => {
      setIsPlaying(false);
      setCurrentTime(0);
      if (onEnded) onEnded();
    });

    // Auto-play if requested
    if (autoPlay) {
      audio.play().then(() => {
        setIsPlaying(true);
      }).catch(console.error);
    }

    // Cleanup
    return () => {
      audio.pause();
      audio.src = "";
    };
  }, [audioUrl, autoPlay, onEnded]);

  const togglePlayPause = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
    } else {
      audioRef.current.play().then(() => {
        setIsPlaying(true);
      }).catch(console.error);
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!audioRef.current) return;
    const newTime = parseFloat(e.target.value);
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!audioRef.current) return;
    const newVolume = parseFloat(e.target.value);
    audioRef.current.volume = newVolume;
    setVolume(newVolume);
    if (newVolume > 0) {
      setIsMuted(false);
    }
  };

  const toggleMute = () => {
    if (!audioRef.current) return;

    if (isMuted) {
      audioRef.current.volume = volume;
      setIsMuted(false);
    } else {
      audioRef.current.volume = 0;
      setIsMuted(true);
    }
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  };

  return (
    <div className="flex items-center space-x-2 rounded-lg bg-gray-100 p-2">
      {/* Play/Pause Button */}
      <button
        onClick={togglePlayPause}
        className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        aria-label={isPlaying ? "Pause" : "Play"}
      >
        {isPlaying ? (
          <Pause className="h-4 w-4" />
        ) : (
          <Play className="h-4 w-4 ml-0.5" />
        )}
      </button>

      {/* Progress Bar */}
      <div className="flex-1">
        <input
          type="range"
          min="0"
          max={duration || 0}
          value={currentTime}
          onChange={handleSeek}
          className="w-full h-1 bg-gray-300 rounded-lg appearance-none cursor-pointer slider"
          style={{
            background: `linear-gradient(to right, #2563eb ${
              (currentTime / (duration || 1)) * 100
            }%, #d1d5db ${(currentTime / (duration || 1)) * 100}%)`,
          }}
        />
      </div>

      {/* Time Display */}
      <div className="text-xs text-gray-600 whitespace-nowrap">
        {formatTime(currentTime)} / {formatTime(duration)}
      </div>

      {/* Volume Controls */}
      <div className="flex items-center space-x-1">
        <button
          onClick={toggleMute}
          className="p-1 text-gray-600 hover:text-gray-800"
          aria-label={isMuted ? "Unmute" : "Mute"}
        >
          {isMuted || volume === 0 ? (
            <VolumeX className="h-4 w-4" />
          ) : (
            <Volume2 className="h-4 w-4" />
          )}
        </button>

        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={isMuted ? 0 : volume}
          onChange={handleVolumeChange}
          className="w-16 h-1 bg-gray-300 rounded-lg appearance-none cursor-pointer"
          style={{
            background: `linear-gradient(to right, #2563eb ${
              (isMuted ? 0 : volume) * 100
            }%, #d1d5db ${(isMuted ? 0 : volume) * 100}%)`,
          }}
        />
      </div>
    </div>
  );
};

export default AudioPlayer;