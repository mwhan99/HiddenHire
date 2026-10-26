import { PageHeader } from "@/components/PageHeader";
import { SearchSkeleton } from "@/components/SearchSkeleton";

// Shown immediately when a search is submitted, while the new results load.
export default function Loading() {
  return (
    <main>
      <PageHeader
        active="/search"
        eyebrow="Find roles"
        title="Find your hidden opportunities"
        description="Ranking open roles by your fit and each company's hiring momentum…"
      />
      <div className="mx-auto max-w-6xl px-4 py-10">
        <SearchSkeleton />
      </div>
    </main>
  );
}
