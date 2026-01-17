import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import { cn } from '@/lib/utils';
import { Button } from './ui/button';
import { Loader2 } from 'lucide-react';
import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface ExerciseDisplayProps {
  contentId: string;
  onClose?: () => void;
}

export function ExerciseDisplay({ contentId, onClose }: ExerciseDisplayProps) {
  const { data: content, error, isLoading } = useSWR(`/api/v1/content/${contentId}`, fetcher);
  const { data: solution } = useSWR(`/api/v1/content/${contentId}/solution`, fetcher);

  const [showSolution, setShowSolution] = React.useState(false);

  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center justify-center min-h-[300px]">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error || !content) {
    return (
      <div className="p-4 text-center text-red-500">
        فشل تحميل التمرين. حاول مرة أخرى.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-zinc-950 rounded-xl overflow-hidden border border-zinc-200 dark:border-zinc-800 shadow-sm">
      {/* Header */}
      <div className="p-4 border-b border-zinc-200 dark:border-zinc-800 flex justify-between items-center bg-zinc-50/50 dark:bg-zinc-900/50">
        <div>
          <h2 className="font-bold text-lg text-zinc-900 dark:text-zinc-100">{content.title}</h2>
          <div className="flex gap-2 text-xs text-muted-foreground mt-1">
            <span className="bg-zinc-200 dark:bg-zinc-800 px-2 py-0.5 rounded">{content.year}</span>
            <span className="bg-zinc-200 dark:bg-zinc-800 px-2 py-0.5 rounded">{content.branch}</span>
            <span className="bg-zinc-200 dark:bg-zinc-800 px-2 py-0.5 rounded">{content.subject}</span>
          </div>
        </div>
        {onClose && (
            <Button variant="ghost" onClick={onClose}>إغلاق</Button>
        )}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-8">

        {/* Exercise Text */}
        <div className={cn("prose dark:prose-invert max-w-none prose-lg dir-rtl", "prose-headings:font-bold prose-p:leading-relaxed")}>
            <ReactMarkdown
              remarkPlugins={[remarkMath]}
              rehypePlugins={[rehypeKatex]}
              components={{
                p: ({node, ...props}) => <p className="mb-4 text-zinc-800 dark:text-zinc-200" {...props} />
              }}
            >
              {content.md_content}
            </ReactMarkdown>
        </div>

        {/* Divider */}
        {solution && (
            <div className="border-t border-dashed border-zinc-300 dark:border-zinc-700 my-8"></div>
        )}

        {/* Solution Toggle */}
        {solution && (
            <div className="flex justify-center">
                <Button
                    variant={showSolution ? "outline" : "default"}
                    onClick={() => setShowSolution(!showSolution)}
                >
                    {showSolution ? "إخفاء الحل" : "عرض الحل النموذجي"}
                </Button>
            </div>
        )}

        {/* Solution Content */}
        {showSolution && solution && (
             <div className="bg-green-50/50 dark:bg-green-950/10 border border-green-100 dark:border-green-900 rounded-xl p-6 animate-in slide-in-from-bottom-2">
                <h3 className="text-green-700 dark:text-green-400 font-bold mb-4 flex items-center gap-2">
                    ✅ الحل المقترح
                </h3>
                <div className="prose dark:prose-invert max-w-none dir-rtl prose-img:rounded-lg">
                    <ReactMarkdown
                        remarkPlugins={[remarkMath]}
                        rehypePlugins={[rehypeKatex]}
                    >
                        {solution.solution_md}
                    </ReactMarkdown>
                </div>
             </div>
        )}

      </div>
    </div>
  );
}
