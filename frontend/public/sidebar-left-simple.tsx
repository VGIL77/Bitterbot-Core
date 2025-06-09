

'use client';

import * as React from 'react';
import Link from 'next/link';
import { 
  Bot, 
  MessageSquare, 
  Settings, 
  ChevronLeft,
  ChevronRight,
  MoreHorizontal
} from 'lucide-react';
import { useState } from 'react';
import { cn } from '../lib/utils';

// BitterBot Brain Logo Component
const BitterBotLogo = ({ className = "w-5 h-5" }: { className?: string }) => (
  <svg viewBox="0 0 100 100" className={className}>
    <defs>
      <linearGradient id="circleGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style={{stopColor:"#c084fc"}} />
        <stop offset="50%" style={{stopColor:"#a855f7"}} />
        <stop offset="100%" style={{stopColor:"#7c3aed"}} />
      </linearGradient>
      <linearGradient id="letterGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style={{stopColor:"#e9d5ff"}} />
        <stop offset="50%" style={{stopColor:"#c084fc"}} />
        <stop offset="100%" style={{stopColor:"#a855f7"}} />
      </linearGradient>
    </defs>
    
    {/* Outer circle */}
    <circle cx="50" cy="50" r="45" fill="none" stroke="url(#circleGradient)" strokeWidth="3"/>
    
    {/* Mirrored B (first B - left brain hemisphere) */}
    <path d="M 47 25 L 47 75 L 35 75 Q 23 75 23 63 Q 23 50 35 50 L 47 50 M 47 50 L 35 50 Q 23 50 23 37 Q 23 25 35 25 L 47 25" 
          fill="none" 
          stroke="url(#letterGradient)" 
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"/>
    
    {/* Regular B (second B - right brain hemisphere) */}
    <path d="M 53 25 L 53 75 L 65 75 Q 77 75 77 63 Q 77 50 65 50 L 53 50 M 53 50 L 65 50 Q 77 50 77 37 Q 77 25 65 25 L 53 25" 
          fill="none" 
          stroke="url(#letterGradient)" 
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"/>
    
    {/* Center connection (brain stem) - subtle */}
    <line x1="50" y1="30" x2="50" y2="70" 
          stroke="url(#letterGradient)" 
          strokeWidth="1" 
          opacity="0.3"/>
  </svg>
);

// Mock data for previous chats with dates
const mockChats = [
  { id: 1, title: 'React Performance Optimization', date: new Date('2024-01-15'), preview: 'How to optimize React components...' },
  { id: 2, title: 'Database Design Patterns', date: new Date('2024-01-14'), preview: 'Best practices for database schema...' },
  { id: 3, title: 'API Security Implementation', date: new Date('2024-01-13'), preview: 'Implementing JWT authentication...' },
  { id: 4, title: 'CSS Grid vs Flexbox', date: new Date('2024-01-12'), preview: 'When to use Grid vs Flexbox...' },
  { id: 5, title: 'TypeScript Advanced Types', date: new Date('2024-01-11'), preview: 'Understanding conditional types...' },
  { id: 6, title: 'Docker Container Optimization', date: new Date('2024-01-10'), preview: 'Reducing Docker image size...' },
];

// Mock user data
const mockUser = {
  name: 'Alex Developer',
  email: 'alex@example.com',
  avatar: ''
};

interface SidebarLeftProps {
  isCollapsed?: boolean;
  onToggle?: () => void;
}

export function SidebarLeft({ isCollapsed = false, onToggle }: SidebarLeftProps) {
  const [hoveredChat, setHoveredChat] = useState<number | null>(null);
  const [activeChat, setActiveChat] = useState<number | null>(1);

  // Format date for display
  const formatDate = (date: Date) => {
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Today';
    if (diffDays === 2) return 'Yesterday';
    if (diffDays <= 7) return `${diffDays - 1} days ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  // Group chats by date
  const groupChatsByDate = (chats: typeof mockChats) => {
    const groups: { [key: string]: typeof mockChats } = {};
    
    chats.forEach(chat => {
      const dateKey = formatDate(chat.date);
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(chat);
    });
    
    return groups;
  };

  const chatGroups = groupChatsByDate(mockChats);

  return (
    <div
      style={{ width: isCollapsed ? 60 : 280 }}
      className="h-screen bg-gradient-to-b from-[hsl(262,20%,8%)] to-[hsl(262,25%,6%)] border-r border-[hsl(262,20%,15%)] flex flex-col relative transition-all duration-300"
    >
      {/* Header */}
      <div className="p-4 border-b border-[hsl(262,20%,15%)]">
        <div className="flex items-center justify-between">
          {!isCollapsed && (
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 flex items-center justify-center">
                <BitterBotLogo className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-white font-semibold text-lg">
                  Bitter<span className="text-purple-400">Bot</span>
                </h1>
              </div>
            </div>
          )}
          
          {isCollapsed && (
            <div className="w-8 h-8 flex items-center justify-center">
              <BitterBotLogo className="w-8 h-8" />
            </div>
          )}
          
          <button
            onClick={onToggle}
            className="p-2 rounded-lg hover:bg-[hsl(262,20%,12%)] transition-colors text-gray-400 hover:text-white"
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>
        
        {/* New Task Button */}
        {!isCollapsed && (
          <button className="w-full mt-4 p-3 bg-transparent border border-task-green-500 hover:bg-task-green-500/10 rounded-lg text-task-green-500 hover:text-task-green-400 font-medium flex items-center justify-center transition-all duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-task-green-500/25">
            New Task
          </button>
        )}
        
        {isCollapsed && (
          <button className="w-full mt-4 p-2 bg-transparent border border-task-green-500 hover:bg-task-green-500/10 rounded-lg text-task-green-500 hover:text-task-green-400 transition-all duration-200 hover:scale-[1.02] flex items-center justify-center text-sm font-medium">
            Task
          </button>
        )}
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto">
        {!isCollapsed && (
          <div className="p-4 space-y-4">
            {Object.entries(chatGroups).map(([dateGroup, chats]) => (
              <div key={dateGroup} className="space-y-2">
                <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider px-2">
                  {dateGroup}
                </h3>
                
                <div className="space-y-1">
                  {chats.map((chat) => (
                    <div
                      key={chat.id}
                      className={cn(
                        "group relative p-3 rounded-lg cursor-pointer transition-all duration-200",
                        "hover:bg-[hsl(262,20%,12%)] hover:scale-[1.02]",
                        activeChat === chat.id 
                          ? "bg-gradient-to-r from-purple-600/20 to-purple-700/20 border-l-2 border-purple-500 shadow-lg shadow-purple-500/10" 
                          : "hover:shadow-md"
                      )}
                      onMouseEnter={() => setHoveredChat(chat.id)}
                      onMouseLeave={() => setHoveredChat(null)}
                      onClick={() => setActiveChat(chat.id)}
                    >
                      <div className="flex items-start gap-3">
                        <MessageSquare className={cn(
                          "w-4 h-4 mt-0.5 flex-shrink-0 transition-colors",
                          activeChat === chat.id ? "text-purple-400" : "text-gray-400 group-hover:text-gray-300"
                        )} />
                        <div className="flex-1 min-w-0">
                          <h4 className={cn(
                            "text-sm font-medium truncate transition-colors",
                            activeChat === chat.id ? "text-white" : "text-gray-200 group-hover:text-white"
                          )}>
                            {chat.title}
                          </h4>
                          <p className="text-xs text-gray-400 truncate mt-1">
                            {chat.preview}
                          </p>
                        </div>
                        
                        {hoveredChat === chat.id && (
                          <button
                            className="p-1 rounded hover:bg-[hsl(262,20%,15%)] text-gray-400 hover:text-gray-300"
                            onClick={(e) => {
                              e.stopPropagation();
                              // Handle delete or more options
                            }}
                          >
                            <MoreHorizontal className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
        
        {isCollapsed && (
          <div className="p-2 space-y-2">
            {mockChats.slice(0, 6).map((chat) => (
              <button
                key={chat.id}
                className={cn(
                  "w-full p-2 rounded-lg transition-all duration-200 flex items-center justify-center",
                  activeChat === chat.id 
                    ? "bg-gradient-to-r from-purple-600/20 to-purple-700/20 text-purple-400" 
                    : "hover:bg-[hsl(262,20%,12%)] text-gray-400 hover:text-gray-300"
                )}
                onClick={() => setActiveChat(chat.id)}
              >
                <MessageSquare className="w-4 h-4" />
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Agent Playground */}
      <div className="border-t border-[hsl(262,20%,15%)] p-4">
        {!isCollapsed ? (
          <div>
            <Link href="/agents">
              <div className="p-3 rounded-lg hover:bg-[hsl(262,20%,12%)] transition-all duration-200 hover:scale-[1.02] cursor-pointer group">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-gradient-to-br from-purple-500/20 to-purple-600/20 group-hover:from-purple-500/30 group-hover:to-purple-600/30 transition-all duration-200">
                    <Bot className="w-4 h-4 text-purple-400" />
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-200 group-hover:text-white transition-colors">
                      Agent Playground
                    </h4>
                    <p className="text-xs text-gray-400">
                      Experiment with AI agents
                    </p>
                  </div>
                </div>
              </div>
            </Link>
          </div>
        ) : (
          <div>
            <Link href="/agents">
              <button className="w-full p-2 rounded-lg hover:bg-[hsl(262,20%,12%)] transition-all duration-200 hover:scale-[1.02] text-purple-400 hover:text-purple-300">
                <Bot className="w-4 h-4" />
              </button>
            </Link>
          </div>
        )}
      </div>

      {/* User Account */}
      <div className="border-t border-[hsl(262,20%,15%)] p-4">
        {!isCollapsed ? (
          <div className="flex items-center gap-3 p-3 rounded-lg hover:bg-[hsl(262,20%,12%)] transition-all duration-200 hover:scale-[1.02] cursor-pointer group">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-white font-medium text-sm">
              {mockUser.name.split(' ').map(n => n[0]).join('')}
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-medium text-gray-200 group-hover:text-white transition-colors truncate">
                {mockUser.name}
              </h4>
              <p className="text-xs text-gray-400 truncate">
                {mockUser.email}
              </p>
            </div>
            <Settings className="w-4 h-4 text-gray-400 group-hover:text-gray-300 transition-colors" />
          </div>
        ) : (
          <button className="w-full p-2 rounded-lg hover:bg-[hsl(262,20%,12%)] transition-all duration-200 hover:scale-[1.02] flex items-center justify-center">
            <div className="w-6 h-6 rounded-full bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-white font-medium text-xs">
              {mockUser.name.split(' ').map(n => n[0]).join('')}
            </div>
          </button>
        )}
      </div>
    </div>
  );
}

