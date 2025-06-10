'use client';

import * as React from 'react';
import Link from 'next/link';
import { 
  Bot, 
  MessageSquare, 
  Settings, 
  ChevronLeft,
  ChevronRight,
  MoreHorizontal,
  Trash2,
  Share2,
  Loader2,
  Check,
  X,
  History,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';
import { createClient } from '@/lib/supabase/client';
import { usePathname, useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { useQueryClient } from '@tanstack/react-query';

// Import all the necessary hooks and components from nav-agents
import { ShareModal } from './share-modal';
import { DeleteConfirmationDialog } from '@/components/thread/DeleteConfirmationDialog';
import { useDeleteOperation } from '@/contexts/DeleteOperationContext';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  ThreadWithProject,
  processThreadsWithProjects, 
  useDeleteMultipleThreads, 
  useDeleteThread, 
  useProjects, 
  useThreads,
  threadKeys 
} from '@/hooks/react-query/sidebar/use-sidebar';
import { NavUserWithTeams } from './nav-user-with-teams';
import { BrainBBLogo } from './brain-bb-logo';
import { useIsMobile } from '@/hooks/use-mobile';

interface SidebarLeftNewProps {
  isCollapsed?: boolean;
  onToggle?: () => void;
}

export function SidebarLeftNew({ isCollapsed = false, onToggle }: SidebarLeftNewProps) {
  const [hoveredChat, setHoveredChat] = useState<string | null>(null);
  const [activeChat, setActiveChat] = useState<string | null>(null);
  const [selectedThreads, setSelectedThreads] = useState<Set<string>>(new Set());
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [threadToDelete, setThreadToDelete] = useState<{ id: string; name: string } | null>(null);
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [shareThreadId, setShareThreadId] = useState<string | null>(null);
  const [deleteProgress, setDeleteProgress] = useState(0);
  const [totalToDelete, setTotalToDelete] = useState(0);
  const [user, setUser] = useState<{
    name: string;
    email: string;
    avatar: string;
  }>({
    name: 'Loading...',
    email: 'loading@example.com',
    avatar: '',
  });

  // Hooks from nav-agents
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();
  const isMobile = useIsMobile();
  const { performDelete } = useDeleteOperation();
  const isPerformingActionRef = useRef(false);
  const isNavigatingRef = useRef(false);

  // Get threads and projects data
  const { data: threads = [], isLoading: threadsLoading } = useThreads();
  const { data: projects = [], isLoading: projectsLoading } = useProjects();
  const { mutate: deleteThreadMutation } = useDeleteThread();
  const { mutate: deleteMultipleThreadsMutation } = useDeleteMultipleThreads();

  // Process threads with projects
  const combinedThreads = processThreadsWithProjects(threads, projects);

  // Set active chat based on pathname
  useEffect(() => {
    if (pathname) {
      const threadId = pathname.split('/').find(segment => 
        segment && combinedThreads.some(t => t.threadId === segment)
      );
      if (threadId) {
        setActiveChat(threadId);
      }
    }
  }, [pathname, combinedThreads]);

  // Fetch user data
  useEffect(() => {
    const fetchUserData = async () => {
      const supabase = createClient();
      const { data } = await supabase.auth.getUser();

      if (data.user) {
        setUser({
          name:
            data.user.user_metadata?.name ||
            data.user.email?.split('@')[0] ||
            'User',
          email: data.user.email || '',
          avatar: data.user.user_metadata?.avatar_url || '',
        });
      }
    };

    fetchUserData();
  }, []);

  // Handle keyboard shortcuts (CMD+B) for consistency
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key === 'b') {
        event.preventDefault();
        if (onToggle) onToggle();

        // Broadcast a custom event to notify other components
        window.dispatchEvent(
          new CustomEvent('sidebar-left-toggled', {
            detail: { expanded: !isCollapsed },
          }),
        );
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isCollapsed, onToggle]);

  // Format date for display
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) return 'Today';
    if (diffDays === 2) return 'Yesterday';
    if (diffDays <= 7) return `${diffDays - 1} days ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  // Group threads by date
  const groupThreadsByDate = (threads: ThreadWithProject[]) => {
    const groups: { [key: string]: ThreadWithProject[] } = {};
    
    threads.forEach(thread => {
      const dateKey = formatDate(thread.updatedAt);
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(thread);
    });
    
    return groups;
  };

  const threadGroups = groupThreadsByDate(combinedThreads);

  // Handle thread deletion
  const handleDeleteThread = (threadId: string, threadName: string) => {
    if (isPerformingActionRef.current) return;
    setThreadToDelete({ id: threadId, name: threadName });
    setIsDeleteDialogOpen(true);
  };

  const handleDeleteMultiple = () => {
    if (selectedThreads.size === 0 || isPerformingActionRef.current) return;
    
    // Create a descriptive name for multiple threads
    const threadNames = Array.from(selectedThreads)
      .slice(0, 3)
      .map(id => {
        const thread = combinedThreads.find(t => t.threadId === id);
        return thread?.name || 'Untitled';
      })
      .join(', ');

    setThreadToDelete({
      id: "multiple",
      name: selectedThreads.size > 3
        ? `${selectedThreads.size} conversations`
        : threadNames
    });

    setTotalToDelete(selectedThreads.size);
    setDeleteProgress(0);
    setIsDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!threadToDelete || isPerformingActionRef.current) return;

    // Mark action in progress
    isPerformingActionRef.current = true;

    // Close dialog first for immediate feedback
    setIsDeleteDialogOpen(false);

    // Check if it's a single thread or multiple threads
    if (threadToDelete.id !== "multiple") {
      // Single thread deletion logic (same as in nav-agents)
      const threadId = threadToDelete.id;
      const isActive = pathname?.includes(threadId);
      const thread = combinedThreads.find(t => t.threadId === threadId);
      const project = projects.find(p => p.id === thread?.projectId);
      const sandboxId = project?.sandbox?.id;

      await performDelete(
        threadId,
        isActive,
        async () => {
          deleteThreadMutation(
            { threadId, sandboxId },
            {
              onSuccess: () => {
                queryClient.invalidateQueries({ queryKey: threadKeys.lists() });
                toast.success('Conversation deleted successfully');
              },
              onSettled: () => {
                setThreadToDelete(null);
                isPerformingActionRef.current = false;
              }
            }
          );
        },
        () => {
          setThreadToDelete(null);
          isPerformingActionRef.current = false;
        },
      );
    } else {
      // Multi-thread deletion logic (same as in nav-agents)
      const threadIdsToDelete = Array.from(selectedThreads);
      const isActiveThreadIncluded = threadIdsToDelete.some(id => pathname?.includes(id));

      toast.info(`Deleting ${threadIdsToDelete.length} conversations...`);

      try {
        if (isActiveThreadIncluded) {
          isNavigatingRef.current = true;
          document.body.style.pointerEvents = 'none';
          router.push('/dashboard');
          await new Promise(resolve => setTimeout(resolve, 100));
        }

        deleteMultipleThreadsMutation(
          {
            threadIds: threadIdsToDelete,
            threadSandboxMap: Object.fromEntries(
              threadIdsToDelete.map(threadId => {
                const thread = combinedThreads.find(t => t.threadId === threadId);
                const project = projects.find(p => p.id === thread?.projectId);
                return [threadId, project?.sandbox?.id || ''];
              }).filter(([, sandboxId]) => sandboxId)
            ),
            onProgress: (current, total) => {
              setDeleteProgress(current);
              setTotalToDelete(total);
            }
          },
          {
            onSuccess: () => {
              queryClient.invalidateQueries({ queryKey: threadKeys.lists() });
              toast.success(`${threadIdsToDelete.length} conversations deleted successfully`);
              setSelectedThreads(new Set());
            },
            onSettled: () => {
              setThreadToDelete(null);
              setDeleteProgress(0);
              setTotalToDelete(0);
              isPerformingActionRef.current = false;
              isNavigatingRef.current = false;
              document.body.style.pointerEvents = 'auto';
            }
          }
        );
      } catch (error) {
        isPerformingActionRef.current = false;
        isNavigatingRef.current = false;
        document.body.style.pointerEvents = 'auto';
      }
    }
  };

  return (
    <>
      <div
        style={{ width: isCollapsed ? 60 : 320 }}
        className="h-screen bg-gradient-to-b from-[hsl(262,20%,8%)] to-[hsl(262,25%,6%)] border-r border-[hsl(262,20%,15%)] flex flex-col relative transition-all duration-300"
      >
        {/* Header */}
        <div className="p-4 border-b border-[hsl(262,20%,15%)]">
          <div className="flex items-center justify-between">
            {!isCollapsed && (
              <Link href="/dashboard" className="flex items-center gap-3">
                <div className="w-8 h-8 flex items-center justify-center">
                  <BrainBBLogo className="w-8 h-8" />
                </div>
                <div>
                  <h1 className="text-white font-semibold text-lg">
                    Bitter<span className="text-purple-400">Bot</span>
                  </h1>
                </div>
              </Link>
            )}
            
            {isCollapsed && (
              <Link href="/dashboard" className="w-8 h-8 flex items-center justify-center">
                <BrainBBLogo className="w-8 h-8" />
              </Link>
            )}
            
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={onToggle}
                  className="p-2 rounded-lg hover:bg-[hsl(262,20%,12%)] transition-colors text-gray-400 hover:text-white"
                >
                  {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
                </button>
              </TooltipTrigger>
              <TooltipContent>Toggle sidebar (CMD+B)</TooltipContent>
            </Tooltip>
          </div>
          
          {/* New Conversation Button */}
          {!isCollapsed && (
            <Link href="/dashboard">
              <button className="w-full mt-4 p-3 bg-transparent border border-task-green-500 hover:bg-task-green-500/10 rounded-lg text-task-green-500 hover:text-task-green-400 font-medium flex items-center justify-center transition-all duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-task-green-500/25">
                New Conversation
              </button>
            </Link>
          )}
          
          {isCollapsed && (
            <Link href="/dashboard">
              <button className="w-full mt-4 p-2 bg-transparent border border-task-green-500 hover:bg-task-green-500/10 rounded-lg text-task-green-500 hover:text-task-green-400 transition-all duration-200 hover:scale-[1.02] flex items-center justify-center text-sm font-medium">
                New
              </button>
            </Link>
          )}
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto scrollbar-hide">
          {threadsLoading || projectsLoading ? (
            <div className="flex items-center justify-center p-8">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
            </div>
          ) : (
            <>
              {/* Selection controls */}
              {selectedThreads.size > 0 && !isCollapsed && (
                <div className="p-4 border-b border-[hsl(262,20%,15%)] flex items-center justify-between">
                  <span className="text-sm text-gray-400">
                    {selectedThreads.size} selected
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setSelectedThreads(new Set())}
                      className="text-xs text-gray-400 hover:text-gray-300"
                    >
                      Clear
                    </button>
                    <button
                      onClick={handleDeleteMultiple}
                      className="text-xs text-red-400 hover:text-red-300"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              )}

              {!isCollapsed && (
                <div className="p-4 space-y-4">
                  {Object.entries(threadGroups).map(([dateGroup, threads]) => (
                    <div key={dateGroup} className="space-y-2">
                      <h3 className="text-xs font-medium text-gray-400 uppercase tracking-wider px-2">
                        {dateGroup}
                      </h3>
                      
                      <div className="space-y-1">
                        {threads.map((thread) => (
                          <div
                            key={thread.threadId}
                            className={cn(
                              "group relative p-3 rounded-lg cursor-pointer transition-all duration-200",
                              "hover:bg-[hsl(262,20%,12%)] hover:scale-[1.02]",
                              activeChat === thread.threadId 
                                ? "bg-gradient-to-r from-purple-600/20 to-purple-700/20 border-l-2 border-purple-500 shadow-lg shadow-purple-500/10" 
                                : "hover:shadow-md"
                            )}
                            onMouseEnter={() => setHoveredChat(thread.threadId)}
                            onMouseLeave={() => setHoveredChat(null)}
                            onClick={() => {
                              if (selectedThreads.size > 0) {
                                // In selection mode, toggle selection
                                const newSelected = new Set(selectedThreads);
                                if (newSelected.has(thread.threadId)) {
                                  newSelected.delete(thread.threadId);
                                } else {
                                  newSelected.add(thread.threadId);
                                }
                                setSelectedThreads(newSelected);
                              } else {
                                // Normal navigation
                                router.push(`/projects/${thread.projectId}/thread/${thread.threadId}`);
                              }
                            }}
                          >
                            <div className="flex items-start gap-3">
                              {selectedThreads.size > 0 && (
                                <Checkbox
                                  checked={selectedThreads.has(thread.threadId)}
                                  onCheckedChange={(checked) => {
                                    const newSelected = new Set(selectedThreads);
                                    if (checked) {
                                      newSelected.add(thread.threadId);
                                    } else {
                                      newSelected.delete(thread.threadId);
                                    }
                                    setSelectedThreads(newSelected);
                                  }}
                                  onClick={(e) => e.stopPropagation()}
                                  className="mt-0.5"
                                />
                              )}
                              <MessageSquare className={cn(
                                "w-4 h-4 mt-0.5 flex-shrink-0 transition-colors",
                                activeChat === thread.threadId ? "text-purple-400" : "text-gray-400 group-hover:text-gray-300"
                              )} />
                              <div className="flex-1 min-w-0">
                                <h4 className={cn(
                                  "text-sm font-medium truncate transition-colors",
                                  activeChat === thread.threadId ? "text-white" : "text-gray-200 group-hover:text-white"
                                )}>
                                  {thread.name}
                                </h4>
                                {thread.preview && (
                                  <p className="text-xs text-gray-400 truncate mt-1">
                                    {thread.preview}
                                  </p>
                                )}
                              </div>
                              
                              {hoveredChat === thread.threadId && selectedThreads.size === 0 && (
                                <DropdownMenu>
                                  <DropdownMenuTrigger asChild>
                                    <button
                                      className="p-1 rounded hover:bg-[hsl(262,20%,15%)] text-gray-400 hover:text-gray-300"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                      }}
                                    >
                                      <MoreHorizontal className="w-3 h-3" />
                                    </button>
                                  </DropdownMenuTrigger>
                                  <DropdownMenuContent>
                                    <DropdownMenuItem
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setShareThreadId(thread.threadId);
                                        setIsShareModalOpen(true);
                                      }}
                                    >
                                      <Share2 className="mr-2 h-4 w-4" />
                                      Share
                                    </DropdownMenuItem>
                                    <DropdownMenuSeparator />
                                    <DropdownMenuItem
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleDeleteThread(thread.threadId, thread.name);
                                      }}
                                      className="text-red-600"
                                    >
                                      <Trash2 className="mr-2 h-4 w-4" />
                                      Delete
                                    </DropdownMenuItem>
                                  </DropdownMenuContent>
                                </DropdownMenu>
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
                  {combinedThreads.slice(0, 10).map((thread) => (
                    <Tooltip key={thread.threadId}>
                      <TooltipTrigger asChild>
                        <button
                          className={cn(
                            "w-full p-2 rounded-lg transition-all duration-200 flex items-center justify-center",
                            activeChat === thread.threadId 
                              ? "bg-gradient-to-r from-purple-600/20 to-purple-700/20 text-purple-400" 
                              : "hover:bg-[hsl(262,20%,12%)] text-gray-400 hover:text-gray-300"
                          )}
                          onClick={() => router.push(`/projects/${thread.projectId}/thread/${thread.threadId}`)}
                        >
                          <MessageSquare className="w-4 h-4" />
                        </button>
                      </TooltipTrigger>
                      <TooltipContent side="right">
                        {thread.name}
                      </TooltipContent>
                    </Tooltip>
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        {/* Agent Playground */}
        <div className="border-t border-[hsl(262,20%,15%)] p-4">
          {!isCollapsed ? (
            <div>
              <Link href="/agents">
                <div className={cn(
                  "p-3 rounded-lg hover:bg-[hsl(262,20%,12%)] transition-all duration-200 hover:scale-[1.02] cursor-pointer group",
                  pathname === '/agents' && "bg-gradient-to-r from-purple-600/20 to-purple-700/20"
                )}>
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
              <Tooltip>
                <TooltipTrigger asChild>
                  <Link href="/agents">
                    <button className={cn(
                      "w-full p-2 rounded-lg hover:bg-[hsl(262,20%,12%)] transition-all duration-200 hover:scale-[1.02] text-purple-400 hover:text-purple-300",
                      pathname === '/agents' && "bg-gradient-to-r from-purple-600/20 to-purple-700/20"
                    )}>
                      <Bot className="w-4 h-4" />
                    </button>
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="right">
                  Agent Playground
                </TooltipContent>
              </Tooltip>
            </div>
          )}
        </div>

        {/* User Account */}
        <div className="border-t border-[hsl(262,20%,15%)] p-4">
          <NavUserWithTeams user={user} />
        </div>
      </div>

      {/* Modals */}
      <ShareModal 
        isOpen={isShareModalOpen} 
        onClose={() => {
          setIsShareModalOpen(false);
          setShareThreadId(null);
        }} 
        threadId={shareThreadId}
      />
      
      <DeleteConfirmationDialog
        isOpen={isDeleteDialogOpen}
        onClose={() => setIsDeleteDialogOpen(false)}
        onConfirm={confirmDelete}
        threadName={threadToDelete?.name || ''}
        isDeleting={false}
      />
    </>
  );
}