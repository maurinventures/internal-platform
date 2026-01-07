import { ReactNode } from "react";

interface PageHeaderProps {
  children: ReactNode;
  /** If true, uses fixed h-10 height for chat-style headers */
  compact?: boolean;
}

/**
 * Standardized page header component
 * - compact: true => h-10 px-4 (for chat screens with dropdown titles)
 * - compact: false => px-12 py-6 (for full-width pages with search/filters)
 */
export function PageHeader({ children, compact = false }: PageHeaderProps) {
  if (compact) {
    return (
      <div className="h-10 border-b border-border flex items-center justify-between px-4">
        {children}
      </div>
    );
  }

  return (
    <div className="px-12 py-6 border-b border-border">
      {children}
    </div>
  );
}
