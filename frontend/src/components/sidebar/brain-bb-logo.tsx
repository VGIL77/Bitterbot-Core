import React from 'react';

interface BrainBBLogoProps {
  className?: string;
}

export const BrainBBLogo: React.FC<BrainBBLogoProps> = ({ className = "" }) => (
    <svg viewBox="0 0 100 100" width="100%" height="100%" className={className}>
      <defs>
        <linearGradient id="bbCircleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#c084fc" />
          <stop offset="50%" stopColor="#a855f7" />
          <stop offset="100%" stopColor="#7c3aed" />
        </linearGradient>
        <linearGradient id="bbLetterGrad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#e9d5ff" />
          <stop offset="50%" stopColor="#c084fc" />
          <stop offset="100%" stopColor="#a855f7" />
        </linearGradient>
      </defs>
      
      <circle cx="50" cy="50" r="45" fill="none" stroke="url(#bbCircleGrad)" strokeWidth="3"/>
      
      <path d="M 47 25 L 47 75 L 35 75 Q 23 75 23 63 Q 23 50 35 50 L 47 50 M 47 50 L 35 50 Q 23 50 23 37 Q 23 25 35 25 L 47 25" 
            fill="none" 
            stroke="url(#bbLetterGrad)" 
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"/>
      
      <path d="M 53 25 L 53 75 L 65 75 Q 77 75 77 63 Q 77 50 65 50 L 53 50 M 53 50 L 65 50 Q 77 50 77 37 Q 77 25 65 25 L 53 25" 
            fill="none" 
            stroke="url(#bbLetterGrad)" 
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"/>
      
      <line x1="50" y1="30" x2="50" y2="70" 
            stroke="url(#bbLetterGrad)" 
            strokeWidth="1" 
            opacity="0.3"/>
    </svg>
  );