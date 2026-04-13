import { AuthGuard } from "@/components/AuthGuard";
import { RunDetailClient } from "@/components/RunDetailClient";
import { Shell } from "@/components/Shell";

export default async function RunDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  return (
    <Shell>
      <AuthGuard>
        <RunDetailClient id={id} />
      </AuthGuard>
    </Shell>
  );
}
