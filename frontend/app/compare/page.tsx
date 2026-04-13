import { AuthGuard } from "@/components/AuthGuard";
import { CompareClient } from "@/components/CompareClient";
import { Shell } from "@/components/Shell";

export default async function ComparePage() {
  return (
    <Shell>
      <AuthGuard>
        <CompareClient />
      </AuthGuard>
    </Shell>
  );
}
