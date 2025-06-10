'use client';

import { useEffect, useState, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
  ArrowUpRight,
  Link as LinkIcon,
  MoreHorizontal,
  Trash2,
  MessagesSquare,
  Loader2,
  Share2,
  X,
  Check,
  History,
  ChevronDown,
  ChevronUp
} from "lucide-react"
import { toast } from "sonner"
import { usePathname, useRouter } from "next/navigation"

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from "@/components/ui/tooltip"
import Link from "next/link"
import { ShareModal } from "./share-modal"
import { DeleteConfirmationDialog } from "@/components/thread/DeleteConfirmationDialog"
import { useDeleteOperation } from '@/contexts/DeleteOperationContext'
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { ThreadWithProject } from '@/hooks/react-query/sidebar/use-sidebar';
import { processThreadsWithProjects, useDeleteMultipleThreads, useDeleteThread, useProjects, useThreads } from '@/hooks/react-query/sidebar/use-sidebar';
import { cn } from '@/lib/utils';
import { threadKeys } from '@/hooks/react-query/sidebar/use-sidebar';

interface ThreadGroup {
  label: string;
  threads: ThreadWithProject[];
}

export function NavAgentsStyled() {
  const { data: threads = [], isLoading: threadsLoading } = useThreads();
  const { data: projects = [], isLoading: projectsLoading } = useProjects();
  const pathname = usePathname();
  const router = useRouter();
  const queryClient = useQueryClient();
  const { state: sidebarState } = useSidebar();
  const { performDelete } = useDeleteOperation();
  const { mutate: deleteThreadMutation } = useDeleteThread();
  const { mutate: deleteMultipleThreadsMutation } = useDeleteMultipleThreads();

  const [hoveredThread, setHoveredThread] = useState<string | null>(null);
  const [selectedThreads, setSelectedThreads] = useState<Set<string>>(new Set());
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [threadToDelete, setThreadToDelete] = useState<{ id: string; name: string } | null>(null);
  const [deleteProgress, setDeleteProgress] = useState(0);
  const [totalToDelete, setTotalToDelete] = useState(0);
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);
  const [shareThreadId, setShareThreadId] = useState<string | null>(null);
  const [isMoreOpen, setIsMoreOpen] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set(['Today', 'Yesterday']));
  const [loadingThreadId, setLoadingThreadId] = useState<string | null>(null);

  const isPerformingActionRef = useRef(false);
  const isNavigatingRef = useRef(false);

  const isLoading = threadsLoading || projectsLoading;
  const combinedThreads = processThreadsWithProjects(threads, projects);

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
  const groupThreadsByDate = (threads: ThreadWithProject[]): ThreadGroup[] => {
    const groups: { [key: string]: ThreadWithProject[] } = {};
    
    threads.forEach(thread => {
      const dateKey = formatDate(thread.updatedAt);
      if (!groups[dateKey]) {
        groups[dateKey] = [];
      }
      groups[dateKey].push(thread);
    });
    
    // Convert to array and maintain order
    return Object.entries(groups).map(([label, threads]) => ({
      label,
      threads
    }));
  };

  const threadGroups = groupThreadsByDate(combinedThreads);

  // Handle thread navigation
  const handleThreadClick = (e: React.MouseEvent, threadId: string, url: string) => {
    if (selectedThreads.size > 0) {
      e.preventDefault();
      const newSelected = new Set(selectedThreads);
      if (newSelected.has(threadId)) {
        newSelected.delete(threadId);
      } else {
        newSelected.add(threadId);
      }
      setSelectedThreads(newSelected);
      return;
    }

    if (loadingThreadId === threadId || isNavigatingRef.current) {
      e.preventDefault();
      return;
    }

    setLoadingThreadId(threadId);
  };

  // Handle thread deletion
  const handleDeleteThread = (threadId: string, threadName: string) => {
    if (isPerformingActionRef.current) return;
    setThreadToDelete({ id: threadId, name: threadName });
    setIsDeleteDialogOpen(true);
  };

  const handleDeleteMultiple = () => {
    if (selectedThreads.size === 0 || isPerformingActionRef.current) return;
    
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

    isPerformingActionRef.current = true;
    setIsDeleteDialogOpen(false);

    if (threadToDelete.id !== "multiple") {
      // Single thread deletion
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
      // Multi-thread deletion
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

  const toggleGroup = (groupLabel: string) => {
    const newExpanded = new Set(expandedGroups);
    if (newExpanded.has(groupLabel)) {
      newExpanded.delete(groupLabel);
    } else {
      newExpanded.add(groupLabel);
    }
    setExpandedGroups(newExpanded);
  };

  return (
    <>
      <SidebarGroup>
        <SidebarGroupLabel className="text-xs font-medium text-gray-400 uppercase tracking-wider px-2 mb-2">
          Conversations
          {selectedThreads.size > 0 && (
            <div className="float-right flex items-center gap-2">
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
                Delete ({selectedThreads.size})
              </button>
            </div>
          )}
        </SidebarGroupLabel>

        <SidebarMenu className="space-y-4">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, index) => (
              <SidebarMenuItem key={`skeleton-${index}`}>
                <SidebarMenuButton className="animate-pulse">
                  <div className="h-4 w-4 bg-gray-700 rounded"></div>
                  <div className="h-3 bg-gray-700 rounded w-3/4"></div>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))
          ) : threadGroups.length > 0 ? (
            threadGroups.map((group) => (
              <div key={group.label} className="space-y-1">
                <button
                  onClick={() => toggleGroup(group.label)}
                  className="w-full flex items-center justify-between px-2 py-1 text-xs font-medium text-gray-400 hover:text-gray-300 transition-colors"
                >
                  <span>{group.label}</span>
                  {expandedGroups.has(group.label) ? (
                    <ChevronUp className="h-3 w-3" />
                  ) : (
                    <ChevronDown className="h-3 w-3" />
                  )}
                </button>
                
                {expandedGroups.has(group.label) && (
                  <div className="space-y-1">
                    {group.threads.map((thread) => {
                      const isActive = pathname?.includes(thread.threadId) || false;
                      const isThreadLoading = loadingThreadId === thread.threadId;
                      const isSelected = selectedThreads.has(thread.threadId);

                      return (
                        <SidebarMenuItem key={thread.threadId} className="group">
                          <div
                            className={cn(
                              "relative rounded-lg transition-all duration-200",
                              "hover:bg-[hsl(262,20%,12%)] hover:scale-[1.02]",
                              isActive 
                                ? "bg-gradient-to-r from-purple-600/20 to-purple-700/20 border-l-2 border-purple-500 shadow-lg shadow-purple-500/10" 
                                : "hover:shadow-md"
                            )}
                            onMouseEnter={() => setHoveredThread(thread.threadId)}
                            onMouseLeave={() => setHoveredThread(null)}
                          >
                            <SidebarMenuButton
                              asChild
                              className={cn(
                                "w-full px-3 py-2 justify-start",
                                isActive ? "text-white" : "text-gray-400 hover:text-white"
                              )}
                            >
                              <Link
                                href={thread.url}
                                onClick={(e) => handleThreadClick(e, thread.threadId, thread.url)}
                              >
                                <div className="flex items-center gap-3 w-full">
                                  {selectedThreads.size > 0 && (
                                    <Checkbox
                                      checked={isSelected}
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
                                      className="h-4 w-4"
                                    />
                                  )}
                                  
                                  {isThreadLoading ? (
                                    <Loader2 className="h-4 w-4 animate-spin flex-shrink-0" />
                                  ) : (
                                    <MessagesSquare className={cn(
                                      "h-4 w-4 flex-shrink-0 transition-colors",
                                      isActive ? "text-purple-400" : "text-gray-400 group-hover:text-gray-300"
                                    )} />
                                  )}
                                  
                                  <div className="flex-1 min-w-0 text-left">
                                    <div className={cn(
                                      "text-sm font-medium truncate transition-colors",
                                      isActive ? "text-white" : "text-gray-200 group-hover:text-white"
                                    )}>
                                      {thread.name}
                                    </div>
                                  </div>
                                </div>
                              </Link>
                            </SidebarMenuButton>
                            
                            {hoveredThread === thread.threadId && selectedThreads.size === 0 && sidebarState !== 'collapsed' && (
                              <SidebarMenuAction showOnHover={false}>
                                <DropdownMenu>
                                  <DropdownMenuTrigger asChild>
                                    <button
                                      className="p-1 rounded hover:bg-[hsl(262,20%,15%)] text-gray-400 hover:text-gray-300"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                      }}
                                    >
                                      <MoreHorizontal className="h-3 w-3" />
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
                              </SidebarMenuAction>
                            )}
                          </div>
                        </SidebarMenuItem>
                      );
                    })}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="px-4 py-8 text-center">
              <p className="text-sm text-gray-400">No conversations yet</p>
              <Link href="/dashboard">
                <Button variant="ghost" size="sm" className="mt-2 text-purple-400 hover:text-purple-300">
                  Start a new conversation
                </Button>
              </Link>
            </div>
          )}
        </SidebarMenu>
      </SidebarGroup>

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