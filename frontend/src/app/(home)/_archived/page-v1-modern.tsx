'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ModalProviders } from '@/providers/modal-providers';

export default function Home() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <>
      <ModalProviders />
      <main className="relative min-h-screen overflow-hidden bg-[#0a0a0f]">
        {/* Animated Background */}
        <div className="fixed inset-0 z-0">
          <div 
            className="absolute inset-0"
            style={{
              background: `
                radial-gradient(circle at 20% 50%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 80% 80%, rgba(236, 72, 153, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 40% 20%, rgba(99, 102, 241, 0.1) 0%, transparent 50%)
              `
            }}
          />
          {/* Particles */}
          {mounted && (
            <div className="absolute inset-0 overflow-hidden">
              {[...Array(50)].map((_, i) => (
                <div
                  key={i}
                  className="absolute w-1 h-1 bg-purple-500/60 rounded-full animate-float"
                  style={{
                    left: `${Math.random() * 100}%`,
                    animationDelay: `${Math.random() * 20}s`,
                    animationDuration: `${20 + Math.random() * 10}s`
                  }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Content */}
        <div className="relative z-10">
          {/* Header */}
          <header className="backdrop-blur-xl bg-gray-900/80 border-b border-purple-500/20">
            <div className="container mx-auto px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                {/* Logo */}
                <div className="relative w-12 h-12">
                  <div className="absolute inset-[-10px] bg-purple-500/60 blur-2xl animate-pulse" />
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
                      <path d="M 25 30 L 25 70 L 35 70 Q 45 70 45 60 Q 45 50 35 50 L 25 50 M 25 50 L 35 50 Q 45 50 45 40 Q 45 30 35 30 L 25 30" 
                            fill="none" stroke="url(#letter-gradient)" strokeWidth="4"
                            strokeLinecap="round" strokeLinejoin="round"/>
                      <path d="M 55 30 L 55 70 L 65 70 Q 75 70 75 60 Q 75 50 65 50 L 55 50 M 55 50 L 65 50 Q 75 50 75 40 Q 75 30 65 30 L 55 30" 
                            fill="none" stroke="url(#letter-gradient)" strokeWidth="4"
                            strokeLinecap="round" strokeLinejoin="round"/>
                    </g>
                  </svg>
                </div>
                
                {/* Brand */}
                <div>
                  <h1 className="text-2xl font-bold">
                    <span className="text-white">Bitter</span>
                    <span className="text-purple-500">Bot</span>
                  </h1>
                  <p className="text-sm text-gray-400">Decentralized Intelligence</p>
                </div>
              </div>

              {/* Navigation */}
              <nav className="hidden md:flex items-center gap-8">
                <Link href="/dashboard" className="text-gray-300 hover:text-purple-400 transition-colors">
                  Dashboard
                </Link>
                <Link href="/agents" className="text-gray-300 hover:text-purple-400 transition-colors">
                  Agents
                </Link>
                <Link href="/marketplace" className="text-gray-300 hover:text-purple-400 transition-colors">
                  Marketplace
                </Link>
                <Link 
                  href="/auth" 
                  className="px-6 py-2 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-full hover:shadow-lg hover:shadow-purple-500/25 transition-all"
                >
                  Get Started
                </Link>
              </nav>
            </div>
          </header>

          {/* Hero Section */}
          <section className="container mx-auto px-6 py-20">
            <div className="max-w-4xl mx-auto text-center">
              <h2 className="text-5xl md:text-7xl font-bold mb-8">
                <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                  Decentralized AI
                </span>
                <br />
                <span className="text-white">For Everyone</span>
              </h2>
              
              <p className="text-xl text-gray-300 mb-12 max-w-2xl mx-auto">
                BitterBot brings the power of distributed intelligence to your fingertips. 
                Build, deploy, and share AI agents across a global P2P network.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link 
                  href="/auth"
                  className="px-8 py-4 bg-gradient-to-r from-purple-600 to-purple-700 text-white rounded-full text-lg font-medium hover:shadow-xl hover:shadow-purple-500/25 transition-all"
                >
                  Start Building
                </Link>
                <Link 
                  href="/dashboard"
                  className="px-8 py-4 bg-purple-500/10 border border-purple-500/30 text-purple-300 rounded-full text-lg font-medium hover:bg-purple-500/20 transition-all"
                >
                  Explore Dashboard
                </Link>
              </div>
            </div>
          </section>

          {/* Features Grid */}
          <section className="container mx-auto px-6 py-20">
            <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              {/* Feature 1 */}
              <div className="backdrop-blur-sm bg-purple-500/5 border border-purple-500/20 rounded-2xl p-8 hover:bg-purple-500/10 transition-all">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg mb-6 flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Federated Learning</h3>
                <p className="text-gray-400">
                  Train models across distributed nodes while preserving privacy and data sovereignty
                </p>
              </div>

              {/* Feature 2 */}
              <div className="backdrop-blur-sm bg-purple-500/5 border border-purple-500/20 rounded-2xl p-8 hover:bg-purple-500/10 transition-all">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg mb-6 flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">Dream Engine</h3>
                <p className="text-gray-400">
                  Autonomous curiosity algorithms that enable emergent behaviors and continuous learning
                </p>
              </div>

              {/* Feature 3 */}
              <div className="backdrop-blur-sm bg-purple-500/5 border border-purple-500/20 rounded-2xl p-8 hover:bg-purple-500/10 transition-all">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg mb-6 flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">P2P Network</h3>
                <p className="text-gray-400">
                  Join a global network of AI nodes sharing knowledge and computational resources
                </p>
              </div>
            </div>
          </section>

          {/* CTA Section */}
          <section className="container mx-auto px-6 py-20">
            <div className="backdrop-blur-xl bg-gradient-to-r from-purple-900/20 to-pink-900/20 border border-purple-500/20 rounded-3xl p-12 text-center">
              <h2 className="text-4xl font-bold text-white mb-6">
                Ready to Join the Revolution?
              </h2>
              <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
                BitterBot is more than an AI platform - it&apos;s a movement towards truly decentralized intelligence.
              </p>
              <Link 
                href="/auth"
                className="inline-block px-8 py-4 bg-white text-purple-900 rounded-full text-lg font-medium hover:shadow-xl hover:shadow-white/25 transition-all"
              >
                Get Started Free
              </Link>
            </div>
          </section>

          {/* Footer */}
          <footer className="border-t border-purple-500/20 backdrop-blur-sm bg-gray-900/50">
            <div className="container mx-auto px-6 py-12">
              <div className="flex flex-col md:flex-row justify-between items-center">
                <div className="flex items-center gap-2 mb-4 md:mb-0">
                  <span className="text-white font-semibold">Bitter</span>
                  <span className="text-purple-500 font-semibold">Bot</span>
                  <span className="text-gray-400 ml-2">© 2025</span>
                </div>
                <div className="flex gap-6">
                  <Link href="/legal" className="text-gray-400 hover:text-purple-400 transition-colors">
                    Legal
                  </Link>
                  <a href="https://github.com/bitterbot" className="text-gray-400 hover:text-purple-400 transition-colors">
                    GitHub
                  </a>
                  <a href="https://twitter.com/bitterbot" className="text-gray-400 hover:text-purple-400 transition-colors">
                    Twitter
                  </a>
                </div>
              </div>
            </div>
          </footer>
        </div>

        {/* Add animation styles */}
        <style jsx>{`
          @keyframes float {
            from {
              transform: translateY(100vh) translateX(0);
            }
            to {
              transform: translateY(-100px) translateX(100px);
            }
          }
        `}</style>
      </main>
    </>
  );
}