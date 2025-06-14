import { FirstBentoAnimation } from '@/components/home/first-bento-animation';
import { FourthBentoAnimation } from '@/components/home/fourth-bento-animation';
import { SecondBentoAnimation } from '@/components/home/second-bento-animation';
import { ThirdBentoAnimation } from '@/components/home/third-bento-animation';
import { FlickeringGrid } from '@/components/home/ui/flickering-grid';
import { Globe } from '@/components/home/ui/globe';
import { cn } from '@/lib/utils';
import { motion } from 'motion/react';
import { config } from '@/lib/config';

export const Highlight = ({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) => {
  return (
    <span
      className={cn(
        'p-1 py-0.5 font-medium dark:font-semibold text-secondary',
        className,
      )}
    >
      {children}
    </span>
  );
};

export const BLUR_FADE_DELAY = 0.15;

interface UpgradePlan {
  hours: string;
  price: string;
  stripePriceId: string;
}

export interface PricingTier {
  name: string;
  price: string;
  description: string;
  buttonText: string;
  buttonColor: string;
  isPopular: boolean;
  hours: string;
  features: string[];
  stripePriceId: string;
  upgradePlans: UpgradePlan[];
}

export const siteConfig = {
  name: 'Bitterbot',
  description: 'The Generalist AI Agent that can act on your behalf.',
  cta: 'Start Free',
  url: process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000',
  links: {
    email: 'vgil@bitterbot.net',
    twitter: 'https://x.com/vicmgil',
    github: 'https://github.com/VGIL77/Bitterbot-Core',
  },
  nav: {
    links: [
      { name: 'Features', href: '#features' },
      { name: 'Pricing', href: '#pricing' },
      { name: 'About', href: '#about' },
    ],
  },
  hero: {
    avatar: (
      <svg
        width="40"
        height="40"
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="size-10"
      >
        <rect width="40" height="40" rx="8" fill="currentColor" />
        <path
          d="M20 12L28 20L20 28L12 20L20 12Z"
          fill="white"
          stroke="white"
          strokeWidth="2"
          strokeLinejoin="round"
        />
      </svg>
    ),
    badge: '100% OPEN SOURCE',
    githubUrl: 'https://github.com/VGIL77/Bitterbot-Core',
    title: 'Bitterbot, the AI Employee.',
    description:
      'Bitterbot is a generalist AI Agent that acts on your behalf.',
    inputPlaceholder: 'Ask Bitterbot to...',
  },
  cloudPricingItems: [
    {
      name: 'Free',
      price: '$0',
      description: 'Get started with',
      buttonText: 'Get Started',
      buttonColor: 'bg-accent text-primary',
      isPopular: false,
      hours: 'Unlimited',
      features: [
        'Basic AI capabilities',
        'Community support',
        'Open source access',
      ],
      stripePriceId: '',
      upgradePlans: [],
    },
    {
      name: 'Pro',
      price: '$20',
      description: 'For power users',
      buttonText: 'Get Pro',
      buttonColor: 'bg-primary text-primary-foreground',
      isPopular: true,
      hours: '20 hours',
      features: [
        '2 hours',
        'Private projects',
        'Access to intelligent Model (Full Bitterbot)',
      ],
      stripePriceId: config.SUBSCRIPTION_TIERS.TIER_2_20.priceId,
      upgradePlans: [],
    },
  ],
  companyShowcase: {
    companyLogos: [
      {
        id: 1,
        name: 'Company 1',
        logo: (
          <svg
            width="100"
            height="40"
            viewBox="0 0 100 40"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <rect width="100" height="40" rx="4" fill="currentColor" />
          </svg>
        ),
      },
    ],
  },
  featureSection: {
    title: 'How Bitterbot Works',
    description: 'Discover how Bitterbot transforms your commands into action in four easy steps',
    items: [
      {
        id: 1,
        title: 'Voice Command',
        content: 'Speak or type your command—let Bitterbot capture your intent. Your request instantly sets the process in motion.',
        image: 'https://images.unsplash.com/photo-1720371300677-ba4838fa0678?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
      },
      {
        id: 2,
        title: 'Smart Planning',
        content: 'Bitterbot analyzes your request, understands the context, and develops a structured plan to complete the task efficiently.',
        image: 'https://images.unsplash.com/photo-1686170287433-c95faf6d3608?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxmZWF0dXJlZC1waG90b3MtZmVlZHwzfHx8ZW58MHx8fHx8fA%3D%3D',
      },
      {
        id: 3,
        title: 'Autonomous Execution',
        content: 'Using its capabilities and integrations, Bitterbot executes the task independently, handling any complexities along the way.',
        image: 'https://images.unsplash.com/photo-1720378042271-60aff1e1c538?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxmZWF0dXJlZC1waG90b3MtZmVlZHwxMHx8fGVufDB8fHx8fA%3D%3D',
      },
      {
        id: 4,
        title: 'Results & Learning',
        content: 'Bitterbot delivers results and learns from each interaction, continuously improving its performance to better serve your needs.',
        image: 'https://images.unsplash.com/photo-1666882990322-e7f3b8df4f75?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1yZWxhdGVkfDF8fHxlbnwwfHx8fHw%3D',
      },
    ],
  },
  bentoSection: {
    title: 'Empower Your Workflow with Bitterbot',
    description: 'Let Bitterbot act on your behalf with advanced AI capabilities, seamless integrations, and autonomous task execution.',
    items: [
      {
        id: 1,
        title: 'Autonomous Task Execution',
        description: 'Experience true automation with Bitterbot. Ask your AI Agent to complete tasks, research information, and handle complex workflows with minimal supervision.',
        content: <FirstBentoAnimation />,
      },
      {
        id: 2,
        title: 'Seamless Integrations',
        description: 'Connect Bitterbot to your existing tools for a unified workflow. Boost productivity through AI-powered interconnected systems.',
        content: <SecondBentoAnimation />,
      },
      {
        id: 3,
        title: 'Intelligent Data Analysis',
        description: "Transform raw data into actionable insights in seconds. Make better decisions with Bitterbot's real-time, adaptive intelligence.",
        content: <ThirdBentoAnimation data={[3, 6, 9, 12, 15]} toolTipValues={[20, 30, 40, 50, 60]} />,
      },
      {
        id: 4,
        title: 'Complete Customization',
        description: 'Tailor Bitterbot to your specific needs. As an open source solution, you have full control over its capabilities, integrations, and implementation.',
        content: <FourthBentoAnimation />,
      },
    ],
  },
  growthSection: [
    {
      id: 1,
      text: "Automate everyday tasks with Bitterbot's powerful AI capabilities.",
      image: '/Device-6.png',
    },
    {
      id: 2,
      text: 'Streamline workflows and boost productivity effortlessly.',
      image: '/Device-7.png',
    },
    {
      id: 3,
      text: 'Improve focus on high-value work as Bitterbot handles the routine.',
      image: '/Device-8.png',
    },
    {
      id: 4,
      text: 'Scale your operations with intelligent automation.',
      image: '/Device-9.png',
    },
  ],
  openSourceSection: {
    badge: 'OPEN SOURCE',
    title: 'Built by Developers, for Developers',
    description: 'Join our community and contribute to the future of AI automation.',
    items: [
      {
        id: 1,
        icon: (
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M12 2L2 7L12 12L22 7L12 2Z"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinejoin="round"
            />
            <path
              d="M2 17L12 22L22 17"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M2 12L12 17L22 12"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        ),
        title: 'Fully Open Source',
        description: 'Access the complete source code, modify it, and contribute to its development.',
      },
      {
        id: 2,
        icon: (
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M17 21V19C17 17.9 16.1 17 15 17H9C7.9 17 7 17.9 7 19V21"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d="M12 11C14.2091 11 16 9.20914 16 7C16 4.79086 14.2091 3 12 3C9.79086 3 8 4.79086 8 7C8 9.20914 9.79086 11 12 11Z"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        ),
        title: 'Community Powered',
        description: "Join a thriving community of developers and users continuously enhancing and expanding Bitterbot's capabilities.",
      },
    ],
  },
  pricing: {
    title: 'Open Source & Free Forever',
    description: 'Bitterbot is 100% open source and free to use. No hidden fees, no premium features locked behind paywalls.',
    pricingItems: [
      {
        name: 'Community',
        price: '$0',
        features: [
          'Full access to Bitterbot',
          'Open source code',
          'Community support',
        ],
        description: 'Perfect for individual users and developers',
        buttonText: 'Hire Bitterbot',
        buttonColor: 'bg-accent text-primary',
        isPopular: false,
      },
    ],
  },
  testimonials: [],
  faqSection: {
    title: 'Frequently Asked Questions',
    description: "Answers to common questions about Bitterbot and its capabilities. If you have any other questions, please don't hesitate to contact us.",
    faQitems: [
      {
        id: 1,
        question: 'What is Bitterbot?',
        answer: 'Bitterbot is an open-source AI agent that can act on your behalf to automate tasks, analyze data, and streamline workflows.',
      },
      {
        id: 2,
        question: 'How does Bitterbot work?',
        answer: 'Bitterbot works by analyzing your requirements, leveraging advanced AI algorithms to understand context, and executing tasks based on your instructions. It can integrate with your workflow, learn from feedback, and continuously improve its performance.',
      },
      {
        id: 3,
        question: 'Is Bitterbot really free?',
        answer: 'Yes, Bitterbot is completely free and open source. We believe in democratizing AI technology and making it accessible to everyone. You can use it, modify it, and contribute to its development without any cost.',
      },
      {
        id: 4,
        question: 'Can I integrate Bitterbot with my existing tools?',
        answer: 'Yes, Bitterbot is designed to be highly compatible with popular tools and platforms. We offer APIs and pre-built integrations for seamless connection with your existing workflow tools and systems.',
      },
      {
        id: 5,
        question: 'How can I contribute to Bitterbot?',
        answer: 'You can contribute to Bitterbot by submitting pull requests on GitHub, reporting bugs, suggesting new features, or helping with documentation. Join our Discord community to connect with other contributors and Hire Bitterbot.',
      },
      {
        id: 6,
        question: 'How does Bitterbot save me time?',
        answer: 'Bitterbot automates repetitive tasks, streamlines workflows, and provides quick solutions to common challenges. This automation and efficiency can save hours of manual work, allowing you to focus on more strategic activities.',
      },
    ],
  },
  ctaSection: {
    id: 'cta',
    title: 'Start Using Bitterbot Today',
    backgroundImage: '/holo.png',
    button: {
      text: 'Get Started for free',
      href: '/dashboard',
    },
  },
  footerLinks: [
    {
      title: 'Bitterbot',
      links: [
        { id: 1, title: 'About', url: 'https://bitterbot.net' },
        { id: 3, title: 'Contact', url: 'mailto:vgil@bitterbot.net' },
        { id: 4, title: 'Careers', url: 'https://bitterbot.net/careers' },
      ],
    },
    {
      title: 'Resources',
      links: [
        {
          id: 5,
          title: 'Documentation',
          url: 'https://github.com/VGIL77/Bitterbot-Core',
        },
        { id: 7, title: 'Discord', url: 'https://discord.gg/Py6pCBUUPw' },
        { id: 8, title: 'GitHub', url: 'https://github.com/VGIL77/Bitterbot-Core' },
      ],
    },
    {
      title: 'Legal',
      links: [
        {
          id: 9,
          title: 'Privacy Policy',
          url: 'https://bitterbot.net/legal?tab=privacy',
        },
        {
          id: 10,
          title: 'Terms of Service',
          url: 'https://bitterbot.net/legal?tab=terms',
        },
        {
          id: 11,
          title: 'License',
          url: 'https://github.com/VGIL77/Bitterbot-Core/blob/main/LICENSE',
        },
      ],
    },
  ],
  useCases: [],
};
