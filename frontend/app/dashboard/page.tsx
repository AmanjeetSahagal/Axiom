import { AuthGuard } from "@/components/AuthGuard";
import { DashboardClient } from "@/components/DashboardClient";
import { Shell } from "@/components/Shell";

export default async function DashboardPage() {
  return (
    <Shell>
      <AuthGuard>
        <DashboardClient />
      </AuthGuard>
    </Shell>
  );
}
