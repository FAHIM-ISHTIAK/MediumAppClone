import { useEffect, useState } from "react";
import { useApp } from "../context/AppContext";
import Sidebar from "../components/Sidebar";
import ArticleCard from "../components/ArticleCard";
import AuthorCard from "../components/AuthorCard";
import { ArticleSummary, AuthorProfile, PublicationProfile } from "../lib/api";
import { Search } from "lucide-react";

type SearchTab = "stories" | "authors" | "publications";

interface SearchResultsState {
  query: string;
  stories: ArticleSummary[];
  authors: AuthorProfile[];
  publications: PublicationProfile[];
  totals: Record<SearchTab, number>;
}

const EMPTY_SEARCH_TOTALS: Record<SearchTab, number> = {
  stories: 0,
  authors: 0,
  publications: 0,
};

export default function Home() {
  const { api, user, loading } = useApp();
  const [articles, setArticles] = useState<ArticleSummary[]>([]);
  const [authors, setAuthors] = useState<AuthorProfile[]>([]);
  const [loadingArticles, setLoadingArticles] = useState(true);
  const [sort, setSort] = useState("recommended");
  const [tagFilter, setTagFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResultsState | null>(
    null,
  );
  const [activeSearchTab, setActiveSearchTab] = useState<SearchTab>("stories");
  const [searchLoading, setSearchLoading] = useState(false);

  // Fetch articles
  useEffect(() => {
    if (loading) return;

    setLoadingArticles(true);
    api
      .getArticles({ userId: user?.id, sort, tag: tagFilter || undefined })
      .then((res) => setArticles(res.data))
      .catch((err) => console.error("Failed to load articles:", err))
      .finally(() => setLoadingArticles(false));
  }, [api, loading, user?.id, sort, tagFilter]);

  // Fetch authors for sidebar
  useEffect(() => {
    if (loading) return;

    api
      .getAuthors(1, 5)
      .then((res) => setAuthors(res.data))
      .catch((err) => console.error("Failed to load authors:", err));
  }, [api, loading, user?.id]);

  const pickInitialTab = (totals: Record<SearchTab, number>): SearchTab => {
    return (
      (["stories", "authors", "publications"] as SearchTab[]).find(
        (tab) => totals[tab] > 0,
      ) || "stories"
    );
  };

  const clearSearchResults = () => {
    setSearchResults(null);
    setSearchLoading(false);
    setActiveSearchTab("stories");
  };

  // Search
  const handleSearch = async () => {
    const query = searchQuery.trim();
    if (!query) {
      clearSearchResults();
      return;
    }

    setSearchLoading(true);
    setSearchResults({
      query,
      stories: [],
      authors: [],
      publications: [],
      totals: EMPTY_SEARCH_TOTALS,
    });
    setActiveSearchTab("stories");

    try {
      // Backend search uses ILIKE %query% matching, so this supports substring lookups (e.g., "ai").
      const res = await api.search(query);
      const stories = (res.stories?.data as ArticleSummary[]) || [];
      const matchedAuthors = (res.people?.data as AuthorProfile[]) || [];
      const matchedPublications =
        (res.publications?.data as PublicationProfile[]) || [];

      const totals: Record<SearchTab, number> = {
        stories: res.stories?.total ?? stories.length,
        authors: res.people?.total ?? matchedAuthors.length,
        publications: res.publications?.total ?? matchedPublications.length,
      };

      setSearchResults({
        query,
        stories,
        authors: matchedAuthors,
        publications: matchedPublications,
        totals,
      });
      setActiveSearchTab(pickInitialTab(totals));
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setSearchLoading(false);
    }
  };

  const searchTabs = searchResults
    ? [
        {
          value: "stories" as const,
          label: "Stories",
          count: searchResults.totals.stories,
        },
        {
          value: "authors" as const,
          label: "Authors",
          count: searchResults.totals.authors,
        },
        {
          value: "publications" as const,
          label: "Publications",
          count: searchResults.totals.publications,
        },
      ]
    : [];

  const sortOptions = [
    { value: "recommended", label: "Recommended" },
    { value: "latest", label: "Latest" },
    { value: "popular", label: "Popular" },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-white">
        <Sidebar />
        <div className="ml-64 flex items-center justify-center h-screen">
          <p className="text-gray-600">Restoring your home feed...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <Sidebar />

      <div className="ml-64 flex">
        <div className="flex-1 min-w-0">
          <main className="max-w-3xl mx-auto px-12 py-8">
          {/* Search Bar */}
          <div className="relative mb-6">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search stories, authors, publications..."
              value={searchQuery}
              onChange={(e) => {
                const value = e.target.value;
                setSearchQuery(value);
                if (!value.trim()) {
                  clearSearchResults();
                }
              }}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="w-full pl-10 pr-24 py-3 bg-gray-50 border border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
            />
            <button
              onClick={handleSearch}
              disabled={searchLoading}
              className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 text-sm rounded-full bg-black text-white hover:bg-gray-800 transition-colors"
            >
              {searchLoading ? "Searching..." : "Search"}
            </button>
          </div>

          {searchResults === null ? (
            <div className="flex gap-6 border-b border-gray-200 mb-6">
              {sortOptions.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => {
                    setSort(opt.value);
                    clearSearchResults();
                    setSearchQuery("");
                  }}
                  className={`pb-3 border-b-2 transition-colors text-sm font-medium ${
                    sort === opt.value
                      ? "border-black text-black"
                      : "border-transparent text-gray-500 hover:text-black"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          ) : (
            <div className="flex gap-6 border-b border-gray-200 mb-6">
              {searchTabs.map((tab) => (
                <button
                  key={tab.value}
                  onClick={() => setActiveSearchTab(tab.value)}
                  className={`pb-3 border-b-2 transition-colors text-sm font-medium ${
                    activeSearchTab === tab.value
                      ? "border-black text-black"
                      : "border-transparent text-gray-500 hover:text-black"
                  }`}
                >
                  {tab.label}
                  <span className="ml-2 text-xs text-gray-500">
                    {tab.count}
                  </span>
                </button>
              ))}
            </div>
          )}

          {/* Title */}
          <h2 className="text-2xl font-bold mb-6">
            {searchResults !== null
              ? `Search results for "${searchResults.query}"`
              : sort === "recommended"
                ? "Recommended for you"
                : sort === "latest"
                  ? "Latest articles"
                  : "Popular articles"}
          </h2>

          {searchResults !== null ? (
            searchLoading ? (
              <p className="text-gray-500 text-center py-12">Searching...</p>
            ) : activeSearchTab === "stories" ? (
              searchResults.stories.length === 0 ? (
                <p className="text-gray-500 text-center py-12">
                  No stories found.
                </p>
              ) : (
                <div>
                  {searchResults.stories.map((article) => (
                    <ArticleCard key={article.id} article={article} />
                  ))}
                </div>
              )
            ) : activeSearchTab === "authors" ? (
              searchResults.authors.length === 0 ? (
                <p className="text-gray-500 text-center py-12">
                  No authors found.
                </p>
              ) : (
                <div className="divide-y divide-gray-100">
                  {searchResults.authors.map((author) => (
                    <AuthorCard key={author.id} author={author} />
                  ))}
                </div>
              )
            ) : searchResults.publications.length === 0 ? (
              <p className="text-gray-500 text-center py-12">
                No publications found.
              </p>
            ) : (
              <div className="divide-y divide-gray-200">
                {searchResults.publications.map((publication) => (
                  <article
                    key={publication.id}
                    className="py-6 flex items-start gap-4"
                  >
                    {publication.avatar ? (
                      <img
                        src={publication.avatar}
                        alt={publication.name}
                        className="size-12 rounded-md object-cover"
                      />
                    ) : (
                      <div className="size-12 rounded-md bg-gray-200 text-gray-700 font-semibold flex items-center justify-center">
                        {publication.name.charAt(0).toUpperCase()}
                      </div>
                    )}

                    <div className="min-w-0">
                      <h3 className="text-xl font-semibold">
                        {publication.name}
                      </h3>
                      <p className="text-gray-600 mt-1 line-clamp-2">
                        {publication.description || "No description available."}
                      </p>
                      <p className="text-sm text-gray-500 mt-3">
                        {publication.followers.toLocaleString()} followers ·{" "}
                        {publication.articlesCount} articles
                      </p>
                    </div>
                  </article>
                ))}
              </div>
            )
          ) : loadingArticles ? (
            <div className="space-y-8">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="animate-pulse py-6 border-b border-gray-200"
                >
                  <div className="h-4 bg-gray-200 rounded w-1/4 mb-3" />
                  <div className="h-6 bg-gray-200 rounded w-3/4 mb-2" />
                  <div className="h-4 bg-gray-200 rounded w-1/2 mb-4" />
                  <div className="h-3 bg-gray-100 rounded w-1/3" />
                </div>
              ))}
            </div>
          ) : articles.length === 0 ? (
            <p className="text-gray-500 text-center py-12">
              No articles found.
            </p>
          ) : (
            <div>
              {articles.map((article) => (
                <ArticleCard key={article.id} article={article} />
              ))}
            </div>
          )}
          </main>
        </div>

        {/* Authors Sidebar */}
        <aside className="w-72 shrink-0 border-l border-gray-200 p-6 sticky top-0 h-screen overflow-y-auto">
          <h3 className="font-medium mb-4">Suggested Authors</h3>
          <div className="divide-y divide-gray-100">
            {authors.map((author) => (
              <AuthorCard key={author.id} author={author} />
            ))}
          </div>
        </aside>
      </div>
    </div>
  );
}
