'use client';

import { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ModalProviders } from '@/providers/modal-providers';
import { useAuth } from '@/components/AuthProvider';

export default function Home() {
  const [mounted, setMounted] = useState(false);
  const [query, setQuery] = useState('');
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [currentPos, setCurrentPos] = useState({ x: 0, y: 0 });
  const animationRef = useRef<number>();
  const router = useRouter();
  const { user } = useAuth();

  useEffect(() => {
    setMounted(true);
  }, []);

  // Mouse move effect
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const x = (e.clientX / window.innerWidth) - 0.5;
      const y = (e.clientY / window.innerHeight) - 0.5;
      setMousePos({ x, y });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  // Smooth animation
  useEffect(() => {
    const animate = () => {
      setCurrentPos(prev => ({
        x: prev.x + (mousePos.x - prev.x) * 0.05,
        y: prev.y + (mousePos.y - prev.y) * 0.05
      }));
      animationRef.current = requestAnimationFrame(animate);
    };
    
    animationRef.current = requestAnimationFrame(animate);
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [mousePos]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/dashboard?prompt=${encodeURIComponent(query)}`);
    }
  };

  const getUserName = () => {
    if (user?.user_metadata?.name) {
      return user.user_metadata.name.split(' ')[0];
    }
    if (user?.email) {
      return user.email.split('@')[0];
    }
    return 'there';
  };

  return (
    <>
      <ModalProviders />
      <main className="relative min-h-screen overflow-hidden bg-[#0a0a0f]">
        {/* Animated Background */}
        <div 
          className="fixed inset-0 z-0"
          style={{
            background: `
              radial-gradient(circle at 20% 50%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
              radial-gradient(circle at 80% 80%, rgba(236, 72, 153, 0.15) 0%, transparent 50%),
              radial-gradient(circle at 40% 20%, rgba(99, 102, 241, 0.1) 0%, transparent 50%)
            `,
            transform: `translate(${currentPos.x * 20}px, ${currentPos.y * 20}px)`
          }}
        />
        
        {/* Particles - slower speed and more visible */}
        {mounted && (
          <div className="fixed inset-0 overflow-hidden z-[1]">
            {[...Array(50)].map((_, i) => (
              <div
                key={i}
                className="absolute w-1 h-1 bg-purple-500/60 rounded-full"
                style={{
                  width: '4px',
                  height: '4px',
                  left: `${Math.random() * 100}%`,
                  animation: `float ${60 + Math.random() * 40}s linear infinite`,
                  animationDelay: `${Math.random() * 60}s`
                }}
              />
            ))}
          </div>
        )}

        {/* Container */}
        <div className="relative z-10 w-full max-w-6xl mx-auto px-5 min-h-screen flex flex-col">
          {/* Header */}
          <header className="py-8 backdrop-blur-[10px]">
            <div className="flex justify-between items-center gap-8 flex-wrap md:flex-nowrap">
              {/* Logo */}
              <div className="flex items-center gap-4">
                <div className="relative w-14 h-14">
                  <div className="absolute inset-[-15px] bg-purple-500/60 blur-[20px] animate-pulse" />
                  {/* Classic BB Logo */}
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
                    
                    <circle cx="50" cy="50" r="45" fill="none" stroke="url(#purple-gradient)" strokeWidth="4"/>
                    
                    <g>
                      {/* First B (mirrored/backwards) */}
                      <path d="M 45 30 L 45 70 L 35 70 Q 25 70 25 60 Q 25 50 35 50 L 45 50 M 45 50 L 35 50 Q 25 50 25 40 Q 25 30 35 30 L 45 30" 
                            fill="none" stroke="url(#letter-gradient)" strokeWidth="4"
                            strokeLinecap="round" strokeLinejoin="round"/>
                      {/* Second B (normal) */}
                      <path d="M 55 30 L 55 70 L 65 70 Q 75 70 75 60 Q 75 50 65 50 L 55 50 M 55 50 L 65 50 Q 75 50 75 40 Q 75 30 65 30 L 55 30" 
                            fill="none" stroke="url(#letter-gradient)" strokeWidth="4"
                            strokeLinecap="round" strokeLinejoin="round"/>
                    </g>
                    
                    <g opacity="0.8">
                      <path d="M 5 50 L 15 50 L 20 45" fill="none" stroke="#c084fc" strokeWidth="2">
                        <animate attributeName="stroke-dasharray" values="0 100;100 0;0 100" dur="3s" repeatCount="indefinite"/>
                      </path>
                      <path d="M 95 50 L 85 50 L 80 55" fill="none" stroke="#c084fc" strokeWidth="2">
                        <animate attributeName="stroke-dasharray" values="0 100;100 0;0 100" dur="3s" repeatCount="indefinite" begin="1.5s"/>
                      </path>
                      <circle cx="5" cy="50" r="3" fill="#c084fc">
                        <animate attributeName="opacity" values="0.3;1;0.3" dur="2s" repeatCount="indefinite"/>
                      </circle>
                      <circle cx="95" cy="50" r="3" fill="#c084fc">
                        <animate attributeName="opacity" values="0.3;1;0.3" dur="2s" repeatCount="indefinite" begin="1s"/>
                      </circle>
                    </g>
                  </svg>
                </div>
                
                <div className="flex flex-col">
                  <div className="text-[2rem] font-bold flex">
                    <span className="text-white">Bitter</span>
                    <span className="text-purple-500">Bot</span>
                  </div>
                  <div className="text-sm text-gray-400 -mt-1">Distributed Intelligence</div>
                </div>
              </div>

              {/* Sign Up Button */}
              <Link 
                href="/auth" 
                className="bg-gradient-to-r from-purple-600 to-purple-700 text-white px-8 py-3 rounded-full text-sm font-semibold hover:shadow-lg hover:shadow-purple-500/25 hover:-translate-y-0.5 transition-all duration-300"
              >
                Get Started
              </Link>
            </div>
          </header>

          {/* Main Content */}
          <main className="flex-1 flex flex-col justify-center items-center px-5 text-center -mt-[10vh]">
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold mb-2 bg-gradient-to-r from-white to-purple-400 bg-clip-text text-transparent animate-fade-in-down">
              Hey {getUserName()}
            </h1>
            <p className="text-xl md:text-2xl text-gray-400 mb-12 animate-fade-in-up animation-delay-200">
              What would you like to create today?
            </p>
            
            {/* Search Form */}
            <form onSubmit={handleSubmit} className="w-full max-w-2xl mb-8 animate-fade-in animation-delay-400">
              <div className="relative">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask me anything..."
                  className="w-full bg-purple-500/10 border border-purple-500/20 rounded-2xl py-5 px-6 pr-16 text-white outline-none transition-all duration-300 backdrop-blur-[10px] focus:border-purple-500 focus:shadow-[0_0_0_3px_rgba(139,92,246,0.1)] focus:bg-purple-500/15 placeholder:text-white/50"
                  autoFocus
                />
                <button
                  type="submit"
                  className="absolute right-2 top-1/2 -translate-y-1/2 bg-gradient-to-r from-purple-600 to-purple-700 text-white w-12 h-12 rounded-full flex items-center justify-center hover:scale-105 hover:shadow-lg hover:shadow-purple-500/30 transition-all duration-300"
                  aria-label="Submit"
                >
                  <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </button>
              </div>
            </form>
            
            {/* Action Buttons */}
            <div className="flex gap-4 animate-fade-in animation-delay-600 flex-wrap justify-center">
              <Link
                href="/dashboard?mode=deepsearch"
                className="flex items-center gap-3 bg-purple-500/10 border border-purple-500/20 rounded-xl px-8 py-4 text-white font-medium hover:bg-purple-500/20 hover:border-purple-500/40 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-purple-500/20 transition-all duration-300 backdrop-blur-[10px]"
              >
                <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <span>Deep Search</span>
              </Link>
              
              <Link
                href="/dashboard?mode=think"
                className="flex items-center gap-3 bg-purple-500/10 border border-purple-500/20 rounded-xl px-8 py-4 text-white font-medium hover:bg-purple-500/20 hover:border-purple-500/40 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-purple-500/20 transition-all duration-300 backdrop-blur-[10px]"
              >
                <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <span>Deep Think</span>
              </Link>
              
              <Link
                href="/dashboard?mode=create"
                className="flex items-center gap-3 bg-purple-500/10 border border-purple-500/20 rounded-xl px-8 py-4 text-white font-medium hover:bg-purple-500/20 hover:border-purple-500/40 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-purple-500/20 transition-all duration-300 backdrop-blur-[10px]"
              >
                <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
                <span>Create</span>
              </Link>
            </div>
          </main>
        </div>
        
        {/* Trust Badge */}
        <div className="fixed bottom-8 right-8 bg-purple-500/10 border border-purple-500/20 px-4 py-2 rounded-full text-xs text-purple-400 backdrop-blur-[10px] animate-fade-in animation-delay-1000 hidden md:block">
          <span className="mr-2">✨</span>
          Powered by Trust Fund Particles™
        </div>

        {/* Add animation styles */}
        <style jsx>{`
          @keyframes float {
            from {
              transform: translateY(100vh) translateX(0);
              opacity: 0;
            }
            10% {
              opacity: 1;
            }
            90% {
              opacity: 1;
            }
            to {
              transform: translateY(-100px) translateX(100px);
              opacity: 0;
            }
          }
          
          @keyframes fade-in-down {
            from {
              opacity: 0;
              transform: translateY(-30px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
          
          @keyframes fade-in-up {
            from {
              opacity: 0;
              transform: translateY(30px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
          
          @keyframes fade-in {
            from {
              opacity: 0;
            }
            to {
              opacity: 1;
            }
          }
          
          .animate-fade-in-down {
            animation: fade-in-down 0.8s ease-out;
          }
          
          .animate-fade-in-up {
            animation: fade-in-up 0.8s ease-out;
          }
          
          .animate-fade-in {
            animation: fade-in 0.8s ease-out;
          }
          
          .animation-delay-200 {
            animation-delay: 0.2s;
            animation-fill-mode: both;
          }
          
          .animation-delay-400 {
            animation-delay: 0.4s;
            animation-fill-mode: both;
          }
          
          .animation-delay-600 {
            animation-delay: 0.6s;
            animation-fill-mode: both;
          }
          
          .animation-delay-1000 {
            animation-delay: 1s;
            animation-fill-mode: both;
          }
        `}</style>
      </main>
    </>
  );
}