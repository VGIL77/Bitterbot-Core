import { motion } from 'framer-motion'

interface HeaderProps {
  onToggleSidebar: () => void
}

export function Header({ onToggleSidebar }: HeaderProps) {
  return (
    <header className="relative z-20 border-b border-purple-500/20 bg-gray-900/80 backdrop-blur-xl">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          {/* Mobile menu button */}
          <button
            onClick={onToggleSidebar}
            className="md:hidden p-2 rounded-lg hover:bg-gray-800/50 transition-colors"
          >
            <svg className="h-6 w-6 text-purple-300" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 5.75h16.5M3.75 12h16.5M3.75 18.25h16.5" />
            </svg>
          </button>
          
          {/* Logo and brand */}
          <div className="flex items-center gap-3">
            {/* Animated Logo */}
            <div className="relative w-12 h-12">
              {/* Glow effect */}
              <div className="absolute inset-[-10px] rounded-full bg-purple-500/40 blur-xl animate-pulse" />
              
              {/* Logo SVG */}
              <svg viewBox="0 0 100 100" className="relative z-10 w-full h-full">
                <defs>
                  <linearGradient id="purple-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#c084fc" />
                    <stop offset="50%" stopColor="#a855f7" />
                    <stop offset="100%" stopColor="#7c3aed" />
                  </linearGradient>
                  <linearGradient id="letter-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#e9d5ff" />
                    <stop offset="50%" stopColor="#c084fc" />
                    <stop offset="100%" stopColor="#a855f7" />
                  </linearGradient>
                </defs>
                
                {/* Outer circle */}
                <motion.circle
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="url(#purple-gradient)"
                  strokeWidth="4"
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 1.5, ease: "easeOut" }}
                />
                
                {/* BB Letters */}
                <g>
                  <path
                    d="M 25 30 L 25 70 L 35 70 Q 45 70 45 60 Q 45 50 35 50 L 25 50 M 25 50 L 35 50 Q 45 50 45 40 Q 45 30 35 30 L 25 30"
                    fill="none"
                    stroke="url(#letter-gradient)"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M 55 30 L 55 70 L 65 70 Q 75 70 75 60 Q 75 50 65 50 L 55 50 M 55 50 L 65 50 Q 75 50 75 40 Q 75 30 65 30 L 55 30"
                    fill="none"
                    stroke="url(#letter-gradient)"
                    strokeWidth="4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </g>
                
                {/* Circuit connections */}
                <g opacity="0.8">
                  <motion.path
                    d="M 5 50 L 15 50 L 20 45"
                    fill="none"
                    stroke="#c084fc"
                    strokeWidth="2"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: [0, 1, 0] }}
                    transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                  />
                  <motion.path
                    d="M 95 50 L 85 50 L 80 55"
                    fill="none"
                    stroke="#c084fc"
                    strokeWidth="2"
                    initial={{ pathLength: 0 }}
                    animate={{ pathLength: [0, 1, 0] }}
                    transition={{ duration: 3, repeat: Infinity, ease: "easeInOut", delay: 1.5 }}
                  />
                  <motion.circle
                    cx="5"
                    cy="50"
                    r="3"
                    fill="#c084fc"
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                  <motion.circle
                    cx="95"
                    cy="50"
                    r="3"
                    fill="#c084fc"
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 2, repeat: Infinity, delay: 1 }}
                  />
                </g>
              </svg>
            </div>
            
            {/* Brand text */}
            <div>
              <h1 className="text-xl md:text-2xl font-bold">
                <span className="text-white">Bitter</span>
                <span className="text-purple-400">Bot</span>
              </h1>
              <p className="text-xs md:text-sm text-gray-400 hidden sm:block">
                Decentralized Intelligence
              </p>
            </div>
          </div>
        </div>
        
        {/* Right side actions could go here */}
        <div className="flex items-center gap-2">
          {/* Future: Settings, notifications, etc */}
        </div>
      </div>
    </header>
  )
}