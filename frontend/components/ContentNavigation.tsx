import React, { useState } from 'react';
import useSWR from 'swr';
import { ChevronRight, Loader2, BookOpen, GraduationCap, School, Book } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './ui/button';

// Generic fetcher
const fetcher = (url: string) => fetch(url).then((res) => res.json());

interface ContentNavigationProps {
  onSelectContent: (id: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

export function ContentNavigation({ onSelectContent, isOpen, onClose }: ContentNavigationProps) {
  const [level, setLevel] = useState<string | null>(null);
  const [branch, setBranch] = useState<string | null>(null);
  const [subject, setSubject] = useState<string | null>(null);
  const [year, setYear] = useState<number | null>(null);
  const [setName, setSetName] = useState<string | null>(null);

  // SWR Hooks for hierarchical data
  const { data: levels } = useSWR(isOpen ? '/api/v1/content/options/levels' : null, fetcher);

  const { data: branches } = useSWR(
    level ? `/api/v1/content/options/branches?level=${level}` : null,
    fetcher
  );

  const { data: subjects } = useSWR(
    level && branch ? `/api/v1/content/options/subjects?level=${level}&branch=${branch}` : null,
    fetcher
  );

  const { data: years } = useSWR(
    level && branch && subject ? `/api/v1/content/options/years?level=${level}&branch=${branch}&subject=${subject}` : null,
    fetcher
  );

  const { data: sets } = useSWR(
    level && branch && subject && year ? `/api/v1/content/options/sets?level=${level}&branch=${branch}&subject=${subject}&year=${year}` : null,
    fetcher
  );

  const { data: exercises } = useSWR(
    level && branch && subject && year && setName
      ? `/api/v1/content/options/exercises?level=${level}&branch=${branch}&subject=${subject}&year=${year}&set_name=${setName}`
      : null,
    fetcher
  );

  if (!isOpen) return null;

  const resetAfter = (stage: string) => {
    if (stage === 'level') { setLevel(null); setBranch(null); setSubject(null); setYear(null); setSetName(null); }
    if (stage === 'branch') { setBranch(null); setSubject(null); setYear(null); setSetName(null); }
    if (stage === 'subject') { setSubject(null); setYear(null); setSetName(null); }
    if (stage === 'year') { setYear(null); setSetName(null); }
    if (stage === 'set') { setSetName(null); }
  };

  return (
    <div className="absolute bottom-20 left-4 z-50 w-80 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl shadow-2xl overflow-hidden animate-in slide-in-from-bottom-5">
      <div className="p-4 bg-zinc-50 dark:bg-zinc-950 border-b border-zinc-200 dark:border-zinc-800 flex justify-between items-center">
        <h3 className="font-semibold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
          <BookOpen className="w-4 h-4" />
          مكتبة التمارين
        </h3>
        <Button variant="ghost" size="sm" onClick={onClose} className="h-6 w-6 p-0 rounded-full">
          &times;
        </Button>
      </div>

      <div className="p-2 h-[400px] overflow-y-auto">
        {/* Step 1: Level */}
        {!level && (
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground p-2">اختر المستوى الدراسي:</p>
            {levels ? (
              levels.map((l: string) => (
                <MenuOption key={l} label={l} icon={<School className="w-4 h-4" />} onClick={() => setLevel(l)} />
              ))
            ) : <Loading />}
          </div>
        )}

        {/* Step 2: Branch */}
        {level && !branch && (
          <div className="space-y-1 animate-in slide-in-from-right-5">
            <Header label={level} onBack={() => resetAfter('level')} />
            <p className="text-xs text-muted-foreground p-2">اختر الشعبة:</p>
            {branches ? (
              branches.map((b: string) => (
                <MenuOption key={b} label={b} icon={<GraduationCap className="w-4 h-4" />} onClick={() => setBranch(b)} />
              ))
            ) : <Loading />}
          </div>
        )}

        {/* Step 3: Subject */}
        {level && branch && !subject && (
          <div className="space-y-1 animate-in slide-in-from-right-5">
            <Header label={`${level} > ${branch}`} onBack={() => resetAfter('branch')} />
            <p className="text-xs text-muted-foreground p-2">اختر المادة:</p>
            {subjects ? (
              subjects.map((s: string) => (
                <MenuOption key={s} label={s} icon={<Book className="w-4 h-4" />} onClick={() => setSubject(s)} />
              ))
            ) : <Loading />}
          </div>
        )}

        {/* Step 4: Year */}
        {level && branch && subject && !year && (
          <div className="space-y-1 animate-in slide-in-from-right-5">
             <Header label={`${subject}`} onBack={() => resetAfter('subject')} />
             <p className="text-xs text-muted-foreground p-2">اختر الدورة/السنة:</p>
            {years ? (
              years.map((y: number) => (
                <MenuOption key={y} label={`${y}`} onClick={() => setYear(y)} />
              ))
            ) : <Loading />}
          </div>
        )}

         {/* Step 5: Set */}
         {level && branch && subject && year && !setName && (
          <div className="space-y-1 animate-in slide-in-from-right-5">
             <Header label={`${year}`} onBack={() => resetAfter('year')} />
             <p className="text-xs text-muted-foreground p-2">اختر الموضوع:</p>
            {sets ? (
              sets.map((s: string) => (
                <MenuOption key={s} label={s} onClick={() => setSetName(s)} />
              ))
            ) : <Loading />}
          </div>
        )}

        {/* Step 6: Exercise */}
        {level && branch && subject && year && setName && (
          <div className="space-y-1 animate-in slide-in-from-right-5">
             <Header label={`${setName}`} onBack={() => resetAfter('set')} />
             <p className="text-xs text-muted-foreground p-2">اختر التمرين:</p>
            {exercises ? (
              exercises.map((ex: {id: string, title: string}) => (
                <MenuOption
                  key={ex.id}
                  label={ex.title}
                  onClick={() => {
                    onSelectContent(ex.id);
                    onClose();
                  }}
                  className="font-bold text-primary"
                />
              ))
            ) : <Loading />}
          </div>
        )}
      </div>
    </div>
  );
}

const MenuOption = ({ label, onClick, icon, className }: { label: string, onClick: () => void, icon?: React.ReactNode, className?: string }) => (
  <button
    onClick={onClick}
    className={cn(
      "w-full text-right px-3 py-2 text-sm rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors flex items-center justify-between group",
      className
    )}
  >
    <span className="flex items-center gap-2">
      {icon}
      {label}
    </span>
    <ChevronRight className="w-4 h-4 text-zinc-400 group-hover:text-zinc-600 rtl:rotate-180" />
  </button>
);

const Header = ({ label, onBack }: { label: string, onBack: () => void }) => (
  <div className="flex items-center gap-2 pb-2 mb-2 border-b border-zinc-100 dark:border-zinc-800">
    <button onClick={onBack} className="text-xs text-muted-foreground hover:text-foreground">
      عودة
    </button>
    <span className="text-xs font-medium text-zinc-500">/</span>
    <span className="text-xs font-semibold text-zinc-900 dark:text-zinc-100 truncate max-w-[150px]">{label}</span>
  </div>
);

const Loading = () => (
  <div className="flex justify-center p-4">
    <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
  </div>
);
