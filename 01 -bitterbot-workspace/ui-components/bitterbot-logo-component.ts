import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'

interface BitterBotLogoProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  animated?: boolean
  glowIntensity?: number
}

export function BitterBotLogo({ size = 'md', animated = true, glowIntensity = 1 }: BitterBotLogoProps) {
  const [isHovered, setIsHovered] = useState(false)
  const [pulsePhase, setPulsePhase] = useState(0)
  
  // Continuous pulse effect
  useEffect(() => {
    if (!animated) return
    
    const interval = setInterval(() => {
      setPulsePhase((prev) => (prev + 1) % 360)
    }, 50)
    
    return () => clearInterval(interval)
  }, [animated])
  
  const sizes = {
    sm: { width: 40, height: 40, strokeWidth: 2 },
    md: { width: 60, height: 60, strokeWidth: 3 },
    lg: { width: 80, height: 80, strokeWidth: 4 },
    xl: { width: 120, height: 120, strokeWidth: 5 }
  }
  
  const { width, height, strokeWidth } = sizes[size]
  
  return (
    <motion.div
      className="relative inline-flex items-center justify-center"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      {/* Glow effect background */}
      <div 
        className="absolute inset-0 rounded-full blur-xl"
        style={{
          background: `radial-gradient(circle, rgba(168, 85, 247, ${0.6 * glowIntensity}) 0%, transparent 70%)`,
          transform: `scale(${isHovered ? 1.3 : 1})`,
          transition: 'transform 0.3s ease',
          filter: `blur(${isHovered ? 24 : 16}px)`
        }}
      />
      
      {/* Animated circuit lines */}
      <svg
        width={width}
        height={height}
        viewBox="0 0 100 100"
        className="relative z-10"
      >
        {/* Background circle */}
        <motion.circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke="url(#purpleGradient)"
          strokeWidth={strokeWidth}
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ duration: 1.5, ease: "easeOut" }}
        />
        
        {/* BB Letters */}
        <g className="fill-purple-900">
          {/* First B */}
          <path d="M 25 30 L 25 70 L 35 70 Q 45 70 45 60 Q 45 50 35 50 L 25 50 M 25 50 L 35 50 Q 45 50 45 40 Q 45 30 35 30 L 25 30" 
                fill="none" 
                stroke="url(#letterGradient)" 
                strokeWidth={strokeWidth}
                strokeLinecap="round"
                strokeLinejoin="round"
          />
          
          {/* Second B */}
          <path d="M 55 30 L 55 70 L 65 70 Q 75 70 75 60 Q 75 50 65 50 L 55 50 M 55 50 L 65 50 Q 75 50 75 40 Q 75 30 65 30 L 55 30" 
                fill="none" 
                stroke="url(#letterGradient)" 
                strokeWidth={strokeWidth}
                strokeLinecap="round"
                strokeLinejoin="round"
          />
        </g>
        
        {/* Circuit connections */}
        <g className="stroke-purple-400" opacity="0.8">
          {/* Left circuit */}
          <motion.path
            d="M 5 50 L 15 50 L 20 45"
            fill="none"
            strokeWidth={strokeWidth / 2}
            initial={{ pathLength: 0 }}
            animate={{ pathLength: animated ? [0, 1, 0] : 1 }}
            transition={{ 
              duration: 3,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
          
          {/* Right circuit */}
          <motion.path
            d="M 95 50 L 85 50 L 80 55"
            fill="none"
            strokeWidth={strokeWidth / 2}
            initial={{ pathLength: 0 }}
            animate={{ pathLength: animated ? [0, 1, 0] : 1 }}
            transition={{ 
              duration: 3,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 1.5
            }}
          />
          
          {/* Circuit nodes */}
          <motion.circle cx="5" cy="50" r="3" fill="currentColor" 
            animate={{ opacity: animated ? [0.3, 1, 0.3] : 1 }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <motion.circle cx="95" cy="50" r="3" fill="currentColor"
            animate={{ opacity: animated ? [0.3, 1, 0.3] : 1 }}
            transition={{ duration: 2, repeat: Infinity, delay: 1 }}
          />
        </g>
        
        {/* Gradient definitions */}
        <defs>
          <linearGradient id="purpleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#c084fc" />
            <stop offset="50%" stopColor="#a855f7" />
            <stop offset="100%" stopColor="#7c3aed" />
          </linearGradient>
          
          <linearGradient id="letterGradient" x1="0%" y1="0%" x2="100%" y2="100%">
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
    </motion.div>
  )
}

// Example usage in Header
export function HeaderWithLogo() {
  return (
    <header className="flex items-center gap-4 p-4 bg-gray-900/80 backdrop-blur-xl">
      <BitterBotLogo size="md" animated={true} glowIntensity={1.2} />
      <div>
        <h1 className="text-2xl font-bold">
          <span className="text-white">Bitter</span>
          <span className="text-purple-400">Bot</span>
        </h1>
        <p className="text-sm text-gray-400">Decentralized Intelligence</p>
      </div>
    </header>
  )
}