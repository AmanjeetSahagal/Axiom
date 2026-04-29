import { AuthGuard } from "@/components/AuthGuard";
import { OptimizerClient } from "@/components/OptimizerClient";
import { Shell } from "@/components/Shell";

export default async function OptimizerPage() {
  return (
    <Shell>
      <AuthGuard>
        <OptimizerClient />
      </AuthGuard>
    </Shell>
  );
}
