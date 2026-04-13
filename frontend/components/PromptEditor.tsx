type PromptEditorProps = {
  systemPrompt: string;
  userTemplate: string;
};

export function PromptEditor({ systemPrompt, userTemplate }: PromptEditorProps) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <section className="rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
        <h3 className="font-display text-2xl">System Prompt</h3>
        <pre className="mt-4 whitespace-pre-wrap text-sm text-slate-700">{systemPrompt}</pre>
      </section>
      <section className="rounded-[28px] border border-black/5 bg-white/80 p-5 shadow-panel">
        <h3 className="font-display text-2xl">User Template</h3>
        <pre className="mt-4 whitespace-pre-wrap text-sm text-slate-700">{userTemplate}</pre>
      </section>
    </div>
  );
}

