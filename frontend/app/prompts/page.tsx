import { AuthGuard } from "@/components/AuthGuard";
import { PromptManager } from "@/components/PromptManager";
import { Shell } from "@/components/Shell";

export default async function PromptsPage() {
  return (
    <Shell>
      <AuthGuard>
      <section className="space-y-6">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-slate-500">Prompt Templates</p>
          <h2 className="mt-2 font-display text-4xl text-ink">Version prompts like product assets, not scratch notes.</h2>
        </div>
        <PromptManager />
      </section>
      </AuthGuard>
    </Shell>
  );
}
