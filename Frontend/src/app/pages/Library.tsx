import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { useApp } from '../context/AppContext';
import Sidebar from '../components/Sidebar';
<<<<<<< HEAD
import { Clock, Bookmark, Highlighter, MessageCircle, Trash2, BarChart3 } from 'lucide-react';
import {
  ArticleSummary,
  HighlightItem,
=======
import { Clock, Bookmark, Highlighter, MessageCircle, MessageSquareText, Trash2, BarChart3 } from 'lucide-react';
import {
  ArticleSummary,
  HighlightItem,
  InlineResponseItem,
>>>>>>> main
  ReadingHistoryEntry,
  ResponseItem,
  ReadingAnalytics,
} from '../lib/api';

<<<<<<< HEAD
type LibraryTab = 'saved' | 'highlights' | 'history' | 'responses' | 'analytics';
=======
type LibraryTab = 'saved' | 'highlights' | 'history' | 'responses' | 'inline-responses' | 'analytics';
>>>>>>> main

export default function Library() {
  const { api, user, loading: authLoading } = useApp();
  const [activeTab, setActiveTab] = useState<LibraryTab>('saved');

  const [savedArticles, setSavedArticles] = useState<ArticleSummary[]>([]);
  const [highlights, setHighlights] = useState<HighlightItem[]>([]);
  const [history, setHistory] = useState<ReadingHistoryEntry[]>([]);
  const [responses, setResponses] = useState<ResponseItem[]>([]);
<<<<<<< HEAD
=======
  const [inlineResponses, setInlineResponses] = useState<InlineResponseItem[]>([]);
>>>>>>> main
  const [analytics, setAnalytics] = useState<ReadingAnalytics | null>(null);
  const [loading, setLoading] = useState(true);

  // Fetch data when tab changes
  useEffect(() => {
    if (!user) return;
    setLoading(true);

    const fetchMap: Record<string, () => Promise<void>> = {
      saved: async () => {
        const res = await api.getSavedArticles(user.id);
        setSavedArticles(res.data);
      },
      highlights: async () => {
        const res = await api.getLibraryHighlights(user.id);
        setHighlights(res.data);
      },
      history: async () => {
        const res = await api.getReadingHistory(user.id);
        setHistory(res.data);
      },
      responses: async () => {
        const res = await api.getUserResponses(user.id);
        setResponses(res.data);
      },
<<<<<<< HEAD
=======
      'inline-responses': async () => {
        const res = await api.getUserInlineResponses(user.id);
        setInlineResponses(res.data);
      },
>>>>>>> main
      analytics: async () => {
        const res = await api.getReadingAnalytics(user.id);
        setAnalytics(res);
      },
    };

    fetchMap[activeTab]()
      .catch((err) => console.error(`Failed to load ${activeTab}:`, err))
      .finally(() => setLoading(false));
  }, [api, user, activeTab]);

  if (authLoading) {
    return (
      <div className="min-h-screen bg-white">
        <Sidebar />
        <div className="ml-64 flex items-center justify-center h-screen">
          <p className="text-gray-600">Restoring your library...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-white">
        <Sidebar />
        <div className="ml-64 flex items-center justify-center h-screen">
          <p className="text-gray-600">Please sign in to view your library</p>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'saved' as LibraryTab, label: 'Saved', icon: Bookmark },
    { id: 'highlights' as LibraryTab, label: 'Highlights', icon: Highlighter },
    { id: 'history' as LibraryTab, label: 'Reading History', icon: Clock },
    { id: 'responses' as LibraryTab, label: 'Responses', icon: MessageCircle },
<<<<<<< HEAD
=======
    { id: 'inline-responses' as LibraryTab, label: 'Inline Responses', icon: MessageSquareText },
>>>>>>> main
    { id: 'analytics' as LibraryTab, label: 'Analytics', icon: BarChart3 },
  ];

  const handleDeleteHighlight = async (highlightId: string) => {
    try {
      await api.deleteLibraryHighlight(user.id, highlightId);
      setHighlights((prev) => prev.filter((h) => h.id !== highlightId));
    } catch (err) {
      console.error('Delete highlight failed:', err);
    }
  };

  const handleDeleteHistory = async (historyId: string) => {
    try {
      await api.deleteHistoryEntry(user.id, historyId);
      setHistory((prev) => prev.filter((h) => h.id !== historyId));
    } catch (err) {
      console.error('Delete history failed:', err);
    }
  };

  const handleUnsave = async (articleId: string) => {
    try {
      await api.unsaveArticle(user.id, articleId);
      setSavedArticles((prev) => prev.filter((a) => a.id !== articleId));
    } catch (err) {
      console.error('Unsave failed:', err);
    }
  };

  const highlightColorMap: Record<string, string> = {
    yellow: '#FEF3C7',
    green: '#DCFCE7',
    blue: '#DBEAFE',
    pink: '#FCE7F3',
    purple: '#EDE9FE',
  };

  return (
    <div className="min-h-screen bg-white">
      <Sidebar />

      <div className="ml-64 px-12 py-8">
        <h1 className="text-4xl font-bold mb-8">Your Library</h1>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-8">
          <div className="flex gap-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 pb-4 border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-black font-medium'
                      : 'border-transparent text-gray-600 hover:text-black'
                  }`}
                >
                  <Icon className="size-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab Content */}
        <div className="max-w-4xl">
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="animate-pulse p-4 border border-gray-200 rounded-lg">
                  <div className="h-5 bg-gray-200 rounded w-3/4 mb-3" />
                  <div className="h-4 bg-gray-100 rounded w-1/2" />
                </div>
              ))}
            </div>
          ) : (
            <>
              {/* Saved Articles */}
              {activeTab === 'saved' && (
                <div>
                  {savedArticles.length === 0 ? (
                    <EmptyState icon={Bookmark} message="No saved articles yet" sub="Articles you save will appear here" />
                  ) : (
                    <div className="space-y-6">
                      {savedArticles.map((article) => (
                        <div key={article.id} className="flex items-start gap-4 group p-4 hover:bg-gray-50 rounded-lg transition-colors">
                          <Link to={`/article/${article.id}`} className="flex gap-4 flex-1">
                            {article.coverImage && (
                              <img src={article.coverImage} alt={article.title} className="w-32 h-32 object-cover rounded" />
                            )}
                            <div className="flex-1">
                              <h3 className="text-xl font-bold mb-2 group-hover:underline">{article.title}</h3>
                              <p className="text-gray-600 mb-3 line-clamp-2">{article.subtitle}</p>
                              <div className="flex items-center gap-3 text-sm text-gray-500">
                                <span>{article.author.name}</span>
                                <span>·</span>
                                <span>{article.readingTime} min read</span>
                              </div>
                            </div>
                          </Link>
                          <button
                            onClick={() => handleUnsave(article.id)}
                            className="opacity-0 group-hover:opacity-100 p-2 hover:bg-gray-200 rounded transition-all"
                            title="Remove from saved"
                          >
                            <Trash2 className="size-4 text-gray-500" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Highlights */}
              {activeTab === 'highlights' && (
                <div>
                  {highlights.length === 0 ? (
                    <EmptyState icon={Highlighter} message="No highlights yet" sub="Highlight text while reading to save it here" />
                  ) : (
                    <div className="space-y-4">
                      {highlights.map((highlight) => (
                        <div key={highlight.id} className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors group">
                          <div className="flex items-start justify-between">
                            <Link
                              to={`/article/${highlight.articleId}`}
                              className="text-sm font-medium text-gray-900 hover:underline mb-2 block"
                            >
                              {highlight.articleTitle}
                            </Link>
                            <button
                              onClick={() => handleDeleteHighlight(highlight.id)}
                              className="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-100 rounded transition-all"
                            >
                              <Trash2 className="size-4 text-gray-400" />
                            </button>
                          </div>
                          <p
                            className="px-3 py-2 rounded italic"
                            style={{ backgroundColor: highlightColorMap[highlight.color] || '#FEF3C7' }}
                          >
                            "{highlight.text}"
                          </p>
                          <p className="text-xs text-gray-500 mt-2">{highlight.date}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Reading History */}
              {activeTab === 'history' && (
                <div>
                  {history.length === 0 ? (
                    <EmptyState icon={Clock} message="No reading history yet" sub="Articles you read will appear here" />
                  ) : (
                    <div className="space-y-4">
                      {history.map((item) => (
                        <div key={item.id} className="flex items-center gap-4 p-4 hover:bg-gray-50 rounded-lg transition-colors group">
                          <Link
                            to={
                              item.readPercentage > 0
                                ? `/article/${item.articleId}?resume=${item.readPercentage}`
                                : `/article/${item.articleId}`
                            }
                            className="flex-1 min-w-0"
                          >
                            <h3 className="font-bold mb-1 hover:underline">{item.title}</h3>
                            <div className="flex items-center gap-3 text-sm text-gray-500 flex-wrap">
                              <span>Read on {item.date}</span>
                              {item.timeSpent > 0 && (
                                <>
                                  <span>·</span>
                                  <span>{item.timeSpent} min spent</span>
                                </>
                              )}
                              {item.readPercentage > 0 && (
                                <>
                                  <span>·</span>
                                  <span className="font-medium text-gray-700">
                                    Continue from {item.readPercentage}%
                                  </span>
                                </>
                              )}
                            </div>
                            {item.tags.length > 0 && (
                              <div className="flex gap-1 mt-2 flex-wrap">
                                {item.tags.map((tag) => (
                                  <span key={tag} className="bg-gray-100 px-2 py-0.5 rounded-full text-xs">{tag}</span>
                                ))}
                              </div>
                            )}
                          </Link>
                          <button
                            onClick={() => handleDeleteHistory(item.id)}
                            className="opacity-0 group-hover:opacity-100 p-2 hover:bg-gray-200 rounded transition-all"
                            title="Remove from history"
                          >
                            <Trash2 className="size-4 text-gray-500" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Responses */}
              {activeTab === 'responses' && (
                <div>
                  {responses.length === 0 ? (
                    <EmptyState icon={MessageCircle} message="No responses yet" sub="Your comments on articles will appear here" />
                  ) : (
                    <div className="space-y-6">
                      {responses.map((comment) => (
                        <div key={comment.id} className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors">
                          <Link
                            to={`/article/${comment.articleId}`}
                            className="text-sm font-medium text-gray-900 hover:underline mb-3 block"
                          >
                            Response to: {comment.articleTitle}
                          </Link>
                          <p className="text-gray-800 mb-3">{comment.text}</p>
                          <div className="flex items-center gap-3 text-sm text-gray-500">
                            <span>{comment.date}</span>
                            <span>·</span>
                            <span>👏 {comment.likes}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

<<<<<<< HEAD
=======
              {/* Inline Responses */}
              {activeTab === 'inline-responses' && (
                <div>
                  {inlineResponses.length === 0 ? (
                    <EmptyState icon={MessageSquareText} message="No inline responses yet" sub="Your inline comments on articles will appear here" />
                  ) : (
                    <div className="space-y-4">
                      {inlineResponses.map((ir) => (
                        <div key={ir.id} className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors">
                          <Link
                            to={`/article/${ir.articleId}`}
                            className="text-sm font-medium text-gray-900 hover:underline mb-2 block"
                          >
                            View article →
                          </Link>
                          <p className="text-sm bg-yellow-50 border-l-2 border-yellow-400 pl-3 py-2 mb-2 italic text-gray-600">
                            "{ir.selectedText}"
                          </p>
                          <p className="text-gray-800 mb-2">{ir.text}</p>
                          <div className="flex items-center gap-3 text-xs text-gray-500">
                            <span>{ir.date}</span>
                            <span>·</span>
                            <span>👏 {ir.likes}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

>>>>>>> main
              {/* Analytics */}
              {activeTab === 'analytics' && analytics && (
                <div className="space-y-8">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-4 gap-6">
                    <StatCard label="Articles Read" value={analytics.totalArticlesRead} />
                    <StatCard label="Total Time (min)" value={analytics.totalTimeSpentMinutes} />
                    <StatCard label="Avg Time (min)" value={analytics.averageReadingTimeMinutes} />
                    <StatCard label="Avg Read %" value={analytics.averageReadPercentage} suffix="%" />
                  </div>

                  {/* Reading Streak */}
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <h3 className="font-bold mb-4">📚 Reading Streak</h3>
                    <div className="flex gap-8">
                      <div>
                        <div className="text-3xl font-bold">{analytics.readingStreak.currentDays}</div>
                        <div className="text-sm text-gray-600">Current streak (days)</div>
                      </div>
                      <div>
                        <div className="text-3xl font-bold">{analytics.readingStreak.longestDays}</div>
                        <div className="text-sm text-gray-600">Longest streak (days)</div>
                      </div>
                    </div>
                  </div>

                  {/* Top Tags */}
                  {analytics.topTags.length > 0 && (
                    <div>
                      <h3 className="font-bold mb-4">🏷️ Top Tags</h3>
                      <div className="flex flex-wrap gap-3">
                        {analytics.topTags.map((t) => (
                          <span key={t.tag} className="bg-gray-100 px-4 py-2 rounded-full text-sm">
                            {t.tag} <span className="font-bold ml-1">({t.count})</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Monthly Breakdown */}
                  {analytics.monthlyBreakdown.length > 0 && (
                    <div>
                      <h3 className="font-bold mb-4">📅 Monthly Breakdown</h3>
                      <div className="border border-gray-200 rounded-lg overflow-hidden">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-50">
                            <tr>
                              <th className="text-left py-3 px-4 font-medium">Month</th>
                              <th className="text-right py-3 px-4 font-medium">Articles</th>
                              <th className="text-right py-3 px-4 font-medium">Time (min)</th>
                            </tr>
                          </thead>
                          <tbody>
                            {analytics.monthlyBreakdown.map((m) => (
                              <tr key={m.month} className="border-t border-gray-100">
                                <td className="py-3 px-4">{m.month}</td>
                                <td className="text-right py-3 px-4">{m.articlesRead}</td>
                                <td className="text-right py-3 px-4">{m.timeSpentMinutes}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'analytics' && !analytics && !loading && (
                <EmptyState icon={BarChart3} message="No analytics data" sub="Start reading articles to see your stats" />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function EmptyState({ icon: Icon, message, sub }: { icon: any; message: string; sub: string }) {
  return (
    <div className="text-center py-12 text-gray-500">
      <Icon className="size-12 mx-auto mb-3 opacity-50" />
      <p>{message}</p>
      <p className="text-sm mt-2">{sub}</p>
    </div>
  );
}

function StatCard({ label, value, suffix }: { label: string; value: number; suffix?: string }) {
  return (
    <div className="bg-gray-50 p-6 rounded-lg text-center">
      <div className="text-3xl font-bold mb-2">{value}{suffix}</div>
      <div className="text-sm text-gray-600">{label}</div>
    </div>
  );
}
