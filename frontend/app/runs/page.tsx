import { AuthGuard } from "@/components/AuthGuard";
import { RunManager } from "@/components/RunManager";
import { Shell } from "@/components/Shell";

export default async function RunsPage() {
  return (
    <Shell>
      <AuthGuard>
        <RunManager />
      </AuthGuard>
    </Shell>
  );
}
