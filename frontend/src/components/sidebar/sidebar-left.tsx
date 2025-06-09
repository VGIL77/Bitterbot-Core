'use client';

import * as React from 'react';
import Link from 'next/link';
import { Bot, Menu, MessageSquare, Plus } from 'lucide-react';

import { NavAgentsStyled } from '@/components/sidebar/nav-agents-styled';
import { NavUserWithTeams } from '@/components/sidebar/nav-user-with-teams';
import { BrainBBLogo } from '@/components/sidebar/brain-bb-logo';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarTrigger,
  useSidebar,
} from '@/components/ui/sidebar';
import { useEffect, useState } from 'react';
import { createClient } from '@/lib/supabase/client';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { useIsMobile } from '@/hooks/use-mobile';
import { cn } from '@/lib/utils';
import { usePathname } from 'next/navigation';

export function SidebarLeft({
  ...props
}: React.ComponentProps<typeof Sidebar>) {
  const { state, setOpen, setOpenMobile } = useSidebar();
  const isMobile = useIsMobile();
  const [user, setUser] = useState<{
    name: string;
    email: string;
    avatar: string;
  }>({
    name: 'Loading...',
    email: 'loading@example.com',
    avatar: '',
  });

  const pathname = usePathname();

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
        // We\'ll handle this in the parent page component
        // to ensure proper coordination between panels
        setOpen(!state.startsWith('expanded'));

        // Broadcast a custom event to notify other components
        window.dispatchEvent(
          new CustomEvent('sidebar-left-toggled', {
            detail: { expanded: !state.startsWith('expanded') },
          }),
        );
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [state, setOpen]);

  return (
    <Sidebar
      collapsible="icon"
      className="border-r-0 bg-gradient-to-b from-[hsl(262,20%,8%)] to-[hsl(262,25%,6%)] border-r border-[hsl(262,20%,15%)]"
      style={{
        '--sidebar-background': 'transparent',
        '--sidebar-foreground': 'hsl(0 0% 100%)',
        '--sidebar-primary': 'hsl(267 84% 81%)',
        '--sidebar-primary-foreground': 'hsl(0 0% 100%)',
        '--sidebar-accent': 'hsl(262 20% 12%)',
        '--sidebar-accent-foreground': 'hsl(0 0% 100%)',
        '--sidebar-border': 'hsl(262 20% 15%)',
      } as React.CSSProperties}
      {...props}
    >
      <SidebarHeader className="px-2 py-2 border-b border-[hsl(262,20%,15%)]">
        <div className="flex h-[40px] items-center px-1 relative">
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="w-8 h-8">
              <BrainBBLogo className="w-full h-full" />
            </div>
            {state !== 'collapsed' && (
              <div className="ml-2 transition-all duration-200 ease-in-out whitespace-nowrap">
                <span className="font-semibold">
                  <span className="text-white">Bitter</span>
                  <span className="text-purple-400">Bot</span>
                </span>
              </div>
            )}
          </Link>
          <div className="ml-auto flex items-center gap-2">
            {state !== 'collapsed' && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <SidebarTrigger className="h-8 w-8 text-gray-400 hover:text-white hover:bg-[hsl(262,20%,12%)]" />
                </TooltipTrigger>
                <TooltipContent>Toggle sidebar (CMD+B)</TooltipContent>
              </Tooltip>
            )}
            {isMobile && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => setOpenMobile(true)}
                    className="h-8 w-8 flex items-center justify-center rounded-md hover:bg-[hsl(262,20%,12%)] text-gray-400 hover:text-white"
                  >
                    <Menu className="h-4 w-4" />
                  </button>
                </TooltipTrigger>
                <TooltipContent>Open menu</TooltipContent>
              </Tooltip>
            )}
          </div>
        </div>
        
        {/* New Conversation Button */}
        <div className="px-2 pt-2">
          <Link href="/dashboard">
            <SidebarMenuButton 
              className={cn(
                "w-full justify-center gap-2 font-medium",
                "bg-transparent border border-task-green-500",
                "text-task-green-500 hover:text-task-green-400",
                "hover:bg-task-green-500/10",
                "transition-all duration-200 hover:scale-[1.02]",
                "hover:shadow-lg hover:shadow-task-green-500/25"
              )}
            >
              <Plus className="h-4 w-4" />
              {state !== 'collapsed' && <span>New Conversation</span>}
            </SidebarMenuButton>
          </Link>
        </div>
      </SidebarHeader>
      
      <SidebarContent className="px-2">
        <div className="mt-2">
          <NavAgentsStyled />
        </div>
        
        <SidebarGroup className="mt-auto mb-4">
          <Link href="/agents">
            <SidebarMenuButton 
              className={cn(
                "transition-all duration-200 hover:scale-[1.02]",
                pathname === '/agents' 
                  ? "bg-gradient-to-r from-purple-600/20 to-purple-700/20 text-purple-400" 
                  : "hover:bg-[hsl(262,20%,12%)]"
              )}
            >
              <div className={cn(
                "p-1.5 rounded-lg transition-all duration-200",
                "bg-gradient-to-br from-purple-500/20 to-purple-600/20",
                "group-hover:from-purple-500/30 group-hover:to-purple-600/30"
              )}>
                <Bot className="h-4 w-4 text-purple-400" />
              </div>
              {state !== 'collapsed' && (
                <div className="ml-2 flex-1 text-left">
                  <div className="text-sm font-medium text-gray-200 group-hover:text-white transition-colors">
                    Agent Playground
                  </div>
                  <div className="text-xs text-gray-400">
                    Experiment with AI agents
                  </div>
                </div>
              )}
            </SidebarMenuButton>
          </Link>
        </SidebarGroup>
      </SidebarContent>
      
      <SidebarFooter className="border-t border-[hsl(262,20%,15%)]">
        {state === 'collapsed' && (
          <div className="mt-2 flex justify-center">
            <Tooltip>
              <TooltipTrigger asChild>
                <SidebarTrigger className="h-8 w-8 text-gray-400 hover:text-white hover:bg-[hsl(262,20%,12%)]" />
              </TooltipTrigger>
              <TooltipContent>Expand sidebar (CMD+B)</TooltipContent>
            </Tooltip>
          </div>
        )}
        <NavUserWithTeams user={user} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}