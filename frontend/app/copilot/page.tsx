import { CopilotClient } from "@/components/CopilotClient";
import { SiteHeader } from "@/components/SiteHeader";
import { Shell } from "@/components/Shell";
import { demoMode } from "@/lib/demo";
import { AuthGuard } from "@/components/AuthGuard";

export default async function CopilotPage() {
  if (demoMode) {
    return (
      <div className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
        <SiteHeader />
        <section className="space-y-4">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-slate-500">AI Copilot</p>
            <h1 className="mt-2 font-display text-4xl text-ink">Cloudflare-backed evaluation assistant.</h1>
          </div>
          <CopilotClient />
        </section>
      </div>
    );
  }

  return (
    <Shell>
      <AuthGuard>
        <section className="space-y-4">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-slate-500">AI Copilot</p>
            <h1 className="mt-2 font-display text-4xl text-ink">Cloudflare-backed evaluation assistant.</h1>
          </div>
          <CopilotClient />
        </section>
      </AuthGuard>
    </Shell>
  );
}
