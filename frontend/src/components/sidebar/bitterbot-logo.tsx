'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

interface BitterBotLogoProps {
  size?: number;
  className?: string;
  animated?: boolean;
  glowIntensity?: number;
}

export function BitterBotLogo({ 
  size = 24, 
  className = '',
  animated = true,
  glowIntensity = 1 
}: BitterBotLogoProps) {
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [pulsePhase, setPulsePhase] = useState(0);

  // After mount, we can access the theme
  useEffect(() => {
    setMounted(true);
  }, []);

  // Continuous pulse effect
  useEffect(() => {
    if (!animated) return;
    
    const interval = setInterval(() => {
      setPulsePhase((prev) => (prev + 1) % 360);
    }, 50);
    
    return () => clearInterval(interval);
  }, [animated]);

  const strokeWidth = Math.max(2, size / 20);

  return (
    <div 
      className={`relative inline-flex items-center justify-center ${className}`}
      style={{ width: size, height: size }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Glow effect background */}
      <div 
        className="absolute inset-0 rounded-full"
        style={{
          background: `radial-gradient(circle, rgba(168, 85, 247, ${0.6 * glowIntensity}) 0%, transparent 70%)`,
          transform: `scale(${isHovered ? 1.3 : 1})`,
          transition: 'transform 0.3s ease',
          filter: `blur(${isHovered ? 24 : 16}px)`
        }}
      />
      
      {/* Main SVG */}
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        className="relative z-10"
        style={{
          filter: 'drop-shadow(0 0 10px rgba(139, 92, 246, 0.5))',
          transform: isHovered ? 'scale(1.05)' : 'scale(1)',
          transition: 'transform 0.3s ease'
        }}
      >
        {/* Background circle */}
        <circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke="url(#bbPurpleGradient)"
          strokeWidth={strokeWidth}
          className="bb-circle-animate"
        />
        
        {/* BB Letters */}
        <g className="fill-none">
          {/* First B - mirrored for brain-like appearance */}
          <path 
            d="M 25 30 L 25 70 L 35 70 Q 45 70 45 60 Q 45 50 35 50 L 25 50 M 25 50 L 35 50 Q 45 50 45 40 Q 45 30 35 30 L 25 30" 
            stroke="url(#bbLetterGradient)" 
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeLinejoin="round"
            transform="scale(-1, 1) translate(-100, 0)"
          />
          
          {/* Second B */}
          <path 
            d="M 55 30 L 55 70 L 65 70 Q 75 70 75 60 Q 75 50 65 50 L 55 50 M 55 50 L 65 50 Q 75 50 75 40 Q 75 30 65 30 L 55 30" 
            stroke="url(#bbLetterGradient)" 
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </g>
        
        {/* Circuit connections */}
        <g className="stroke-purple-400" opacity="0.8">
          {/* Left circuit */}
          <path
            d="M 5 50 L 15 50 L 20 45"
            fill="none"
            strokeWidth={strokeWidth / 2}
            className={animated ? "bb-circuit-animate" : ""}
          />
          
          {/* Right circuit */}
          <path
            d="M 95 50 L 85 50 L 80 55"
            fill="none"
            strokeWidth={strokeWidth / 2}
            className={animated ? "bb-circuit-animate-delayed" : ""}
          />
          
          {/* Circuit nodes */}
          <circle 
            cx="5" 
            cy="50" 
            r="3" 
            fill="currentColor"
            className={animated ? "bb-node-pulse" : ""}
          />
          <circle 
            cx="95" 
            cy="50" 
            r="3" 
            fill="currentColor"
            className={animated ? "bb-node-pulse-delayed" : ""}
          />
        </g>
        
        {/* Gradient definitions */}
        <defs>
          <linearGradient id="bbPurpleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#c084fc" />
            <stop offset="50%" stopColor="#a855f7" />
            <stop offset="100%" stopColor="#7c3aed" />
          </linearGradient>
          
          <linearGradient id="bbLetterGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#e9d5ff" />
            <stop offset="50%" stopColor="#c084fc" />
            <stop offset="100%" stopColor="#a855f7" />
          </linearGradient>
        </defs>
      </svg>
      
      {/* Pulse effect overlay */}
      {animated && (
        <div 
          className="absolute inset-0 rounded-full pointer-events-none"
          style={{
            background: `radial-gradient(circle, transparent 30%, rgba(168, 85, 247, ${Math.sin(pulsePhase * Math.PI / 180) * 0.2}) 70%)`,
          }}
        />
      )}

      <style jsx>{`
        @keyframes circuitPath {
          0% { stroke-dashoffset: 100; opacity: 0; }
          50% { stroke-dashoffset: 0; opacity: 1; }
          100% { stroke-dashoffset: -100; opacity: 0; }
        }

        @keyframes nodePulse {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 1; }
        }

        @keyframes drawCircle {
          from { stroke-dasharray: 0 283; }
          to { stroke-dasharray: 283 283; }
        }

        .bb-circle-animate {
          animation: drawCircle 1.5s ease-out forwards;
        }

        .bb-circuit-animate {
          stroke-dasharray: 100;
          animation: circuitPath 3s ease-in-out infinite;
        }

        .bb-circuit-animate-delayed {
          stroke-dasharray: 100;
          animation: circuitPath 3s ease-in-out infinite;
          animation-delay: 1.5s;
        }

        .bb-node-pulse {
          animation: nodePulse 2s ease-in-out infinite;
        }

        .bb-node-pulse-delayed {
          animation: nodePulse 2s ease-in-out infinite;
          animation-delay: 1s;
        }
      `}</style>
    </div>
  );
}