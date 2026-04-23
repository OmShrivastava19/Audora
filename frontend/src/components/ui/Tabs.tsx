import { useState, type ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

interface TabItem {
  id: string;
  label: string;
  icon?: ReactNode;
  content: ReactNode;
}

interface TabsProps {
  items: TabItem[];
  defaultTab?: string;
  className?: string;
}

export function Tabs({ items, defaultTab, className }: TabsProps) {
  const [activeTab, setActiveTab] = useState(defaultTab || items[0]?.id || '');
  const activeItem = items.find((i) => i.id === activeTab);

  return (
    <div className={cn('', className)}>
      <div className="flex gap-1 p-1 bg-bg-elevated rounded-lg border border-border mb-4 overflow-x-auto" role="tablist">
        {items.map((item) => (
          <button
            key={item.id}
            role="tab"
            aria-selected={activeTab === item.id}
            onClick={() => setActiveTab(item.id)}
            className={cn(
              'relative flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-md transition-colors whitespace-nowrap',
              activeTab === item.id
                ? 'text-accent'
                : 'text-muted hover:text-text-secondary'
            )}
          >
            {activeTab === item.id && (
              <motion.div
                layoutId="activeTab"
                className="absolute inset-0 bg-surface rounded-md border border-border"
                transition={{ type: 'spring', duration: 0.4, bounce: 0.15 }}
              />
            )}
            <span className="relative z-10 flex items-center gap-2">
              {item.icon}
              {item.label}
            </span>
          </button>
        ))}
      </div>
      <AnimatePresence mode="wait">
        {activeItem && (
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
            role="tabpanel"
          >
            {activeItem.content}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
