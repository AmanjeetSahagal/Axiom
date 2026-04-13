import { AuthGuard } from "@/components/AuthGuard";
import { DatasetManager } from "@/components/DatasetManager";
import { Shell } from "@/components/Shell";

export default async function DatasetsPage() {
  return (
    <Shell>
      <AuthGuard>
      <section className="space-y-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-slate-500">Dataset Management</p>
          <h2 className="mt-2 font-display text-4xl text-ink">Upload, validate, and inspect evaluation corpora.</h2>
        </div>
        <DatasetManager />
      </section>
      </AuthGuard>
    </Shell>
  );
}
