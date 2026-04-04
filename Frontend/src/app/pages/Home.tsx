import { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import Sidebar from '../components/Sidebar';
import ArticleCard from '../components/ArticleCard';
import AuthorCard from '../components/AuthorCard';
import { ArticleSummary, AuthorProfile } from '../lib/api';
import { Search } from 'lucide-react';

export default function Home() {
  const { api, user, loading } = useApp();
  const [articles, setArticles] = useState<ArticleSummary[]>([]);
  const [authors, setAuthors] = useState<AuthorProfile[]>([]);
  const [loadingArticles, setLoadingArticles] = useState(true);
  const [sort, setSort] = useState('recommended');
  const [tagFilter, setTagFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<ArticleSummary[] | null>(null);

  // Fetch articles
  useEffect(() => {
    if (loading) return;

    setLoadingArticles(true);
    api
      .getArticles({ userId: user?.id, sort, tag: tagFilter || undefined })
      .then((res) => setArticles(res.data))
      .catch((err) => console.error('Failed to load articles:', err))
      .finally(() => setLoadingArticles(false));
  }, [api, loading, user?.id, sort, tagFilter]);

  // Fetch authors for sidebar
  useEffect(() => {
    if (loading) return;

    api
      .getAuthors(1, 5)
      .then((res) => setAuthors(res.data))
      .catch((err) => console.error('Failed to load authors:', err));
  }, [api, loading, user?.id]);

  // Search
  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    try {
      const res = await api.search(searchQuery, 'stories');
      setSearchResults((res.stories?.data as ArticleSummary[]) || []);
    } catch (err) {
      console.error('Search failed:', err);
    }
  };

  const displayArticles = searchResults !== null ? searchResults : articles;

  const sortOptions = [
    { value: 'recommended', label: 'Recommended' },
    { value: 'latest', label: 'Latest' },
    { value: 'popular', label: 'Popular' },
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
        <main className="flex-1 max-w-3xl px-12 py-8">
          {/* Search Bar */}
          <div className="relative mb-6">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search articles..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                if (!e.target.value.trim()) setSearchResults(null);
              }}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-10 pr-4 py-3 bg-gray-50 border border-gray-200 rounded-full focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
            />
          </div>

          {/* Sort Tabs */}
          <div className="flex gap-6 border-b border-gray-200 mb-6">
            {sortOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => {
                  setSort(opt.value);
                  setSearchResults(null);
                  setSearchQuery('');
                }}
                className={`pb-3 border-b-2 transition-colors text-sm font-medium ${
                  sort === opt.value && searchResults === null
                    ? 'border-black text-black'
                    : 'border-transparent text-gray-500 hover:text-black'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>

          {/* Title */}
          <h2 className="text-2xl font-bold mb-6">
            {searchResults !== null
              ? `Search results for "${searchQuery}"`
              : sort === 'recommended'
                ? 'Recommended for you'
                : sort === 'latest'
                  ? 'Latest articles'
                  : 'Popular articles'}
          </h2>

          {/* Article List */}
          {loadingArticles && searchResults === null ? (
            <div className="space-y-8">
              {[1, 2, 3].map((i) => (
                <div key={i} className="animate-pulse py-6 border-b border-gray-200">
                  <div className="h-4 bg-gray-200 rounded w-1/4 mb-3" />
                  <div className="h-6 bg-gray-200 rounded w-3/4 mb-2" />
                  <div className="h-4 bg-gray-200 rounded w-1/2 mb-4" />
                  <div className="h-3 bg-gray-100 rounded w-1/3" />
                </div>
              ))}
            </div>
          ) : displayArticles.length === 0 ? (
            <p className="text-gray-500 text-center py-12">No articles found.</p>
          ) : (
            <div>
              {displayArticles.map((article) => (
                <ArticleCard key={article.id} article={article} />
              ))}
            </div>
          )}
        </main>

        {/* Authors Sidebar */}
        <aside className="w-80 border-l border-gray-200 p-8 sticky top-0 h-screen overflow-y-auto">
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
